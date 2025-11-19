import os
from importlib import reload
from pathlib import Path
from uuid import uuid4

import chromadb
import numpy as np
import pytest
from chromadb.config import Settings

os.environ.setdefault("FINWHIZ_TEST_MODE", "1")
os.environ.setdefault("GCS_BUCKET", "dummy-bucket")
os.environ.setdefault("BUCKET_CREDENTIALS", "tests/fake-creds.json")
os.environ.setdefault("VERTEXAI_CREDENTIALS", "tests/fake-creds.json")

FAKE_CREDS = Path(__file__).resolve().parents[1] / "fake-creds.json"
FAKE_CREDS.parent.mkdir(parents=True, exist_ok=True)
if not FAKE_CREDS.exists():
    FAKE_CREDS.write_text("{}")

import embedder.embedding as embedding_module  # noqa: E402
import llm.llm_service as llm_service_module  # noqa: E402


@pytest.fixture()
def llm_embedder_env(monkeypatch):
    """Provide a shared Chroma collection plus patched embedder/LLM for integration tests."""
    embedding = reload(embedding_module)
    llm_service = reload(llm_service_module)

    client = chromadb.Client(Settings(anonymized_telemetry=False))
    collection_name = f"test_{uuid4()}"
    collection = client.get_or_create_collection(name=collection_name)

    def fake_embed_texts(texts):
        return [[float(idx + 1), float(idx + 2), float(idx + 3)] for idx, _ in enumerate(texts)]

    class DummyQueryEmbedder:
        def encode(self, query, task="retrieval.query", convert_to_numpy=True):
            if isinstance(query, list):
                query = query[0]
            magnitude = 2.0 if "market" in query.lower() else 1.0
            return np.array([[magnitude, magnitude, magnitude]])

    class DummyLLM:
        def __init__(self):
            self.prompts: list[str] = []

        def invoke(self, prompt: str) -> str:
            self.prompts.append(prompt)
            return "integration-answer"

    monkeypatch.setattr(embedding, "embed_texts", fake_embed_texts)
    dummy_embedder = DummyQueryEmbedder()
    dummy_llm = DummyLLM()
    monkeypatch.setattr(llm_service, "collection", collection)
    monkeypatch.setattr(llm_service, "embedder", dummy_embedder)
    monkeypatch.setattr(llm_service, "llm", dummy_llm)

    def ingest_records(records):
        return embedding.store_records(records, collection)

    yield {
        "collection": collection,
        "embedding": embedding,
        "llm_service": llm_service,
        "ingest": ingest_records,
        "dummy_llm": dummy_llm,
    }

    client.delete_collection(name=collection_name)
