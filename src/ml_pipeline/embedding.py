import os
import json
from google.cloud import storage
from sentence_transformers import SentenceTransformer
import chromadb
import logging
from dotenv import load_dotenv
import gzip

logging.basicConfig(level=logging.INFO)
logging.getLogger("sentence-transformers").setLevel(logging.WARNING)
load_dotenv()

#config
BUCKET_NAME = os.getenv("GCS_BUCKET")   # set in .env
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.environ.get("BUCKET_CREDENTIALS")# set in .env
CHROMA_PATH = "/app/src/chroma_storage"
COLLECTION_NAME = "finwhiz_docs"
BATCH_SIZE = 64   # number of docs per embedding batch

# load jina embedding model locally
logging.info("Downloading Embedding Model from HuggingFace")
model = SentenceTransformer("jinaai/jina-embeddings-v3", trust_remote_code=True)

def embed_texts(texts):
    return model.encode(texts, batch_size=32, task="retrieval.passage", convert_to_numpy=True).tolist()

# stream ndjson files from GCS blob line-by-line
def stream_ndjson_from_blob(bucket, blob_name):
    blob = bucket.blob(blob_name)
    with blob.open("r") as f:  
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

#stream .gz files from GC blob line-by-line
def stream_jsonl_gz_from_blob(bucket, blob_name):
    blob = bucket.blob(blob_name)
    with blob.open("rb") as f:
        with gzip.open(f, 'rt', encoding='utf-8') as gz:
            for line in gz:
                line = line.strip()
                if line:
                    yield json.loads(line)


# Cleanup Metadata
def clean_metadata(meta: dict) -> dict:
    return {
        "title": meta.get("title") or "N/A",
        "source_url": meta.get("source_url") or "N/A",
        "doctype": meta.get("doctype") or "N/A",
        "authority": meta.get("authority") or "N/A",
        "year": meta.get("year") if meta.get("year") is not None else -1,
    }

#Split long text into chunks of ~max_chars.
def chunk_text(text, max_chars=500):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

# store batch in ChromaDB
def store_records(records, collection):
    if not records:
        return 0

    texts, ids, metadatas = [], [], []

    for rec in records:
        if not rec.get("text"):
            continue
        chunks = chunk_text(rec["text"], max_chars=500)
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
    
    return None
            


if __name__ == "__main__":
    if not BUCKET_NAME:
        raise ValueError("GCS_BUCKET environment variable not set!")

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

        # flush leftover batch
        if batch:
            total_ingested += store_records(batch, collection)
        

    logging.info(
        f"Finished ingesting {total_ingested} records into ChromaDB collection '{COLLECTION_NAME}'"
    )
    
    logging.info("Uploading ChromaDB to GCS")
    upload_chroma_to_gcs(CHROMA_PATH, BUCKET_NAME, "chroma_storage_backup")
    logging.info("Upload Complete.")

