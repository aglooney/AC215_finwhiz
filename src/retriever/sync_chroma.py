from google.cloud import storage
import os
from dotenv import load_dotenv
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def download_chroma_from_gcs(bucket_name, gcs_prefix, collection, local_path):
    # Authentication
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.environ.get("BUCKET_CREDENTIALS")
    client = storage.Client.from_service_account_json(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    bucket = client.bucket(bucket_name)

    os.makedirs(local_path, exist_ok=True)

    def download_blob(blob):
        rel_path = os.path.relpath(blob.name, gcs_prefix)
        dest_path = os.path.join(local_path, rel_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        blob.download_to_filename(dest_path)
        logger.info(f"Downloaded {blob.name} -> {dest_path}")

    # Download chroma.sqlite3
    for blob in bucket.list_blobs(prefix=gcs_prefix):
        if blob.name.endswith("chroma.sqlite3"):
            download_blob(blob)

    # Download all files in the collection folder
    for blob in bucket.list_blobs(prefix=f"{gcs_prefix}/{collection}"):
        download_blob(blob)
if __name__ == "__main__":
    load_dotenv()

    GCS_PREFIX = "chroma_storage_backup"
    GCS_BUCKET = os.environ.get("GCS_BUCKET")
    LOCAL_CHROMA_PATH = "/app/src/chroma_storage"
    COLLECTION = "1a90eda1-e932-4e73-89dd-edb1adf9d126"
    download_chroma_from_gcs(GCS_BUCKET, GCS_PREFIX, COLLECTION, LOCAL_CHROMA_PATH)