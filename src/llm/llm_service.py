import os
import logging
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
from langchain_google_vertexai import VertexAI
import uuid


from .chroma_utils import ensure_chroma_local

# load environment
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_service")

# configuration
CHROMA_PATH = os.getenv("CHROMA_PATH", "/app/src/chroma_storage")
COLLECTION_DIR = "1a90eda1-e932-4e73-89dd-edb1adf9d126"
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "finwhiz_docs")
GCS_BUCKET = os.getenv("GCS_BUCKET")
GCS_PREFIX = os.getenv("GCS_PREFIX", "chroma_storage_backup")
AGENT_URL = os.getenv("AGENT_URL", "http://agent:8010")

TEST_MODE = os.getenv("FINWHIZ_TEST_MODE") == "1"

VERTEXAI_CREDENTIALS = os.getenv("VERTEXAI_CREDENTIALS")
if not VERTEXAI_CREDENTIALS and not TEST_MODE:
    raise ValueError("VERTEXAI_CREDENTIALS must be set")

if VERTEXAI_CREDENTIALS:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = VERTEXAI_CREDENTIALS

if not TEST_MODE:
    ensure_chroma_local(GCS_BUCKET, GCS_PREFIX, COLLECTION_DIR, CHROMA_PATH)
    logger.info("Initializing ChromaDB client")
    client = PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME)

    logger.info("Loading embedding model")
    embedder = SentenceTransformer("jinaai/jina-embeddings-v3", device="cpu", trust_remote_code=True)

    logger.info("Initializing Vertex AI model")
    llm = VertexAI(model_name="gemini-2.5-pro")
else:
    client = None
    collection = None
    embedder = None
    llm = None


app = FastAPI(title="FinWhiz LLM Service")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
    return sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)


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


# core logic
def retrieve_context(query: str, top_k: int = 5, method: str = "rrf") -> tuple[str, list[dict]]:
    """Embed the query and retrieve context documents + metadata from Chroma."""
    if embedder is None or collection is None:
        raise RuntimeError("Chroma collection or embedder is not initialized")
    query_emb = embedder.encode(query, task="retrieval.query", convert_to_numpy=True)
    if query_emb.ndim == 1:
        query_emb = [query_emb.tolist()]

    if method == "cosine":
        results = collection.query(query_embeddings=query_emb, n_results=top_k)
    elif method == "rrf":
        try:
            chroma_data = collection.get(include=["embeddings", "documents", "metadatas"])
            if chroma_data:
                logging.info("Have Chroma Data")
            docs = chroma_data.get("documents") or []
            if not docs:
                logging.error("No Documents")
            doc_embs = np.array(chroma_data["embeddings"])
            doc_ids = np.array(chroma_data["ids"])

            cos_scores = cosine_similarity(query_emb, doc_embs)[0]
            cosine_rank = [doc_ids[i] for i in np.argsort(cos_scores)[::-1][: top_k * 2]]

            tokenized_corpus = [tokenize(d) for d in docs]
            bm25 = BM25Okapi(tokenized_corpus)
            bm25_scores = bm25.get_scores(tokenize(query))

            bm25_rank = [doc_ids[i] for i in np.argsort(bm25_scores)[::-1][: top_k * 2]]
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
            metadata.get("title") or metadata.get("source_title") or metadata.get("source") or metadata.get("document") or metadata.get("url") or ids[idx]
            if idx < len(ids)
            else None
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


def retrieve_agent_context(session_id: str | None) -> tuple[str, dict]:
    """
    Fetch chat and uploaded document context from agent.
    Now also fetches live portfolio data and market overview.

    Returns:
        tuple: (formatted_context_string, raw_data_dict)
    """
    if not session_id:
        return "", {}

    context_parts = []
    raw_data = {}

    try:
        # 1. Get basic session context (messages, documents)
        response = requests.get(f"{AGENT_URL}/sessions/{session_id}/context")
        response.raise_for_status()
        data = response.json()
        raw_data["session"] = data

        # Recent messages
        messages_text = "\n".join(f"{m['role']}: {m['content']}" for m in data.get("recent_messages", []))
        if messages_text:
            context_parts.append(f"Recent Conversation:\n{messages_text}")

        # 2. Get live portfolio data (current prices, gains/losses)
        try:
            portfolio_response = requests.get(f"{AGENT_URL}/sessions/{session_id}/portfolio/live")
            if portfolio_response.status_code == 200:
                live_portfolio = portfolio_response.json()
                raw_data["live_portfolio"] = live_portfolio

                # Format live portfolio for context
                portfolio_context = format_live_portfolio(live_portfolio)
                if portfolio_context:
                    context_parts.append(portfolio_context)
        except Exception as e:
            logger.warning(f"Could not fetch live portfolio data: {e}")

        # 3. Get market overview (indices)
        try:
            market_response = requests.get(f"{AGENT_URL}/market/indices")
            if market_response.status_code == 200:
                market_data = market_response.json()
                raw_data["market_overview"] = market_data

                # Format market overview
                market_context = format_market_overview(market_data)
                if market_context:
                    context_parts.append(market_context)
        except Exception as e:
            logger.warning(f"Could not fetch market overview: {e}")

        # 4. Add W-2 and 1099 data if available
        w2 = data.get("w2_fields", {})
        f1099 = data.get("form1099_fields", {})

        if w2:
            w2_text = format_tax_fields(w2, "W-2 Tax Data")
            if w2_text:
                context_parts.append(w2_text)

        if f1099:
            f1099_text = format_tax_fields(f1099, "1099 Tax Data")
            if f1099_text:
                context_parts.append(f1099_text)

        return "\n\n".join(context_parts), raw_data

    except Exception as e:
        logger.warning(f"Failed to fetch agent context: {e}")
        return "", {}


def format_live_portfolio(portfolio_data: dict) -> str:
    """Format live portfolio data for LLM context."""
    lines = ["=== YOUR PORTFOLIO (LIVE DATA) ==="]

    # Account info
    if portfolio_data.get("account_name"):
        lines.append(f"Account: {portfolio_data['account_name']}")
    if portfolio_data.get("account_type"):
        lines.append(f"Type: {portfolio_data['account_type']}")

    # Overall performance
    total_current = portfolio_data.get("total_current_value", 0)
    total_original = portfolio_data.get("total_original_value", 0)
    total_gain_loss = portfolio_data.get("total_gain_loss", 0)
    total_gain_loss_pct = portfolio_data.get("total_gain_loss_percent", 0)

    lines.append(f"\nTotal Value: ${total_current:,.2f}")
    lines.append(f"Original Value: ${total_original:,.2f}")
    lines.append(f"Total Gain/Loss: ${total_gain_loss:,.2f} ({total_gain_loss_pct:+.2f}%)")

    # Individual holdings
    holdings = portfolio_data.get("holdings", [])
    if holdings:
        lines.append(f"\nHoldings ({len(holdings)} positions):")

        for holding in holdings:
            ticker = holding.get("ticker", "N/A")
            name = holding.get("name", "N/A")
            shares = holding.get("shares", 0)
            current_price = holding.get("current_price", 0)
            current_value = holding.get("current_value", 0)
            gain_loss = holding.get("gain_loss", 0)
            gain_loss_pct = holding.get("gain_loss_percent", 0)
            day_change_pct = holding.get("day_change_percent", 0)

            # Calculate allocation percentage
            allocation_pct = (current_value / total_current * 100) if total_current > 0 else 0

            lines.append(
                f"\n  • {ticker} ({name})"
                f"\n    - Shares: {shares:,.2f}"
                f"\n    - Current Price: ${current_price:,.2f}"
                f"\n    - Position Value: ${current_value:,.2f} ({allocation_pct:.1f}% of portfolio)"
                f"\n    - Total Gain/Loss: ${gain_loss:,.2f} ({gain_loss_pct:+.2f}%)"
                f"\n    - Today's Change: {day_change_pct:+.2f}%"
            )

    updated_at = portfolio_data.get("updated_at", "N/A")
    lines.append(f"\nLast Updated: {updated_at}")

    return "\n".join(lines)


def format_market_overview(market_data: dict) -> str:
    """Format market indices data for LLM context."""
    indices = market_data.get("indices", [])
    if not indices:
        return ""

    lines = ["=== MARKET OVERVIEW ==="]

    for index in indices:
        symbol = index.get("symbol", "N/A")
        name = index.get("name", "N/A")
        price = index.get("price", 0)
        change = index.get("change", 0)
        change_pct = index.get("change_percent", 0)

        lines.append(f"{name} ({symbol}): ${price:,.2f} ({change:+.2f}, {change_pct:+.2f}%)")

    updated_at = market_data.get("updated_at", "N/A")
    lines.append(f"\nMarket data as of: {updated_at}")

    return "\n".join(lines)


def format_tax_fields(fields: dict, title: str) -> str:
    """Format tax document fields for context."""
    if not fields:
        return ""

    lines = [f"=== {title} ==="]
    for key, value in fields.items():
        if value is not None:
            # Format key nicely (convert snake_case to Title Case)
            formatted_key = key.replace("_", " ").title()
            lines.append(f"{formatted_key}: {value}")

    return "\n".join(lines)


def generate_answer(prompt: str) -> str:
    """Query the VertexAI LLM."""
    if llm is None:
        raise RuntimeError("LLM client is not initialized")
    try:
        return llm.invoke(prompt)
    except Exception as e:
        logger.error(f"LLM query failed: {e}")
        return f"Error: {e}"


# API endpoint
@app.post("/query")
async def handle_query(req: QueryRequest):
    # Fetch agentic context (chat messages + documents + LIVE portfolio + market data)
    agent_context, raw_agent_data = retrieve_agent_context(req.session_id)

    # Fetch Chroma context
    chroma_context, citations = retrieve_context(req.query, top_k=req.top_k, method="rrf")

    # Combine contexts
    full_context = ""
    if agent_context:
        full_context += agent_context
    if chroma_context:
        if full_context:
            full_context += "\n\n"  # separate agent & Chroma
        full_context += "=== FINANCIAL EDUCATION KNOWLEDGE BASE ===\n"
        full_context += chroma_context

    logger.info(f"Full context for query '{req.query}':\n{full_context}")

    # Build optional sources section for the prompt
    sources_text = ""
    if citations:
        source_lines = []
        for index, item in enumerate(citations, start=1):
            label = item.get("label") or f"Source {index}"
            section = item.get("section")
            source_lines.append(f"[S{index}] {label}" + (f" — {section}" if section else ""))
        sources_text = "\n\nSources:\n" + "\n".join(source_lines)

    # Build enhanced LLM prompt with specific portfolio awareness
    prompt = build_enhanced_prompt(full_context, sources_text, req.query, raw_agent_data)

    answer = generate_answer(prompt)
    return {"answer": answer, "context": full_context, "sources": citations}


def build_enhanced_prompt(context: str, sources: str, query: str, raw_data: dict) -> str:
    """Build an enhanced prompt with portfolio-specific instructions."""

    # Check if user has portfolio data
    has_portfolio = bool(raw_data.get("live_portfolio", {}).get("holdings"))

    base_prompt = (
        "You are FinWhiz, an educational financial information assistant. "
        "You provide EDUCATIONAL information about financial concepts, portfolio composition, "
        "investment principles, allocation strategies, and market insights.\n\n"
    )

    if has_portfolio:
        portfolio_instructions = (
            "IMPORTANT - You have access to the user's live portfolio data with current market prices. "
            "You can:\n"
            "- Reference their specific holdings and allocations\n"
            "- Comment on how their stocks are performing TODAY (based on day change %)\n"
            "- Discuss their portfolio concentration (% allocations to each position)\n"
            "- Compare their holdings' performance to market indices\n"
            "- Provide educational context about diversification based on their actual positions\n\n"
            "When discussing their portfolio:\n"
            "- Be specific: mention tickers, percentages, and current values you see\n"
            "- Note winners and losers: identify positions with positive/negative performance\n"
            "- Frame as educational observations, NOT as personalized advice\n"
            "- Example: 'I notice AAPL makes up 25% of your portfolio and is up 2.3% today. "
            "From an educational perspective, having a single stock represent over 20% of a portfolio "
            "is considered high concentration...'\n\n"
        )
        base_prompt += portfolio_instructions
    else:
        base_prompt += (
            "YOU CAN answer allocation questions by providing educational examples with specific "
            "percentages (e.g., 'A common balanced approach is 60% stocks, 40% bonds'). "
            "Frame responses as educational examples, not personalized advice.\n\n"
        )

    disclaimer = (
        "CRITICAL DISCLAIMERS:\n"
        "- Always maintain educational framing - you are teaching, not advising\n"
        "- Add appropriate disclaimers when discussing investments\n"
        "- Never say 'you should buy/sell' - instead say 'educational principles suggest...'\n"
        "- Make it clear you are NOT a licensed financial advisor\n\n"
    )

    base_prompt += disclaimer

    full_prompt = (
        f"{base_prompt}"
        f"Context:\n{context}{sources}\n\n"
        f"User Question: {query}\n\n"
        f"Provide an educational response. Be specific about their portfolio if available. "
        f"Reference market conditions and stock performance where relevant."
    )

    return full_prompt


# health check
@app.get("/health")
def health_check():
    return {"status": "ok"}
