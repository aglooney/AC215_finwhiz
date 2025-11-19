from fastapi.testclient import TestClient

from query_client import interactive_query

from .helpers import ResponseAdapter, build_agent_stub


def test_query_client_roundtrip_through_agent_and_llm(monkeypatch, llm_embedder_env):
    env = llm_embedder_env
    env["ingest"](
        [
            {
                "id": "doc-42",
                "text": "Detailed market commentary was published today.",
                "title": "Daily Commentary",
                "source_url": "http://example.com/daily",
            }
        ]
    )

    agent_app, agent_state = build_agent_stub()
    agent_client = TestClient(agent_app)
    llm_client = TestClient(env["llm_service"].app)

    agent_base = "http://agent.test"
    llm_base = "http://llm.test"

    def dispatch_post(url, json=None, **kwargs):
        if url.startswith(agent_base):
            path = url[len(agent_base) :] or "/"
            return ResponseAdapter(agent_client.post(path, json=json))
        if url.startswith(llm_base):
            path = url[len(llm_base) :] or "/"
            return ResponseAdapter(llm_client.post(path, json=json))
        raise AssertionError(f"unexpected POST url {url}")

    def dispatch_get(url, params=None, **kwargs):
        if url.startswith(agent_base):
            path = url[len(agent_base) :] or "/"
            return ResponseAdapter(agent_client.get(path, params=params))
        raise AssertionError(f"unexpected GET url {url}")

    monkeypatch.setattr(env["llm_service"], "AGENT_URL", agent_base)
    monkeypatch.setattr(interactive_query, "AGENT_URL", agent_base)
    monkeypatch.setattr(interactive_query, "LLM_URL", llm_base)
    monkeypatch.setattr(interactive_query.requests, "post", dispatch_post)
    monkeypatch.setattr(env["llm_service"].requests, "get", dispatch_get)

    from uuid import uuid4

    user_id = str(uuid4())
    session_id = interactive_query.create_session(user_id)
    interactive_query.log_message(session_id, "user", "How are the markets doing?")
    result = interactive_query.query_llm(user_id, session_id, "Provide a market summary")

    assert session_id in agent_state["sessions"]
    assert agent_state["sessions"][session_id][0]["content"] == "How are the markets doing?"

    assert result["answer"] == "integration-answer"
    assert "markets doing" in result["context"]
    assert any(cit["label"] == "Daily Commentary" for cit in result["sources"])
