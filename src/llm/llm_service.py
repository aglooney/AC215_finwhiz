import os
import logging
import requests
from typing import Optional
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
GCS_PREFIX = os.getenv("GCS_PREFIX", "chroma_storage")
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

def retrieve_context(query: str, top_k: int = 5) -> str:
    """Embed the query and retrieve context documents from Chroma."""
    query_emb = embedder.encode(query, task="retrieval.passage", convert_to_numpy=True)
    if query_emb.ndim == 1:
        query_emb = [query_emb.tolist()]

    results = collection.query(query_embeddings=query_emb, n_results=top_k)
    if not results["documents"] or not results["documents"][0]:
        logger.warning("No context retrieved from Chroma.")
        return ""

    docs = results["documents"][0]
    context = "\n".join(docs)
    logger.info(f"Retrieved {len(docs)} documents from Chroma for Query: {query}")
    return context

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
        chroma_context = retrieve_context(req.query, top_k=req.top_k)

        # Combine contexts
        full_context = ""
        if agent_context:
            full_context += agent_context
        if chroma_context:
            if full_context:
                full_context += "\n\n"  # separate agent & Chroma
            full_context += chroma_context

        logger.info(f"Full context for query '{req.query}':\n{full_context}")

        # Build LLM prompt
        prompt = (
            "You are FinWhiz, a financial education assistant. "
            "Use the context below to answer clearly and accurately.\n\n"
            f"Context:\n{full_context}\n\n"
            f"User query: {req.query}"
        )

        answer = generate_answer(prompt)
        return {"answer": answer, "context": full_context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))