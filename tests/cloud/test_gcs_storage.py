import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from google.cloud import storage

from agentic_user_data_processing.services import storage as storage_service

BUCKET = os.environ.get("GCS_BUCKET")
CRED_PATH = os.environ.get("BUCKET_CREDENTIALS")
REQUIRES_GCS = pytest.mark.skipif(
    not BUCKET or not CRED_PATH or not Path(CRED_PATH).exists(),
    reason="GCS bucket or credentials not configured",
)


def _client():
    return storage.Client.from_service_account_json(CRED_PATH)


@REQUIRES_GCS
def test_save_document_bytes_uploads_and_writes_metadata():
    pdf_path = Path(__file__).resolve().parents[2] / "src" / "synthetic_data" / "w2" / "outputs" / "w2_000.pdf"
    pdf_bytes = pdf_path.read_bytes()
    session_id = f"cloud-test-{uuid4()}"

    gcs_uri = storage_service.save_document_bytes(
        session_id=session_id,
        filename=pdf_path.name,
        contents=pdf_bytes,
        content_type="application/pdf",
    )

    assert gcs_uri.startswith(f"gs://{BUCKET}/sessions/{session_id}")

    client = _client()
    bucket = client.bucket(BUCKET)

    object_path = gcs_uri.replace(f"gs://{BUCKET}/", "")
    blob = bucket.blob(object_path)
    metadata_blob = bucket.blob(f"user_uploads/{session_id}/metadata.json")

    try:
        assert blob.exists(client), f"Uploaded blob missing: {object_path}"

        metadata_text = metadata_blob.download_as_text()
        entries = json.loads(metadata_text)
        assert any(entry["filename"] == pdf_path.name for entry in entries)
    finally:
        blob.delete(if_exists=True)
        metadata_blob.delete(if_exists=True)
