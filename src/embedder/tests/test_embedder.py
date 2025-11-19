import io
import gzip
import os

os.environ.setdefault("FINWHIZ_TEST_MODE", "1")
os.environ.setdefault("GCS_BUCKET", "dummy-bucket")
os.environ.setdefault("BUCKET_CREDENTIALS", "dummy-creds.json")

from embedder import embedding  # noqa: E402


def test_chunk_text_respects_max_chars():
    text = "abcdefghij"
    chunks = embedding.chunk_text(text, max_chars=3)
    assert chunks == ["abc", "def", "ghi", "j"]


def test_clean_metadata_fills_defaults():
    meta = {"title": None, "year": None}
    cleaned = embedding.clean_metadata(meta)
    assert cleaned["title"] == "N/A"
    assert cleaned["year"] == -1
    assert cleaned["doctype"] == "N/A"


def test_store_records_adds_embeddings(monkeypatch):
    fake_collection_calls = {}

    class DummyCollection:
        def add(self, **kwargs):
            fake_collection_calls.update(kwargs)

    monkeypatch.setattr(embedding, "embed_texts", lambda texts: [[0.1]] * len(texts))

    records = [{"id": "doc", "text": "hello world", "title": "Title"}]
    stored = embedding.store_records(records, DummyCollection())

    assert stored == 1
    assert fake_collection_calls["ids"] == ["doc_chunk0"]
    assert fake_collection_calls["documents"][0] == "hello world"


def test_store_records_skips_empty_text(monkeypatch):
    monkeypatch.setattr(embedding, "embed_texts", lambda texts: [[0.1]] * len(texts))

    class DummyCollection:
        def add(self, **_kwargs):
            raise AssertionError("should not add")

    stored = embedding.store_records([{"id": "doc", "text": ""}], DummyCollection())
    assert stored == 0


class _DummyBlob:
    def __init__(self, data: str | bytes):
        self.data = data

    def open(self, mode: str):
        if "r" in mode and "b" not in mode:
            return io.StringIO(self.data)
        return io.BytesIO(self.data if isinstance(self.data, bytes) else self.data.encode("utf-8"))


class _DummyBucket:
    def __init__(self, data: str | bytes):
        self.data = data

    def blob(self, _name):
        return _DummyBlob(self.data)


def test_stream_ndjson_from_blob(monkeypatch):
    bucket = _DummyBucket('{"id": 1}\n{"id": 2}\n')
    rows = list(embedding.stream_ndjson_from_blob(bucket, "dummy"))
    assert rows == [{"id": 1}, {"id": 2}]


def test_stream_jsonl_gz_from_blob():
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb") as gz:
        gz.write(b'{"id": 1}\n{"id": 2}\n')
    bucket = _DummyBucket(buffer.getvalue())
    rows = list(embedding.stream_jsonl_gz_from_blob(bucket, "dummy"))
    assert rows == [{"id": 1}, {"id": 2}]
