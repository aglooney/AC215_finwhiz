import os
from pathlib import Path

import pytest

from gcp_storage import gcs_client
from gcp_storage import gcp_config


class DummyBlob:
    def __init__(self):
        self.uploaded = []
        self.downloads = []
        self.deleted = False
        self.exists_flag = True

    def upload_from_filename(self, filename):
        self.uploaded.append(filename)

    def download_to_filename(self, filename):
        self.downloads.append(filename)

    def upload_from_string(self, *_args, **_kwargs):
        self.uploaded.append("string")

    def delete(self):
        if self.deleted is False:
            self.deleted = True
        else:
            raise RuntimeError("already deleted")

    def exists(self):
        return self.exists_flag


class DummyBucket:
    def __init__(self):
        self.blobs = {}

    def blob(self, name):
        return self.blobs.setdefault(name, DummyBlob())

    def list_blobs(self, prefix=""):
        for name, blob in self.blobs.items():
            if name.startswith(prefix):
                dummy = type("Blob", (), {"name": name})
                yield dummy


class DummyStorageClient:
    def __init__(self):
        self.bucket_obj = DummyBucket()

    def bucket(self, _name):
        return self.bucket_obj


@pytest.fixture(autouse=True)
def patch_storage(monkeypatch):
    dummy_client = DummyStorageClient()
    monkeypatch.setattr(gcs_client.storage, "Client", lambda *args, **kwargs: dummy_client)
    return dummy_client


def test_upload_file_success(tmp_path):
    local = tmp_path / "file.txt"
    local.write_text("data")
    client = gcs_client.GCSClient(bucket_name="bucket", project_id="proj")
    assert client.upload_file(str(local), "prefix/file.txt")
    blob = client.bucket.blobs["prefix/file.txt"]
    assert blob.uploaded == [str(local)]


def test_upload_file_failure(monkeypatch, tmp_path):
    local = tmp_path / "file.txt"
    local.write_text("data")
    client = gcs_client.GCSClient()

    class FailingBlob(DummyBlob):
        def upload_from_filename(self, filename):
            raise RuntimeError("boom")

    client.bucket.blobs["fail"] = FailingBlob()
    monkeypatch.setattr(client.bucket, "blob", lambda name: client.bucket.blobs[name])
    assert not client.upload_file(str(local), "fail")


def test_upload_folder_counts_files(tmp_path):
    (tmp_path / "a").write_text("1")
    subdir = tmp_path / "nested"
    subdir.mkdir()
    (subdir / "b").write_text("2")
    client = gcs_client.GCSClient()
    count = client.upload_folder(str(tmp_path), "dest")
    assert count == 2


def test_download_file_success(tmp_path):
    client = gcs_client.GCSClient()
    download_to = tmp_path / "out.txt"
    assert client.download_file("missing", str(download_to)) is True
    blob = client.bucket.blobs["missing"]
    assert blob.downloads == [str(download_to)]


def test_download_file_failure(monkeypatch):
    client = gcs_client.GCSClient()

    class FailingBlob(DummyBlob):
        def download_to_filename(self, *_):
            raise RuntimeError("fail")

    client.bucket.blobs["bad"] = FailingBlob()
    monkeypatch.setattr(client.bucket, "blob", lambda name: client.bucket.blobs[name])
    assert not client.download_file("bad", "/tmp/out")


def test_list_files_returns_names():
    client = gcs_client.GCSClient()
    client.bucket.blobs["prefix/a"] = DummyBlob()
    client.bucket.blobs["prefix/b"] = DummyBlob()
    files = client.list_files(prefix="prefix/")
    assert set(files) == {"prefix/a", "prefix/b"}


def test_file_exists_checks_blob():
    client = gcs_client.GCSClient()
    blob = client.bucket.blobs["doc"] = DummyBlob()
    blob.exists_flag = False
    assert not client.file_exists("doc")
    blob.exists_flag = True
    assert client.file_exists("doc")


def test_delete_file_handles_exception(monkeypatch):
    client = gcs_client.GCSClient()

    class FailingBlob(DummyBlob):
        def delete(self):
            raise RuntimeError("err")

    client.bucket.blobs["x"] = FailingBlob()
    monkeypatch.setattr(client.bucket, "blob", lambda name: client.bucket.blobs[name])
    assert not client.delete_file("x")


def test_delete_file_success():
    client = gcs_client.GCSClient()
    assert client.delete_file("missing")
    assert client.bucket.blobs["missing"].deleted


def test_gcp_config_verify(monkeypatch):
    monkeypatch.setenv("GCP_PROJECT_ID", "proj")
    monkeypatch.setenv("GCS_BUCKET_NAME", "bucket")
    import importlib

    importlib.reload(gcp_config)
    assert gcp_config.verify_config()
