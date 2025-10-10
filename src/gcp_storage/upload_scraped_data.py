"""
Upload scraped NDJSON data to GCS

This script demonstrates the correct way to upload scraped data
from the webscraping pipeline to Google Cloud Storage.

Usage:
    python upload_scraped_data.py

Requirements:
    - Scraped data exists in data/consumer_finance/
    - GCS bucket 'finwhiz-storage' exists
    - Authenticated with GCP (gcloud auth application-default login)
"""

import sys
from pathlib import Path

from gcs_client import GCSClient


def find_scraped_data():
    """
    Find the scraped data directory
    Checks common locations relative to script
    """
    # Possible locations
    possible_paths = [
        Path("data/consumer_finance"),              # From repo root
        Path("../../data/consumer_finance"),        # From src/storage/
        Path("../data/consumer_finance"),           # From src/
    ]
    
    for path in possible_paths:
        if path.exists():
            return path.resolve()
    
    return None


def upload_scraped_data():
    """Upload all scraped data from data/consumer_finance/ to GCS"""
    
    print("=" * 60)
    print("FinWhiz Data Upload Script")
    print("=" * 60)
    print()
    
    # Initialize client
    print("Initializing GCS client...")
    client = GCSClient(bucket_name="finwhiz-storage", project_id="finwhiz-ac215")
    print(f"Connected to: gs://{client.bucket_name}")
    print()
    
    # Find scraped data
    print("Looking for scraped data...")
    scraped_data_path = find_scraped_data()
    
    if not scraped_data_path:
        print("ERROR: Scraped data not found!")
        print("Expected location: data/consumer_finance/")
        print(f"Current directory: {Path.cwd()}")
        print()
        print("Make sure you:")
        print("1. Run this from the repo root, OR")
        print("2. Have scraped data in data/consumer_finance/")
        sys.exit(1)
    
    print(f"Found scraped data at: {scraped_data_path}")
    
    # Check what's in the folder
    ndjson_files = list(scraped_data_path.rglob('*.ndjson'))
    if not ndjson_files:
        print("WARNING: No .ndjson files found in scraped data folder")
        print("Did you run the scraper yet?")
        sys.exit(1)
    
    print(f"Found {len(ndjson_files)} .ndjson file(s) to upload")
    print()
    
    # Upload the folder
    print("Starting upload...")
    print(f"Destination: gs://{client.bucket_name}/base-knowledge/scraped-data/consumer-finance/")
    print()
    
    count = client.upload_folder(
        local_folder=str(scraped_data_path),
        gcs_prefix="base-knowledge/scraped-data/consumer-finance"
    )
    
    print()
    print("=" * 60)
    print(f"Upload complete: {count} files uploaded")
    print("=" * 60)
    print()
    
    # Verify upload
    print("Verifying upload...")
    files = client.list_files(prefix="base-knowledge/scraped-data/")
    print(f"Total files in GCS: {len(files)}")
    print()
    
    if files:
        print("Sample files uploaded:")
        for file in files[:10]:
            print(f"  - {file}")
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more")
    
    print()
    print("SUCCESS: Data uploaded to GCS")
    print(f"View in console: https://console.cloud.google.com/storage/browser/{client.bucket_name}/base-knowledge/scraped-data")


if __name__ == "__main__":
    upload_scraped_data()