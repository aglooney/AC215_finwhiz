"""Helpers for writing NDJSON payloads to local disk and optionally Google Cloud Storage."""
from __future__ import annotations

import json
import os
import logging
from pathlib import Path
from typing import Iterable, Optional

from google.cloud import storage

# Default configuration matching GCS storage module
DEFAULT_BUCKET = "finwhiz-storage"
DEFAULT_PROJECT_ID = "finwhiz-ac215"

LOGGER = logging.getLogger(__name__)


def write_ndjson_local(path: Path, records: Iterable[dict]) -> None:
    """Write records as newline-delimited JSON to local file.
    
    Args:
        path: Local file path to write to
        records: Iterable of dictionaries to write as NDJSON
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    LOGGER.info(f"Wrote {path}")


def write_ndjson_local_and_gcs(
    local_path: Path,
    records: Iterable[dict],
    *,
    bucket: Optional[str] = None,
    gcs_path: Optional[str] = None,
    project_id: Optional[str] = None,
) -> None:
    """Write records to local file first, then optionally upload to GCS.
    
    This is the recommended approach: always save locally, optionally upload.
    
    Args:
        local_path: Local file path to write to
        records: Iterable of dictionaries to write as NDJSON
        bucket: GCS bucket name (if None, only writes locally)
        gcs_path: Path within the bucket (required if bucket is provided)
        project_id: GCP project ID (default: 'finwhiz-ac215')
        
    Example:
        # Write locally only
        write_ndjson_local_and_gcs(Path("data/doc.ndjson"), records)
        
        # Write locally AND upload to GCS
        write_ndjson_local_and_gcs(
            Path("data/doc.ndjson"), 
            records,
            bucket="finwhiz-storage",
            gcs_path="base-knowledge/scraped-data/doc.ndjson"
        )
    """
    # Step 1: ALWAYS write to local disk first
    records_list = list(records)  # Materialize iterator
    write_ndjson_local(local_path, records_list)
    
    # Step 2: Optionally upload to GCS
    if bucket and gcs_path:
        LOGGER.info(f"Uploading to GCS: gs://{bucket}/{gcs_path}")
        upload_file_to_gcs(
            local_path=local_path,
            bucket=bucket,
            gcs_path=gcs_path,
            project_id=project_id,
        )
    else:
        LOGGER.debug("Skipping GCS upload (bucket/gcs_path not provided)")


def write_ndjson_gcs(
    bucket: str,
    path: str,
    records: Iterable[dict],
    *,
    project_id: Optional[str] = None,
) -> None:
    """Write records as newline-delimited JSON directly to GCS (no local file).
    
    Note: Consider using write_ndjson_local_and_gcs() instead for better reliability.
    
    Args:
        bucket: GCS bucket name
        path: Path within the bucket (e.g., 'base-knowledge/scraped-data/irs/doc.ndjson')
        records: Iterable of dictionaries to write as NDJSON
        project_id: GCP project ID (default: 'finwhiz-ac215', or from env GOOGLE_CLOUD_PROJECT)
    """
    # Use provided project_id, or get from env, or use default
    if project_id is None:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", DEFAULT_PROJECT_ID)
    
    client = storage.Client(project=project_id)
    blob = client.bucket(bucket).blob(path)
    data = "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
    blob.upload_from_string(data, content_type="application/x-ndjson")
    
    LOGGER.info(f"Uploaded to gs://{bucket}/{path}")


def upload_file_to_gcs(
    local_path: Path,
    bucket: str,
    gcs_path: str,
    *,
    project_id: Optional[str] = None,
) -> bool:
    """Upload a local file to Google Cloud Storage.
    
    Args:
        local_path: Path to local file
        bucket: GCS bucket name
        gcs_path: Destination path in bucket
        project_id: GCP project ID (default: 'finwhiz-ac215')
        
    Returns:
        True if successful, False otherwise
    """
    if project_id is None:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", DEFAULT_PROJECT_ID)
    
    try:
        client = storage.Client(project=project_id)
        blob = client.bucket(bucket).blob(gcs_path)
        blob.upload_from_filename(str(local_path))
        LOGGER.info(f"Uploaded {local_path} -> gs://{bucket}/{gcs_path}")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to upload {local_path}: {e}")
        return False


def get_gcs_client(
    bucket_name: str = DEFAULT_BUCKET,
    project_id: str = DEFAULT_PROJECT_ID,
) -> tuple[storage.Client, storage.Bucket]:
    """Get GCS client and bucket (matches GCSClient pattern).
    
    Args:
        bucket_name: GCS bucket name
        project_id: GCP project ID
        
    Returns:
        Tuple of (storage.Client, storage.Bucket)
    """
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    return client, bucket