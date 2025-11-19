import pytest

from query_client import interactive_query


class DummyResponse:
    def __init__(self, payload=None, status=200):
        self._payload = payload or {}
        self.status_code = status
        self.raise_called = False

    def json(self):
        return self._payload

    def raise_for_status(self):
        self.raise_called = True
        if self.status_code >= 400:
            raise RuntimeError("error")


def test_create_session_posts(monkeypatch):
    captured = {}

    def fake_post(url, json):
        captured["url"] = url
        captured["json"] = json
        return DummyResponse({"id": "sess-1"})

    monkeypatch.setattr(interactive_query.requests, "post", fake_post)
    session_id = interactive_query.create_session("user-1")
    assert session_id == "sess-1"
    assert captured["url"].endswith("/sessions/")
    assert captured["json"]["user_id"] == "user-1"


def test_log_message_raises_on_failure(monkeypatch):
    resp = DummyResponse(status=500)

    def fake_post(*_args, **_kwargs):
        return resp

    monkeypatch.setattr(interactive_query.requests, "post", fake_post)
    with pytest.raises(RuntimeError):
        interactive_query.log_message("sess", "user", "content")
    assert resp.raise_called


def test_query_llm_returns_payload(monkeypatch):
    payload = {"answer": "42"}

    def fake_post(url, json):
        assert "query" in json
        return DummyResponse(payload)

    monkeypatch.setattr(interactive_query.requests, "post", fake_post)
    result = interactive_query.query_llm("user", "sess", "question")
    assert result["answer"] == "42"
