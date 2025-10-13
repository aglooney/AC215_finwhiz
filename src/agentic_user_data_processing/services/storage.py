"""
Utilities for persisting user documents in Google Cloud Storage.
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Final

from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

USER_UPLOAD_BUCKET: Final[str] = os.environ.get("USER_UPLOAD_BUCKET")
LOCAL_FALLBACK_DIR = Path("local_uploads")


def save_document_bytes(
    session_id: str,
    filename: str,
    contents: bytes,
    content_type: str | None = None,
) -> str:
    """
    Store the uploaded file in GCS and return the URI.

    If bucket configuration is missing or the upload fails (e.g., during local
    dev without credentials), fall back to writing the file to disk so the
    rest of the flow can continue.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    safe_name = filename or "document.pdf"
    object_name = f"sessions/{session_id}/{timestamp}_{safe_name}"

    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    if USER_UPLOAD_BUCKET and cred_path and Path(cred_path).exists():
        try:
            client = storage.Client()
            bucket = client.bucket(USER_UPLOAD_BUCKET)
            blob = bucket.blob(object_name)
            blob.upload_from_string(contents, content_type=content_type)
            return f"gs://{USER_UPLOAD_BUCKET}/{object_name}"
        except Exception:
            pass  # fall back to local storage

    LOCAL_FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
    fallback_path = LOCAL_FALLBACK_DIR / object_name.replace("/", "_")
    fallback_path.write_bytes(contents)
    return fallback_path.as_posix()
