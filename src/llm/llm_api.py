import os
import logging
from typing import Optional, Dict, Any

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .language import query_llm  # Import the function above

app = FastAPI(title="FinWhiz RAG Service")

RETRIEVER_URL = os.environ.get("RETRIEVER_URL", "http://retriever:8000/retrieve")
AGENT_URL = os.environ.get("AGENT_URL", "http://agent:8010")

logger = logging.getLogger("llm_service")
logging.basicConfig(level=logging.INFO)


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    session_id: str
    context: Optional[str] = None


def fetch_agent_context(session_id: str) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(f"{AGENT_URL}/sessions/{session_id}/context")
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.warning("Failed to retrieve agent context: %s", exc)
        return None


def post_agent_message(session_id: str, role: str, content: str) -> None:
    try:
        response = requests.post(
            f"{AGENT_URL}/sessions/{session_id}/messages",
            json={"role": role, "content": content},
            timeout=5,
        )
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to post %s message to agent service: %s", role, exc)


def format_agent_context(agent_ctx: Dict[str, Any]) -> str:
    if not agent_ctx:
        return ""

    sections = []

    history_lines = []
    for turn in agent_ctx.get("recent_messages", []):
        role = turn.get("role", "user")
        content = turn.get("content", "")
        history_lines.append(f"{role}: {content}")
    if history_lines:
        sections.append("Recent conversation:\n" + "\n".join(history_lines))

    w2_fields = agent_ctx.get("w2_fields") or {}
    w2_lines = [
        f"{key.replace('_', ' ').title()}: {value}"
        for key, value in w2_fields.items()
        if value
    ]
    if w2_lines:
        sections.append("W-2 summary:\n" + "\n".join(w2_lines))

    summary = agent_ctx.get("summary")
    if summary:
        sections.append("Session summary:\n" + summary)

    return "\n\n".join(sections)


@app.post("/query")
def llm_endpoint(request: QueryRequest):
    """
    This endpoint:
    1. Calls the Retriever service for context
    2. Sends the context + query to the LLM
    3. Returns the generated answer
    """
    try:
        # Step 1: gather RAG context
        context = request.context
        if not context:
            try:
                retriever_resp = requests.post(
                    RETRIEVER_URL,
                    json={"user_query": request.query, "top_k": request.top_k},
                    timeout=15,
                )
                retriever_resp.raise_for_status()
                context = retriever_resp.json().get("context", "")
            except Exception as exc:
                logger.warning("Retriever call failed: %s", exc)
                context = ""

        agent_context = fetch_agent_context(request.session_id)
        agent_context_str = format_agent_context(agent_context) if agent_context else ""

        # Step 2: build prompt for LLM
        prompt_sections = [
            "You are FinWhiz, a financial education assistant. Use the provided information to answer clearly and accurately.",
        ]
        if agent_context_str:
            prompt_sections.append(agent_context_str)
        if context:
            prompt_sections.append(f"Retrieved documents:\n{context}")
        prompt_sections.append(f"User query: {request.query}")
        prompt = "\n\n".join(prompt_sections)

        # Step 3: call LLM via language.py
        answer = query_llm(prompt)

        # Step 4: persist assistant turn
        if answer:
            post_agent_message(request.session_id, "assistant", answer)

        return {"answer": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
