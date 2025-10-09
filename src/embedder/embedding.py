import os
import json
import gzip
import logging
from tqdm import tqdm
from google.cloud import storage
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logging.getLogger("sentence-transformers").setLevel(logging.WARNING)

# Load environment variables
BUCKET_NAME = os.environ.get("GCS_BUCKET")
KEY_PATH = os.environ.get("BUCKET_CREDENTIALS")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH
CHROMA_PATH = "/app/src/chroma_storage"
COLLECTION_NAME = "finwhiz_docs"

if not BUCKET_NAME or not KEY_PATH:
    raise ValueError("GCS_BUCKET and BUCKET_CREDENTIALS must be set in .env")

# Chroma in-memory client
chroma_client = chromadb.Client(Settings(persist_directory=CHROMA_PATH))

collection = chroma_client.get_or_create_collection(COLLECTION_NAME)

# Load embedding model
logging.info("Loading SentenceTransformer embedding model...")
embedder = SentenceTransformer("jinaai/jina-embeddings-v3", trust_remote_code=True)
BATCH_SIZE = 64  # batch size for embedding

# Utility functions
def chunk_text(text, max_chars=500):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def clean_metadata(meta: dict) -> dict:
    return {
        "title": meta.get("title") or "N/A",
        "source_url": meta.get("source_url") or "N/A",
        "doctype": meta.get("doctype") or "N/A",
        "authority": meta.get("authority") or "N/A",
        "year": meta.get("year") if meta.get("year") is not None else -1,
    }

def embed_texts(texts):
    return embedder.encode(texts, batch_size=32, task="retrieval.passage", convert_to_numpy=True).tolist()

def store_records(records, collection):
    if not records:
        return 0

    texts, ids, metadatas = [], [], []

    for rec in records:
        if not rec.get("text"):
            continue
        chunks = chunk_text(rec["text"])
        for i, chunk in enumerate(chunks):
            texts.append(chunk)
            ids.append(f"{rec['id']}_chunk{i}")
            metadatas.append(clean_metadata(rec))

    if not texts:
        return 0

    embeddings = embed_texts(texts)
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )
    return len(records)

# Stream functions for GCS blobs
def stream_ndjson_from_blob(bucket, blob_name):
    blob = bucket.blob(blob_name)
    with blob.open("r") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def stream_jsonl_gz_from_blob(bucket, blob_name):
    blob = bucket.blob(blob_name)
    with blob.open("rb") as f:
        with gzip.open(f, 'rt', encoding='utf-8') as gz:
            for line in gz:
                line = line.strip()
                if line:
                    yield json.loads(line)

# Upload ChromaDB to GCS (optional, if you want persistence)
def upload_chroma_to_gcs(local_dir, bucket_name, dest_prefix):
    client = storage.Client.from_service_account_json(KEY_PATH)
    bucket = client.bucket(bucket_name)
    for root, _, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            rel_path = os.path.relpath(local_path, local_dir)
            blob_path = f"{dest_prefix}/{rel_path}"
            blob = bucket.blob(blob_path)
            blob.upload_from_filename(local_path)
            logging.info(f"Uploaded {local_path} to gs://{bucket_name}/{blob_path}")

# Main ingestion function
def ingest_from_gcs():
    logging.info(f"Connecting to GCS bucket: {BUCKET_NAME}")
    client = storage.Client.from_service_account_json(KEY_PATH)
    bucket = client.bucket(BUCKET_NAME)
    all_blobs = list(bucket.list_blobs())
    logging.info(f"Found {len(all_blobs)} blobs in bucket.")

    total_ingested = 0
    for blob in tqdm(all_blobs):
        if blob.name.endswith(".ndjson"):
            stream_func = stream_ndjson_from_blob
        elif blob.name.endswith(".jsonl.gz"):
            stream_func = stream_jsonl_gz_from_blob
        else:
            continue

        logging.info(f"Processing blob: {blob.name}")
        batch = []
        for record in stream_func(bucket, blob.name):
            batch.append(record)
            if len(batch) >= BATCH_SIZE:
                total_ingested += store_records(batch, collection)
                batch.clear()

        if batch:
            total_ingested += store_records(batch, collection)

    logging.info(f"Finished ingesting {total_ingested} records into ChromaDB collection '{COLLECTION_NAME}'")
    return collection  # return in-memory collection

# Example usage
if __name__ == "__main__":
    ingest_from_gcs()
    logging.info("Upload Complete")
