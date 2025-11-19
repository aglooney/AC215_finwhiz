from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.integration.helpers import ResponseAdapter, build_agent_stub

ROOT = Path(__file__).resolve().parents[2]
W2_SAMPLE = ROOT / "src" / "synthetic_data" / "w2" / "outputs" / "w2_000.pdf"
INT1099_SAMPLE = ROOT / "src" / "synthetic_data" / "int_1099" / "outputs" / "1099int_002_flat.pdf"


def test_full_pipeline_with_sample_documents(monkeypatch, llm_embedder_env):
    if not (W2_SAMPLE.exists() and INT1099_SAMPLE.exists()):
        pytest.skip("Sample synthetic documents missing")

    env = llm_embedder_env
    env["ingest"](
        [
            {
                "id": "doc-sample",
                "text": "This report discusses yearly wages and dividend earnings.",
                "title": "Annual Income Overview",
                "source_url": "http://example.com/annual",
            }
        ]
    )

    agent_app, _agent_state = build_agent_stub()
    agent_client = TestClient(agent_app)
    llm_client = TestClient(env["llm_service"].app)

    agent_base = "http://agent.pipeline"

    def dispatch_get(url, params=None, **kwargs):
        if url.startswith(agent_base):
            path = url[len(agent_base) :] or "/"
            return ResponseAdapter(agent_client.get(path, params=params))
        raise AssertionError(f"unexpected GET url {url}")

    monkeypatch.setattr(env["llm_service"], "AGENT_URL", agent_base)
    monkeypatch.setattr(env["llm_service"].requests, "get", dispatch_get)

    user_id = str(uuid4())
    session_resp = agent_client.post("/sessions/", json={"user_id": user_id})
    session_id = session_resp.json()["id"]

    uploads = [
        (INT1099_SAMPLE, f"/sessions/{session_id}/1099"),
        (W2_SAMPLE, f"/sessions/{session_id}/w2"),
    ]

    for path, endpoint in uploads:
        data = path.read_bytes()
        response = agent_client.post(
            endpoint,
            files={"file": (path.name, data, "application/pdf")},
        )
        payload = response.json()
        assert payload["filename"] == path.name
        assert payload["size"] == len(data)

    ctx = agent_client.get(f"/sessions/{session_id}/context").json()
    assert ctx["w2_fields"]["filename"] == W2_SAMPLE.name
    assert ctx["form1099_fields"]["filename"] == INT1099_SAMPLE.name

    agent_client.post(f"/sessions/{session_id}/messages", json={"role": "user", "content": "Please summarize my filings"})

    query_payload = {"query": "Summarize my filings", "session_id": session_id, "user_id": user_id}
    response = llm_client.post("/query", json=query_payload)
    result = response.json()

    assert result["answer"] == "integration-answer"
    assert W2_SAMPLE.name in result["context"]
    assert INT1099_SAMPLE.name in result["context"]
