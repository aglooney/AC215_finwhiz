"""
Utilities for persisting user documents in Google Cloud Storage.
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Final
import logging

from google.cloud import storage
from google.api_core.exceptions import NotFound
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

BUCKET_NAME: Final[str] = os.environ.get("GCS_BUCKET")
KEY_PATH = os.getenv("BUCKET_CREDENTIALS")
LOCAL_FALLBACK_DIR = Path("local_user_uploads")


def _get_gcs_client():
    if not BUCKET_NAME or not KEY_PATH or not Path(KEY_PATH).exists():
        raise RuntimeError("GCS credentials or bucket not configured properly")
    return storage.Client.from_service_account_json(KEY_PATH)

def _load_session_metadata(bucket, session_id:str) -> list:
    """Load metadata.json for a session from GCS if it exists, else return empty list."""
    metadata_blob = bucket.blob(f"user_uploads/{session_id}/metadata.json")
    try:
        data = metadata_blob.download_as_text()
        return json.loads(data)
    except NotFound:
        logging.info(f"No existing metadata.json found for session {session_id}, creating new file")
        return []
    except Exception as e:
        logging.warning(f"Failed to load metadata.json for {session_id}: {e}")

def _save_session_metadata(bucket, session_id: str, metadata_list: list):
    """Upload the updated metadata list as JSON to GCS"""
    metadata_blob = bucket.blob(f"user_uploads/{session_id}/metadata.json")
    metadata_blob.upload_from_string(
        json.dumps(metadata_list, indent=2),
        content_type='application/json'
    )
    logging.info(f"Updated metadata.json for session: {session_id}")

def save_document_bytes(
    session_id: str,
    filename: str,
    contents: bytes,
    content_type: Optional[str] = None,
) -> str:
    """
    Store the uploaded file in GCS and return the URI.

    If bucket configuration is missing or the upload fails (e.g., during local
    dev without credentials), fall back to writing the file to disk so the
    rest of the flow can continue.
    """
    if not filename:
        filename="document.pdf"
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    object_name = f"sessions/{session_id}/{timestamp}_{filename}"

    try:
        client=_get_gcs_client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(object_name)

        blob.upload_from_string(contents, content_type=content_type)
        gcs_uri=f"gs://{BUCKET_NAME}/{object_name}"
        logging.info(f"Uploaded {filename} to {gcs_uri}")

        metadata = _load_session_metadata(bucket, session_id)
        metadata.append({
            "filename": filename,
            "gcs_path": gcs_uri,
            "timestamp": timestamp,
            "content_type": content_type or "application/octet-stream",
            "size_bytes": len(contents),
        })

        _save_session_metadata(bucket, session_id, metadata)

        return gcs_uri
    except Exception as e:
        logging.error(f"GCS upload failed: {e}. Falling back to local storage.")

        LOCAL_FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
        local_path = LOCAL_FALLBACK_DIR / object_name.replace("/", "_")
        local_path.write_bytes(contents)
        logging.info(f"Stored Locally at {local_path}")
        return local_path.as_posix()
