import os
import logging
from google.cloud import storage

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def ensure_chroma_local(bucket_name: str, prefix: str, collection_dir: str, local_path: str):
    """Ensure Chroma data exists locally. Download from GCS if missing."""
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.environ.get("BUCKET_CREDENTIALS")

    if os.path.exists(local_path) and os.listdir(local_path):
        logger.info("Found existing Chroma directory locally.")
        return

    logger.info(f"Downloading Chroma database from GCS bucket={bucket_name}, prefix={prefix}")
    client = storage.Client.from_service_account_json(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    bucket = client.bucket(bucket_name)

    os.makedirs(local_path, exist_ok=True)

    def download_blob(blob):
        rel_path = os.path.relpath(blob.name, prefix)
        dest_path = os.path.join(local_path, rel_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        blob.download_to_filename(dest_path)
        logger.info(f"Downloaded {blob.name} → {dest_path}")

    # Download the sqlite3 file and collection subdirectory
    for blob in bucket.list_blobs(prefix=prefix):
        if blob.name.endswith("chroma.sqlite3") or blob.name.startswith(f"{prefix}/{collection_dir}"):
            download_blob(blob)
