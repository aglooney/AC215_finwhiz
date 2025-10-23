import os
import json
import gzip
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

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
SCRAPED_PREFIX = os.environ.get("GCS_SCRAPED_PREFIX", "base-knowledge/scraped-data")
FRED_PREFIX = os.environ.get("GCS_FRED_PREFIX", f"{SCRAPED_PREFIX.rstrip('/')}/fred")
FRED_SOURCE_BASE = os.environ.get("FRED_SOURCE_BASE_URL", "https://fred.stlouisfed.org/series")
FRED_LOOKBACK_MONTHS = int(os.environ.get("FRED_LOOKBACK_MONTHS", "12"))

if not BUCKET_NAME or not KEY_PATH:
    raise ValueError("GCS_BUCKET and BUCKET_CREDENTIALS must be set in .env")

# Chroma in-memory client
chroma_client = chromadb.Client(Settings(persist_directory=CHROMA_PATH))

collection = chroma_client.get_or_create_collection(COLLECTION_NAME)

# Load embedding model
logging.info("Loading SentenceTransformer embedding model")
embedder = SentenceTransformer("jinaai/jina-embeddings-v3", trust_remote_code=True)
BATCH_SIZE = 64  # batch size for embedding

# Utility functions
def chunk_text(text, max_chars=500):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def clean_metadata(meta: dict) -> dict:
    cleaned = {
        "title": meta.get("title") or "N/A",
        "source_url": meta.get("source_url") or "N/A",
        "doctype": meta.get("doctype") or "N/A",
        "authority": meta.get("authority") or "N/A",
        "year": meta.get("year") if meta.get("year") is not None else -1,
    }
    for key in ("indicator", "observation_date", "value", "units", "category", "trend", "lookback_months"):
        if key in meta and meta[key] is not None:
            cleaned[key] = meta[key]
    return cleaned

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


def sanitize_id(blob_name: str) -> str:
    return blob_name.replace("/", "_").replace(" ", "_")


def detect_indicator(blob_name: str) -> str:
    path_parts = Path(blob_name).parts
    indicator = Path(blob_name).stem
    if "fred" in path_parts:
        try:
            idx = path_parts.index("fred")
            if idx + 1 < len(path_parts):
                indicator = path_parts[idx + 1]
        except ValueError:
            pass
    return indicator.upper()


def detect_units(text: str) -> str | None:
    lowered = text.lower()
    if "%" in text or "percent" in lowered:
        return "percent"
    if "basis point" in lowered:
        return "basis_points"
    if "index" in lowered:
        return "index"
    if "rate" in lowered:
        return "rate"
    return None


def parse_numeric(text: str) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def parse_observation_date(blob_name: str, text: str) -> str | None:
    # Try from filename first
    stem = Path(blob_name).stem
    for candidate in (stem, text):
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", candidate)
        if date_match:
            return date_match.group(0)
    return None


def categorize_indicator(indicator: str) -> str | None:
    indicator_upper = indicator.upper()
    mapping = {
        "CPI": "inflation",
        "PCE": "inflation",
        "CORECPI": "inflation",
        "CPILFESL": "inflation",
        "UNRATE": "labor_market",
        "PAYEMS": "labor_market",
        "JOLTS": "labor_market",
        "FEDFUNDS": "interest_rates",
        "EFFR": "interest_rates",
        "T10Y2Y": "yield_curve",
        "GDP": "growth",
        "GDPC1": "growth",
        "INDPRO": "production",
        "M2SL": "money_supply",
        "RECPROUSM156N": "recession_risk",
        "SP500": "equities",
        "VIXCLS": "volatility",
    }
    return mapping.get(indicator_upper)


def parse_fred_metadata(blob_name: str, raw_text: str) -> tuple[str, dict]:
    indicator = detect_indicator(blob_name)
    observation_date = parse_observation_date(blob_name, raw_text)
    value = parse_numeric(raw_text)
    units = detect_units(raw_text)

    metadata = {
        "title": f"{indicator} on {observation_date}" if observation_date else indicator,
        "source_url": f"{FRED_SOURCE_BASE}/{indicator}",
        "doctype": "fred_indicator",
        "authority": "FRED",
        "indicator": indicator,
        "observation_date": observation_date,
        "value": value,
        "units": units,
        "category": categorize_indicator(indicator),
    }
    return indicator, metadata


def build_fred_narrative(indicator: str, metadata: dict, raw_text: str) -> str:
    parts = []
    if metadata.get("observation_date"):
        parts.append(f"{indicator} reading on {metadata['observation_date']}")
    else:
        parts.append(f"{indicator} latest reading")

    if metadata.get("value") is not None:
        units = metadata.get("units") or ""
        value_str = f"{metadata['value']:.2f}"
        if metadata.get("units") == "percent":
            value_str = f"{value_str}%"
        parts.append(f"is {value_str}{'' if units in ('percent', '') else f' {units}'}")
    else:
        parts.append(f"is reported as: {raw_text.strip()}")

    if metadata.get("category"):
        category_hint = metadata["category"].replace("_", " ")
        parts.append(f"(category: {category_hint})")

    return " ".join(parts) + f". Raw statement: {raw_text.strip()}"


def fred_blob_to_record(bucket, blob):
    text = blob.download_as_text().strip()
    if not text:
        return None, None
    indicator, metadata = parse_fred_metadata(blob.name, text)
    record = {
        "id": sanitize_id(blob.name),
        "text": build_fred_narrative(indicator, metadata, text),
        **metadata,
    }
    return indicator, record


def summarize_indicator_history(indicator: str, entries: list[dict], lookback_months: int) -> dict | None:
    dated_entries = []
    for entry in entries:
        date_str = entry.get("observation_date")
        value = entry.get("value")
        if not date_str or value is None:
            continue
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        dated_entries.append(
            {
                "date": date_obj,
                "value": value,
                "units": entry.get("units"),
                "category": entry.get("category"),
                "source_url": entry.get("source_url"),
            }
        )

    if not dated_entries:
        return None

    dated_entries.sort(key=lambda x: x["date"], reverse=True)
    latest = dated_entries[0]
    narrative_parts = [
        f"{indicator} latest observation on {latest['date'].date()} is {latest['value']:.2f}"
        + ("%" if latest.get("units") == "percent" else f" {latest.get('units')}" if latest.get("units") else "")
        + "."
    ]

    trend = "stable"
    lookback_target = None
    if len(dated_entries) > 1:
        prev = dated_entries[1]
        delta = latest["value"] - prev["value"]
        if abs(delta) > 1e-6:
            direction = "rose" if delta > 0 else "fell"
            pct_change = (abs(delta) / abs(prev["value"])) * 100 if prev["value"] else None
            change_clause = f"{direction} by {abs(delta):.2f}"
            if pct_change is not None:
                change_clause += f" ({pct_change:.2f}%)"
            change_clause += f" since {prev['date'].date()}."
            narrative_parts.append(change_clause)
            trend = "increasing" if delta > 0 else "decreasing"
        else:
            narrative_parts.append(f"Unchanged relative to {prev['date'].date()}.")

    if len(dated_entries) > 2:
        for entry in dated_entries[1:]:
            months_diff = (latest["date"].year - entry["date"].year) * 12 + (latest["date"].month - entry["date"].month)
            if months_diff >= lookback_months:
                lookback_target = entry
                break
        if lookback_target:
            delta = latest["value"] - lookback_target["value"]
            if abs(delta) > 1e-6:
                direction = "higher" if delta > 0 else "lower"
                pct_change = (abs(delta) / abs(lookback_target["value"])) * 100 if lookback_target["value"] else None
                clause = f"Compared with {lookback_months}-month lookback ({lookback_target['date'].date()}), value is {direction} by {abs(delta):.2f}"
                if pct_change is not None:
                    clause += f" ({pct_change:.2f}%)."
                else:
                    clause += "."
                narrative_parts.append(clause)
                if trend == "stable":
                    trend = "increasing" if delta > 0 else "decreasing"

    if trend == "stable":
        narrative_parts.append("Overall trend appears stable over recent observations.")

    category = dated_entries[0].get("category")
    if category:
        narrative_parts.append(f"Indicator category: {category.replace('_', ' ')} – consider its implications when assessing market timing.")

    summary_text = " ".join(narrative_parts)
    metadata = {
        "title": f"{indicator} trend summary",
        "source_url": dated_entries[0].get("source_url"),
        "doctype": "fred_summary",
        "authority": "FRED",
        "indicator": indicator,
        "trend": trend,
        "lookback_months": lookback_months,
        "category": category,
        "observation_date": latest["date"].strftime("%Y-%m-%d"),
        "value": latest["value"],
        "units": latest.get("units"),
    }
    return {
        "id": f"{indicator}_summary",
        "text": summary_text,
        **metadata,
    }

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
    all_blobs = list(bucket.list_blobs(prefix=SCRAPED_PREFIX))
    logging.info(f"Found {len(all_blobs)} blobs in bucket.")

    total_ingested = 0
    fred_entries: defaultdict[str, list[dict]] = defaultdict(list)
    for blob in tqdm(all_blobs):
        if blob.name.startswith(FRED_PREFIX) and blob.name.endswith(".txt"):
            indicator, record = fred_blob_to_record(bucket, blob)
            if record:
                total_ingested += store_records([record], collection)
                if indicator:
                    fred_entries[indicator].append(record)
            continue

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

    for indicator, entries in fred_entries.items():
        summary = summarize_indicator_history(indicator, entries, FRED_LOOKBACK_MONTHS)
        if summary:
            total_ingested += store_records([summary], collection)

    logging.info(f"Finished ingesting {total_ingested} records into ChromaDB collection '{COLLECTION_NAME}'")
    return collection  # return in-memory collection

# Example usage
if __name__ == "__main__":
    ingest_from_gcs()
    logging.info("Finished Making Database")

    logging.info("Pushing Database to GCS")

    upload_chroma_to_gcs(local_dir=CHROMA_PATH, bucket_name=BUCKET_NAME, dest_prefix="chroma_storage_backup")

    logging.info("GCS Upload Complete")
