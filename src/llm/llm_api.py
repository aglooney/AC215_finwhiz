from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from .language import query_llm  # Import the function above

app = FastAPI()

RETRIEVER_URL = os.environ.get("RETRIEVER_URL", "http://retriever:8000/retrieve")


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/query")
def llm_endpoint(request: QueryRequest):
    """
    This endpoint:
    1. Calls the Retriever service for context
    2. Sends the context + query to the LLM
    3. Returns the generated answer
    """
    try:
        # Step 1: call the retriever
        retriever_resp = requests.post(
            RETRIEVER_URL, json={"user_query": request.query, "top_k": request.top_k}
        )
        retriever_resp.raise_for_status()
        context = retriever_resp.json().get("context", "")

        # Step 2: build prompt for LLM
        prompt = f"Answer using the following context:\n{context}\n\nQuery: {request.query}"

        # Step 3: call LLM via language.py
        answer = query_llm(prompt)

        return {"answer": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
