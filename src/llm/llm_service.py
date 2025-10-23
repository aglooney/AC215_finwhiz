import os
import logging
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb import PersistentClient
from langchain_google_vertexai import VertexAI
import httpx
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

#core logic

def encode_query(query: str) -> list[list[float]]:
    """Encode a query string into the embedding space."""
    query_emb = embedder.encode(query, task="retrieval.query", convert_to_numpy=True)
    if query_emb.ndim == 1:
        return [query_emb.tolist()]
    return query_emb.tolist()


def retrieve_context(
    query: str,
    top_k: int = 5,
    query_embeddings: list[list[float]] | None = None,
    where: dict | None = None,
) -> tuple[list[str], list[dict], list[str]]:
    """Embed the query and retrieve documents, citations, and ids from Chroma."""
    embeddings = query_embeddings or encode_query(query)
    results = collection.query(query_embeddings=embeddings, n_results=top_k, where=where)
    if not results["documents"] or not results["documents"][0]:
        logger.warning("No context retrieved from Chroma.")
        return [], [], []

    docs = results["documents"][0]
    metadatas = (results.get("metadatas") or [[]])[0]
    ids = (results.get("ids") or [[]])[0]
    distances = results.get("distances") or [[]]
    distances = distances[0] if distances else []

    citations: list[dict] = []
    for idx, doc in enumerate(docs):
        metadata = metadatas[idx] if idx < len(metadatas) else {}
        label = (
            metadata.get("title")
            or (
                f"{metadata.get('indicator')} — {metadata.get('observation_date')}"
                if metadata.get("indicator") and metadata.get("observation_date")
                else None
            )
            or metadata.get("indicator")
            or metadata.get("source_title")
            or metadata.get("source")
            or metadata.get("document")
            or metadata.get("url")
            or (ids[idx] if idx < len(ids) else None)
        )
        url = metadata.get("url") or metadata.get("source_url")
        citation = {
            "id": ids[idx] if idx < len(ids) else None,
            "score": distances[idx] if idx < len(distances) else None,
            "label": label,
            "section": metadata.get("section"),
            "url": url,
            "doctype": metadata.get("doctype"),
            "indicator": metadata.get("indicator"),
            "observation_date": metadata.get("observation_date"),
            "value": metadata.get("value"),
            "units": metadata.get("units"),
            "category": metadata.get("category"),
        }
        citations.append(citation)

    logger.info(f"Retrieved {len(docs)} documents from Chroma for Query: {query}")
    return docs, citations, ids


def needs_macro_view(query: str) -> bool:
    """Detect if the user is asking about broad market timing."""
    macro_terms = (
        "invest",
        "market",
        "economy",
        "economic",
        "stocks",
        "equities",
        "recession",
        "interest rate",
        "inflation",
        "macro",
        "growth",
    )
    lowered = query.lower()
    return any(term in lowered for term in macro_terms)


def build_macro_signals(citations: list[dict]) -> str:
    """Summarize macro indicators surfaced in citations for the prompt."""
    lines = []
    for citation in citations:
        if citation.get("doctype") not in {"fred_indicator", "fred_summary"}:
            continue
        indicator = citation.get("indicator") or citation.get("label")
        if not indicator:
            continue
        pieces = [indicator]
        if citation.get("observation_date"):
            pieces.append(str(citation["observation_date"]))
        value = citation.get("value")
        if value is not None:
            if isinstance(value, (int, float)):
                value_str = f"{value:.2f}"
            else:
                value_str = str(value)
            units = citation.get("units")
            if units == "percent":
                value_str = f"{value_str}%"
            elif units:
                value_str = f"{value_str} {units}"
            pieces.append(value_str)
        if citation.get("category"):
            pieces.append(citation["category"].replace("_", " "))
        lines.append(" – ".join(pieces))

    if not lines:
        return ""
    return "Macro Signals:\n" + "\n".join(f"- {line}" for line in lines)

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

        # W-2 fields
        w2 = data.get("w2_fields")
        w2_text = ""
        if w2:
            w2_text = "\n".join([f"{k}: {v}" for k, v in w2.items()])

        return messages_text + ("\n\nW-2 Data:\n" + w2_text if w2_text else "")
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
    try:
        # Fetch agentic context (chat messages + W-2 fields)
        agent_context = retrieve_agent_context(req.session_id)

        # Fetch Chroma context
        query_embeddings = encode_query(req.query)
        docs, citations, ids = retrieve_context(
            req.query, top_k=req.top_k, query_embeddings=query_embeddings
        )

        if needs_macro_view(req.query):
            macro_docs, macro_citations, macro_ids = retrieve_context(
                req.query,
                top_k=max(req.top_k, 8),
                query_embeddings=query_embeddings,
                where={"doctype": {"$in": ["fred_indicator", "fred_summary"]}},
            )
            seen_ids = {doc_id for doc_id in ids if doc_id}
            filtered_docs = []
            filtered_citations = []
            for doc, citation, doc_id in zip(macro_docs, macro_citations, macro_ids):
                if doc_id and doc_id in seen_ids:
                    continue
                filtered_docs.append(doc)
                filtered_citations.append(citation)
                if doc_id:
                    seen_ids.add(doc_id)
            if filtered_docs:
                docs.extend(filtered_docs)
                citations.extend(filtered_citations)

        chroma_context = "\n".join(docs)

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

        macro_signals_text = build_macro_signals(citations)

        # Build LLM prompt
        prompt = (
            "You are FinWhiz, a financial education assistant. "
            "Use the context below to answer clearly and accurately."
        )

        if macro_signals_text:
            prompt += f"\n\n{macro_signals_text}"

        prompt += (
            f"\n\nContext:\n{full_context}{sources_text}\n\n"
            f"User query: {req.query}"
        )

        answer = generate_answer(prompt)
        return {"answer": answer, "context": full_context, "sources": citations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#health check
@app.get("/health")
def health_check():
    return {"status": "ok"}
