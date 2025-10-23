import os
import uuid
import requests

LLM_URL = os.environ.get("LLM_URL", "http://llm:8001")
AGENT_URL = os.environ.get("AGENT_URL", "http://agent:8010")


def create_session(user_id: str) -> str:
    response = requests.post(f"{AGENT_URL}/sessions/", json={"user_id": str(user_id)})
    response.raise_for_status()
    return response.json()["id"]


def log_message(session_id: str, role: str, content: str) -> None:
    response = requests.post(
        f"{AGENT_URL}/sessions/{session_id}/messages",
        json={"role": role, "content": content},
    )
    response.raise_for_status()

def query_llm(user_id: str, session_id: str, query: str) -> str:
    """Send a query to the combined LLM service"""
    payload = {
        "query": query,
        "session_id": session_id,
        "user_id": user_id,
        "top_k": 5,
    }
    response = requests.post(f"{LLM_URL}/query", json=payload)
    response.raise_for_status()
    return response.json()

def main():
    user_id = str(uuid.uuid4())
    session_id = create_session(user_id)
    print(f"Started session {session_id} for user {user_id}")

    while True:
        user_input = input("\nEnter your query (or 'exit' to quit): ")
        if user_input.lower() == "exit":
            break

        try:
            log_message(session_id, "user", user_input)
        except Exception as exc:
            print(f"[warn] failed to record user message: {exc}")
        try:
            response = query_llm(user_id, session_id, user_input)
            answer = response.get("answer", "")
            context = response.get("context", "")
            sources = response.get("sources") or []

            print("\nLLM Answer:\n", answer)
            print("\nContext Provided:\n", context)

            if sources:
                print("\nSources:")
                for idx, item in enumerate(sources, start=1):
                    label = item.get("label") or item.get("url") or item.get("id") or f"Source {idx}"
                    section = item.get("section")
                    url = item.get("url")
                    print(f"  [S{idx}] {label}")
                    if section:
                        print(f"     Section: {section}")
                    if url:
                        print(f"     URL: {url}")

            try:
                log_message(session_id, "assistant", answer)
            except Exception as exc:
                print(f"[warn] Failed to record assistant message: {exc}")
        
        except Exception as exc:
            print(f"[error] Query failed: {exc}")
if __name__ == "__main__":
    main()
