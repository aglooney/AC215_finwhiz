from google.cloud import storage
import logging
import os
from chromadb.config import Settings

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logging.getLogger("sentence-transformers").setLevel(logging.WARNING)
load_dotenv()

BUCKET_NAME = os.getenv("GCS_BUCKET")   # set in .env
KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") # set in .env


client = storage.Client.from_service_account_json(KEY_PATH)
bucket = client.bucket(BUCKET_NAME)
all_blobs = list(bucket.list_blobs())
logging.info(f"Found {len(all_blobs)} blobs in bucket.")

for blob in bucket.list_blobs():
    print(blob.name)