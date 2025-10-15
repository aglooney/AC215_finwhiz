from google.cloud import storage
import logging
import os
from chromadb.config import Settings

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logging.getLogger("sentence-transformers").setLevel(logging.WARNING)
load_dotenv()

BUCKET_NAME = os.environ.get("GCS_BUCKET") 

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.environ.get("BUCKET_CREDENTIALS")
KEY_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") 

client = storage.Client.from_service_account_json(KEY_PATH)
bucket = client.bucket(BUCKET_NAME)
all_blobs = list(bucket.list_blobs())
logging.info(f"Found {len(all_blobs)} blobs in bucket.")

for blob in bucket.list_blobs():
    print(blob.name)