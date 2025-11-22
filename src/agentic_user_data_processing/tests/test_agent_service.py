import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from google.api_core.exceptions import NotFound

from agentic_user_data_processing.services import context as context_service
from agentic_user_data_processing.services import storage as storage_service


@pytest.fixture(autouse=True)
def configure_storage(tmp_path, monkeypatch):
    creds = tmp_path / "creds.json"
    creds.write_text("{}")
    monkeypatch.setattr(storage_service, "KEY_PATH", str(creds))
    monkeypatch.setattr(storage_service, "BUCKET_NAME", "unit-test-bucket")
    monkeypatch.setattr(storage_service, "LOCAL_FALLBACK_DIR", tmp_path / "uploads")
    yield


def test_save_document_bytes_uploads(monkeypatch):
    captured_metadata = {}

    class DummyBlob:
        def __init__(self):
            self.upload_calls = 0

        def upload_from_string(self, data, content_type=None):
            self.upload_calls += 1
            assert data.startswith(b"content")
            assert content_type == "application/pdf"

    dummy_blob = DummyBlob()

    class DummyBucket:
        def __init__(self):
            self.last_blob_name = None

        def blob(self, name):
            self.last_blob_name = name
            return dummy_blob

    dummy_bucket = DummyBucket()

    class DummyClient:
        def bucket(self, _name):
            return dummy_bucket

    monkeypatch.setattr(storage_service, "_get_gcs_client", lambda: DummyClient())
    monkeypatch.setattr(storage_service, "_load_session_metadata", lambda *_: [])

    def _save(bucket, session_id, metadata_list):
        captured_metadata["session"] = session_id
        captured_metadata["entries"] = metadata_list

    monkeypatch.setattr(storage_service, "_save_session_metadata", _save)

    class FixedDateTime:
        @staticmethod
        def utcnow():
            class Stamp:
                def strftime(self, _fmt):
                    return "20240102T030405"

            return Stamp()

    monkeypatch.setattr(storage_service, "datetime", FixedDateTime)

    uri = storage_service.save_document_bytes(
        session_id="abc",
        filename="w2.pdf",
        contents=b"content-bytes",
        content_type="application/pdf",
    )

    assert uri == "gs://unit-test-bucket/sessions/abc/20240102T030405_w2.pdf"
    assert dummy_blob.upload_calls == 1
    assert captured_metadata["session"] == "abc"
    assert captured_metadata["entries"][0]["filename"] == "w2.pdf"


def test_save_document_bytes_falls_back_to_local(monkeypatch, tmp_path):
    class DummyBlob:
        def upload_from_string(self, *_args, **_kwargs):
            raise RuntimeError("fail upload")

    class DummyBucket:
        def blob(self, _name):
            return DummyBlob()

    class DummyClient:
        def bucket(self, _name):
            return DummyBucket()

    monkeypatch.setattr(storage_service, "_get_gcs_client", lambda: DummyClient())
    monkeypatch.setattr(storage_service, "_load_session_metadata", lambda *_: [])
    monkeypatch.setattr(storage_service, "_save_session_metadata", lambda *args, **kwargs: None)

    result = storage_service.save_document_bytes(
        session_id="xyz",
        filename="form.pdf",
        contents=b"fallback",
        content_type="application/pdf",
    )

    local_path = Path(result)
    assert local_path.exists()
    assert local_path.read_bytes() == b"fallback"


def test_load_session_metadata_handles_not_found():
    class DummyBlob:
        def download_as_text(self):
            raise NotFound("missing file")

    class DummyBucket:
        def blob(self, _name):
            return DummyBlob()

    data = storage_service._load_session_metadata(DummyBucket(), "sess-1")
    assert data == []


def test_save_session_metadata_uploads_json():
    captured = {}

    class DummyBlob:
        def upload_from_string(self, data, content_type=None):
            captured["data"] = data
            captured["content_type"] = content_type

    class DummyBucket:
        def blob(self, _name):
            return DummyBlob()

    storage_service._save_session_metadata(DummyBucket(), "sess-2", [{"filename": "doc.pdf"}])
    assert json.loads(captured["data"])[0]["filename"] == "doc.pdf"
    assert captured["content_type"] == "application/json"


def test_build_context_includes_documents():
    session = SimpleNamespace(id="f1e21111-1111-1111-1111-111111111111", user_id="d1e21111-1111-1111-1111-111111111111")
    messages = [
        SimpleNamespace(role="assistant", content="Hi", created_at=datetime.utcnow()),
        SimpleNamespace(role="user", content="Hello", created_at=datetime.utcnow()),
    ]
    documents = [
        SimpleNamespace(
            id="2f5d2222-2222-2222-2222-222222222222",
            session_id="f1e21111-1111-1111-1111-111111111111",
            document_type="w2",
            gcs_uri="gs://bucket/file",
            raw_metadata=json.dumps({"employee_name": "Alice"}),
            created_at=datetime.utcnow(),
        )
    ]

    ctx = context_service.build_context(session=session, messages=messages, documents=documents)
    assert ctx.session_id == "f1e21111-1111-1111-1111-111111111111"
    assert ctx.w2_fields.employee_name == "Alice"
    assert ctx.recent_messages[0].role == "user"  # reversed order
