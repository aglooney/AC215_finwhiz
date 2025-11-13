import os
from pathlib import Path

from llm import chroma_utils


def test_ensure_chroma_local_skips_when_present(monkeypatch, tmp_path):
    local_dir = tmp_path / "chroma"
    local_dir.mkdir()
    (local_dir / "existing").write_text("data")

    monkeypatch.setattr(chroma_utils.os.path, "exists", lambda p: True)
    monkeypatch.setattr(chroma_utils.os, "listdir", lambda p: ["existing"])

    called = {"client": False}

    def fake_client(*_args, **_kwargs):
        called["client"] = True
        raise AssertionError("Client should not be created when local data exists")

    monkeypatch.setattr(
        chroma_utils.storage.Client,
        "from_service_account_json",
        lambda *_args, **_kwargs: fake_client(),
    )

    chroma_utils.ensure_chroma_local("bucket", "prefix", "collection", str(local_dir))
    assert called["client"] is False


def test_ensure_chroma_local_downloads_missing(monkeypatch, tmp_path):
    local_dir = tmp_path / "chroma"
    creds = tmp_path / "creds.json"
    creds.write_text("{}")
    monkeypatch.setenv("BUCKET_CREDENTIALS", str(creds))

    class DummyBlob:
        def __init__(self, name):
            self.name = name
            self.saved = None

        def download_to_filename(self, dest):
            Path(dest).parent.mkdir(parents=True, exist_ok=True)
            Path(dest).write_text("blob")
            self.saved = dest

    blobs = [
        DummyBlob("chroma/chroma.sqlite3"),
        DummyBlob("chroma/1a90eda1-e932-4e73-89dd-edb1adf9d126/data.bin"),
        DummyBlob("chroma/ignore.txt"),
    ]

    class DummyBucket:
        def list_blobs(self, prefix):
            for blob in blobs:
                if blob.name.startswith(prefix):
                    yield blob

    class DummyClient:
        def bucket(self, _name):
            return DummyBucket()

    monkeypatch.setattr(
        chroma_utils.storage.Client,
        "from_service_account_json",
        lambda *_args, **_kwargs: DummyClient(),
    )

    chroma_utils.ensure_chroma_local(
        bucket_name="bucket",
        prefix="chroma",
        collection_dir="1a90eda1-e932-4e73-89dd-edb1adf9d126",
        local_path=str(local_dir),
    )

    expected_sqlite = local_dir / "chroma.sqlite3"
    expected_collection = local_dir / "1a90eda1-e932-4e73-89dd-edb1adf9d126" / "data.bin"

    assert expected_sqlite.exists()
    assert expected_collection.exists()
