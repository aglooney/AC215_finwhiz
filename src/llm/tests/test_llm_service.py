import os
import numpy as np
import pytest

os.environ.setdefault("FINWHIZ_TEST_MODE", "1")
os.environ.setdefault("VERTEXAI_CREDENTIALS", "tests/fake-creds.json")

from llm import llm_service  # noqa: E402  (import after env is set)


class DummyEmbedder:
    def encode(self, query, task="retrieval.query", convert_to_numpy=True):
        return np.array([[0.1, 0.2]])


class DummyCollection:
    def __init__(self):
        self._results = {
            "documents": [["Doc 1"]],
            "metadatas": [[{"title": "Doc 1", "url": "http://example.com"}]],
            "ids": [["doc-1"]],
            "distances": [[0.1]],
        }

    def query(self, **_kwargs):
        return self._results

    def get(self, **_kwargs):
        return self._results


class DummyLLM:
    def __init__(self):
        self.prompts = []

    def invoke(self, prompt: str):
        self.prompts.append(prompt)
        return "dummy-response"


def test_reciprocal_rank_fusion_prefers_higher_scores():
    ranked = llm_service.reciprocal_rank_fusion([["a", "b"], ["b", "a"]], k=0)
    assert ranked[0][0] == "a"
    assert ranked[1][0] == "b"


def test_tokenize_lowercases_and_splits():
    assert llm_service.tokenize("Stocks & Bonds!") == ["stocks", "bonds"]


def test_normalize_chroma_results_handles_nested():
    nested = {
        "documents": [["Doc"]],
        "metadatas": [[{"title": "Doc"}]],
        "ids": [["id1"]],
        "distances": [[0.1]],
    }
    docs, metadatas, ids, distances = llm_service.normalize_chroma_results(nested)
    assert docs == ["Doc"]
    assert metadatas == [{"title": "Doc"}]
    assert ids == ["id1"]
    assert distances == [0.1]


def test_retrieve_agent_context_formats_sections(monkeypatch):
    payload = {
        "recent_messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}],
        "w2_fields": {"employee_name": "Alice"},
        "form1099_fields": {},
        "portfolio_fields": {"total_portfolio_value": "1000"},
    }

    class DummyResponse:
        status_code = 200

        def json(self):
            return payload

        def raise_for_status(self):
            return None

    monkeypatch.setattr(llm_service.requests, "get", lambda *_args, **_kwargs: DummyResponse())
    context, _ = llm_service.retrieve_agent_context("session-123")
    assert "user: Hello" in context
    assert "W-2 Tax Data" in context
    assert isinstance(context, str)


def test_retrieve_context_cosine_returns_context(monkeypatch):
    monkeypatch.setattr(llm_service, "embedder", DummyEmbedder())
    monkeypatch.setattr(llm_service, "collection", DummyCollection())
    context, citations = llm_service.retrieve_context("What is tax?", top_k=1, method="cosine")
    assert "Doc 1" in context
    assert citations[0]["label"] == "Doc 1"


def test_retrieve_context_raises_without_dependencies(monkeypatch):
    monkeypatch.setattr(llm_service, "embedder", None)
    monkeypatch.setattr(llm_service, "collection", None)
    with pytest.raises(RuntimeError):
        llm_service.retrieve_context("Question")


def test_generate_answer_uses_llm(monkeypatch):
    dummy = DummyLLM()
    monkeypatch.setattr(llm_service, "llm", dummy)
    response = llm_service.generate_answer("prompt")
    assert response == "dummy-response"
    assert dummy.prompts[0] == "prompt"
