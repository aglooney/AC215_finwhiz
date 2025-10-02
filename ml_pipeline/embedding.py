import os
import json
from google.cloud import storage
from sentence_transformers import SentenceTransformer
import chromadb
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logging.getLogger("sentence-transformers").setLevel(logging.WARNING)
load_dotenv()

# ---------------------------
# CONFIG
# ---------------------------
BUCKET_NAME = os.getenv("GCS_BUCKET")   # set in .env
KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") #set in .env
CHROMA_PATH = "/home/app/chroma_storage"
COLLECTION_NAME = "finwhiz_docs"

#load jina embedding model locally
model = SentenceTransformer("jinaai/jina-embeddings-v3", trust_remote_code=True)
logging.info("Downloading Embedding Model from HuggingFace")
def embed_texts(texts):
    return model.encode(texts, batch_size=32, convert_to_numpy=True).tolist()

#load json from GCS blob
def load_ndjson_from_blob(bucket, blob_name):
    blob = bucket.blob(blob_name)
    content = blob.download_as_text(encoding="utf-8")
    for line in content.strip().split("\n"):
        if line:
            yield json.loads(line)

#Cleanup Metadata
def clean_metadata(meta: dict) -> dict:
    return {
        "title": meta.get("title") or "N/A",
        "source_url": meta.get("source_url") or "N/A",
        "doctype": meta.get("doctype") or "N/A",
        "authority": meta.get("authority") or "N/A",
        "year": meta.get("year") if meta.get("year") is not None else -1,
    }

#store in ChromaDB
def store_records(records, collection):
    if not records:
        return 0

    texts = [rec["text"] for rec in records]
    ids = [rec["id"] for rec in records]

    metadatas = [
        clean_metadata({
            "title": rec.get("title"),
            "source_url": rec.get("source_url"),
            "doctype": rec.get("doctype"),
            "year": rec.get("year"),
            "authority": rec.get("authority"),
        })
        for rec in records
    ]

    embeddings = embed_texts(texts)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )
    return len(records)


if __name__ == "__main__":
    if not BUCKET_NAME:
        raise ValueError("GCS_BUCKET env var not set!")

    logging.info(f"Connecting to GCS bucket: {BUCKET_NAME}")
    client = storage.Client.from_service_account_json(KEY_PATH)
    bucket = client.bucket(BUCKET_NAME)
    all_blobs = list(bucket.list_blobs())
    logging.info(f"Found {len(all_blobs)} blobs in bucket.")

    # ChromaDB setup
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(COLLECTION_NAME)

    total_ingested = 0
    for blob in all_blobs:
        logging.info(f"Processing blob: {blob.name}")
        records = list(load_ndjson_from_blob(bucket, blob.name))
        ingested_count = store_records(records, collection)
        total_ingested += ingested_count

    logging.info(f"Finished ingesting {total_ingested} records into ChromaDB collection '{COLLECTION_NAME}'")
