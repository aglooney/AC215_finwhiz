from unittest.mock import MagicMock

import pytest

from src.gcp_storage import gcp_config
from src.gcp_storage.gcs_client import GCSClient
from src.gcp_storage.upload_all_scraped_data import find_scraped_data, list_available_sources


@pytest.fixture
def mock_storage_client(monkeypatch):
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_client.bucket.return_value = mock_bucket
    monkeypatch.setattr("src.gcp_storage.gcs_client.storage.Client", MagicMock(return_value=mock_client))
    return mock_client, mock_bucket


def test_verify_config_success(monkeypatch):
    monkeypatch.setattr(gcp_config, "GCP_PROJECT_ID", "proj")
    monkeypatch.setattr(gcp_config, "GCS_BUCKET_NAME", "bucket")
    assert gcp_config.verify_config() is True


def test_verify_config_missing(monkeypatch):
    monkeypatch.setattr(gcp_config, "GCS_BUCKET_NAME", "")
    with pytest.raises(ValueError):
        gcp_config.verify_config()


def test_find_scraped_data_prefers_src_path(tmp_path, monkeypatch):
    data_dir = tmp_path / "src" / "webscraping" / "data"
    data_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    assert find_scraped_data() == data_dir


def test_list_available_sources_filters_by_files(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    first = root / "irs"
    first.mkdir()
    (first / "doc.ndjson").write_text("{}")
    second = root / "consumer"
    second.mkdir()
    (second / "info.json.gz").write_text("content")
    empty = root / "empty"
    empty.mkdir()

    assert list_available_sources(root) == ["consumer", "irs"]


def test_upload_file_success(mock_storage_client):
    _, mock_bucket = mock_storage_client
    blob = MagicMock()
    mock_bucket.blob.return_value = blob
    client = GCSClient(bucket_name="bucket", project_id="proj")
    assert client.upload_file("local.txt", "remote/path.txt") is True
    blob.upload_from_filename.assert_called_once_with("local.txt")


def test_upload_folder_returns_zero_when_missing(mock_storage_client, tmp_path):
    client = GCSClient(bucket_name="bucket", project_id="proj")
    missing_path = tmp_path / "does-not-exist"
    assert client.upload_folder(str(missing_path), "prefix") == 0
