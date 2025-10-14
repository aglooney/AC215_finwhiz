from __future__ import annotations
import argparse
from pathlib import Path
from google.cloud import storage

def upload_to_gcs(local_dir: str, bucket: str, prefix: str):
    client = storage.Client()
    local_path = Path(local_dir)
    for file in local_path.glob("*.jsonl.gz"):
        blob_name = f"{prefix}/{file.name}"
        blob = client.bucket(bucket).blob(blob_name)
        blob.upload_from_filename(file)
        print(f"Uploaded {file} → gs://{bucket}/{blob_name}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", required=True, help="Local dir of JSONL exports")
    parser.add_argument("--bucket", required=True, help="Target GCS bucket")
    parser.add_argument("--prefix", required=True, help="GCS prefix (like finra/exports/jsonl)")
    args = parser.parse_args()
    upload_to_gcs(args.local, args.bucket, args.prefix)

if __name__ == "__main__":
    main()