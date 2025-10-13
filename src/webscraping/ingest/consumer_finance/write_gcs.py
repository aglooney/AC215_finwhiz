"""Helpers for writing NDJSON payloads to Google Cloud Storage."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable

from google.cloud import storage

LOGGER = logging.getLogger(__name__)

# FinWhiz GCP Configuration
GCP_PROJECT_ID = "finwhiz-ac215"


def upload_file_to_gcs(local_path: Path, bucket: str, gcs_path: str) -> None:
    """
    Upload an existing local file to GCS.
    
    This is more efficient than write_ndjson_gcs() when the file already exists locally.
    
    Args:
        local_path: Path to local file
        bucket: GCS bucket name
        gcs_path: Destination path in bucket
    """
    client = storage.Client(project=GCP_PROJECT_ID)
    blob = client.bucket(bucket).blob(gcs_path)
    blob.upload_from_filename(str(local_path), content_type="application/x-ndjson")
    LOGGER.info(f"✓ Uploaded {local_path.name} to gs://{bucket}/{gcs_path}")


def write_ndjson_gcs(bucket: str, path: str, records: Iterable[dict]) -> None:
    """
    Write NDJSON records directly to GCS (without local file).
    
    Use this when you don't need a local copy. Otherwise, use upload_file_to_gcs().
    
    Args:
        bucket: GCS bucket name
        path: Destination path in bucket
        records: Iterable of dict records
    """
    client = storage.Client(project=GCP_PROJECT_ID)
    blob = client.bucket(bucket).blob(path)
    
    # Convert records to NDJSON format
    data = "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
    
    # Upload with correct content type
    blob.upload_from_string(data, content_type="application/x-ndjson")
    
    LOGGER.info(f"✓ Uploaded {len(data)} bytes to gs://{bucket}/{path}")