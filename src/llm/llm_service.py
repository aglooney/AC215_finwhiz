import os
import logging
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
import re
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
from langchain_google_vertexai import VertexAI
import uuid


from .chroma_utils import ensure_chroma_local

#load environment
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_service")

#configuration
CHROMA_PATH = os.getenv("CHROMA_PATH", "/app/src/chroma_storage")
COLLECTION_DIR = "1a90eda1-e932-4e73-89dd-edb1adf9d126"
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "finwhiz_docs")
GCS_BUCKET = os.getenv("GCS_BUCKET")
GCS_PREFIX = os.getenv("GCS_PREFIX", "chroma_storage_backup")
AGENT_URL = os.getenv("AGENT_URL", "http://agent:8010")

VERTEXAI_CREDENTIALS = os.getenv("VERTEXAI_CREDENTIALS")
if not VERTEXAI_CREDENTIALS:
    raise ValueError("VERTEXAI_CREDENTIALS must be set")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = VERTEXAI_CREDENTIALS

#initialize chroma
ensure_chroma_local(GCS_BUCKET, GCS_PREFIX, COLLECTION_DIR, CHROMA_PATH)
logger.info("Initializing ChromaDB client")
client = PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(COLLECTION_NAME)

logger.info("Loading embedding model")
embedder = SentenceTransformer("jinaai/jina-embeddings-v3", device="cpu", trust_remote_code=True)

logger.info("Initializing Vertex AI model")
llm = VertexAI(model_name="gemini-2.5-pro")


app = FastAPI(title="FinWhiz LLM Service")

class QueryRequest(BaseModel):
    query: str
    session_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    top_k: int = 5


def reciprocal_rank_fusion(rank_lists, k=60):
    """Combine multiple ranked lists via RRF."""
    fused_scores = {}
    for rank_list in rank_lists:
        for rank, doc_id in enumerate(rank_list):
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1.0/(k+rank+1)
    return sorted(fused_scores.items(), key=lambda x:x[1], reverse=True)

def tokenize(text):
    return re.findall(r"\w+", text.lower())

def normalize_chroma_results(results):
    """Normalize Chroma query/get results to a consistent structure."""
    if not results:
        return [], [], [], []

    # Handle nested (from query)
    if isinstance(results.get("documents", [None])[0], list):
        docs = results.get("documents", [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        ids = (results.get("ids") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
    else:
        # Flat structure (from get)
        docs = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        ids = results.get("ids", [])
        distances = results.get("distances", [])

    # Convert metadatas dict to list if necessary
    if isinstance(metadatas, dict) and isinstance(ids, list):
        metadatas = [metadatas.get(i, {}) for i in ids]

    # If any are None, replace with empty lists
    return docs or [], metadatas or [], ids or [], distances or []



#core logic
def retrieve_context(query: str, top_k: int = 5, method:str = "rrf") -> tuple[str, list[dict]]:
    """Embed the query and retrieve context documents + metadata from Chroma."""
    query_emb = embedder.encode(query, task="retrieval.query", convert_to_numpy=True)
    if query_emb.ndim == 1:
        query_emb = [query_emb.tolist()]

    if method == 'cosine':
        results = collection.query(query_embeddings=query_emb, n_results=top_k)
    elif method == 'rrf':
        try:
            chroma_data = collection.get(include=['embeddings', 'documents','metadatas'])
            if chroma_data:
                logging.info("Have Chroma Data")
            docs = chroma_data.get('documents') or []
            if not docs:
                logging.error("No Documents")
            doc_embs = np.array(chroma_data['embeddings'])
            doc_ids = np.array(chroma_data['ids'])

            cos_scores = cosine_similarity(query_emb, doc_embs)[0]
            cosine_rank = [doc_ids[i] for i in np.argsort(cos_scores)[::-1][:top_k * 2]]

            tokenized_corpus = [tokenize(d) for d in docs]
            bm25 = BM25Okapi(tokenized_corpus)
            bm25_scores = bm25.get_scores(tokenize(query))

            bm25_rank = [doc_ids[i] for i in np.argsort(bm25_scores)[::-1][:top_k * 2]]
            fused = reciprocal_rank_fusion([cosine_rank, bm25_rank])
            fused_doc_ids = [doc_id for doc_id, _ in fused[:top_k]]

            results = collection.get(ids=fused_doc_ids)
        except Exception as e:
            logging.error(f"Issue with RRF: {e}")

    else:
        raise ValueError(f"Unkown retrieval method: {method}")
    
    if not results["documents"] or not results["documents"][0]:
        logger.warning("No context retrieved from Chroma.")
        return "", []
    
    docs, metadatas, ids, distances = normalize_chroma_results(results)

    citations: list[dict] = []
    for idx, doc in enumerate(docs):
        metadata = metadatas[idx] if idx < len(metadatas) else {}
        label = (
            metadata.get("title")
            or metadata.get("source_title")
            or metadata.get("source")
            or metadata.get("document")
            or metadata.get("url")
            or ids[idx] if idx < len(ids) else None
        )
        url = metadata.get("url") or metadata.get("source_url")
        citation = {
            "id": ids[idx] if idx < len(ids) else None,
            "score": distances[idx] if idx < len(distances) else None,
            "label": label,
            "section": metadata.get("section"),
            "url": url,
        }
        citations.append(citation)

    context = "\n".join(docs)
    logger.info(f"Retrieved {len(docs)} documents from Chroma for Query: {query}")
    return context, citations

def retrieve_agent_context(session_id: str | None) -> str:
    """Fetch chat and uploaded document context from agent"""
    if not session_id:
        return ""
    try:
        response = requests.get(f"{AGENT_URL}/sessions/{session_id}/context")
        response.raise_for_status()
        data = response.json()

        # Recent messages
        messages_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in data.get("recent_messages", [])
        )

        # Document fields
        w2 = data.get("w2_fields", {})
        f1099 = data.get("form1099_fields", {})
        portfolio = data.get("portfolio_fields", {})
        
        def format_fields(fields: dict, title: str):
            return (
                f"\n\n{title}:\n" +
                "\n".join([f"{k}: {v}" for k, v in fields.items() if v is not None])
                if fields else ""
            )
        
        return (
            messages_text + 
            format_fields(w2, "W-2 Data") + 
            format_fields(f1099, "1099 Data") +
            format_fields(portfolio, "Portfolio Summary")
        )
    
    except Exception as e:
        logger.warning(f"Failed to fetch agent context: {e}")
        return ""

def generate_answer(prompt: str) -> str:
    """Query the VertexAI LLM."""
    try:
        return llm.invoke(prompt)
    except Exception as e:
        logger.error(f"LLM query failed: {e}")
        return f"Error: {e}"

#API endpoint
@app.post("/query")
async def handle_query(req: QueryRequest):
    # Fetch agentic context (chat messages + W-2 fields)
    agent_context = retrieve_agent_context(req.session_id)

    # Fetch Chroma context
    chroma_context, citations = retrieve_context(req.query, top_k=req.top_k, method='rrf')

    # Combine contexts
    full_context = ""
    if agent_context:
        full_context += agent_context
    if chroma_context:
        if full_context:
            full_context += "\n\n"  # separate agent & Chroma
        full_context += chroma_context

    logger.info(f"Full context for query '{req.query}':\n{full_context}")

    # Build optional sources section for the prompt
    sources_text = ""
    if citations:
        source_lines = []
        for index, item in enumerate(citations, start=1):
            label = item.get("label") or f"Source {index}"
            section = item.get("section")
            source_lines.append(
                f"[S{index}] {label}" + (f" — {section}" if section else "")
            )
        sources_text = "\n\nSources:\n" + "\n".join(source_lines)

    # Build LLM prompt
    prompt = (
        "You are FinWhiz, a financial education assistant. "
        "Use the context below to answer clearly and accurately.\n\n"
        f"Context:\n{full_context}{sources_text}\n\n"
        f"User query: {req.query}"
    )

    answer = generate_answer(prompt)
    return {"answer": answer, "context": full_context, "sources": citations}
    
#health check
@app.get("/health")
def health_check():
    return {"status": "ok"}
