import os
import uuid
import requests

LLM_URL = os.environ.get("LLM_URL", "http://llm:8001/query")
AGENT_URL = os.environ.get("AGENT_URL", "http://agent:8010")


def create_session(user_id: uuid.UUID) -> str:
    response = requests.post(f"{AGENT_URL}/sessions/", json={"user_id": str(user_id)})
    response.raise_for_status()
    return response.json()["id"]


def log_message(session_id: str, role: str, content: str) -> None:
    response = requests.post(
        f"{AGENT_URL}/sessions/{session_id}/messages",
        json={"role": role, "content": content},
    )
    response.raise_for_status()


def main():
    user_id = uuid.uuid4()
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

        llm_resp = requests.post(
            LLM_URL,
            json={
                "query": user_input,
                "session_id": session_id,
                "top_k": 5,
            },
        )
        llm_resp.raise_for_status()
        answer = llm_resp.json().get("answer", "")
        print(f"\nLLM Answer:\n{answer}")


if __name__ == "__main__":
    main()
