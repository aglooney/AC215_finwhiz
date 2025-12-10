import os
from unittest.mock import patch, MagicMock

os.environ.setdefault("FINWHIZ_TEST_MODE", "1")


def test_ensure_chroma_local_existing_dir(tmp_path):
    from llm import chroma_utils

    # Create a non-empty directory
    test_dir = tmp_path / "chroma"
    test_dir.mkdir()
    (test_dir / "test.db").write_text("test")

    # Should return early without downloading
    with patch.object(chroma_utils.storage, "Client") as mock_client:
        chroma_utils.ensure_chroma_local("bucket", "prefix", "collection", str(test_dir))
        mock_client.assert_not_called()


def test_ensure_chroma_local_downloads(tmp_path):
    from llm import chroma_utils

    test_dir = tmp_path / "chroma"

    mock_blob = MagicMock()
    mock_blob.name = "prefix/chroma.sqlite3"
    mock_blob.download_to_filename = MagicMock()

    mock_bucket = MagicMock()
    mock_bucket.list_blobs.return_value = [mock_blob]

    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket

    with patch.object(chroma_utils.storage.Client, "from_service_account_json", return_value=mock_client):
        with patch.dict(os.environ, {"BUCKET_CREDENTIALS": "/tmp/creds.json"}):
            chroma_utils.ensure_chroma_local("bucket", "prefix", "collection", str(test_dir))
