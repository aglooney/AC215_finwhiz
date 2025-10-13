"""
Upload selected scraped NDJSON data to GCS

Usage:
    # Upload all
    python upload_all_scraped_data.py
    
    # Upload specific sources
    python upload_all_scraped_data.py --sources irs consumer_finance
    
    # List available sources
    python upload_all_scraped_data.py --list
"""

import sys
import argparse
from pathlib import Path

from gcs_client import GCSClient


def find_scraped_data():
    """Find the scraped data directory."""
    possible_paths = [
        Path("src/webscraping/data"),
        Path("webscraping/data"),
        Path("data"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path.resolve()
    
    return None


def list_available_sources(data_root: Path):
    """List all available source folders"""
    if not data_root or not data_root.exists():
        print("ERROR: Data directory not found")
        return []
    
    sources = []
    for folder in data_root.iterdir():
        if folder.is_dir():
            # Check if it has .ndjson or .json.gz files
            ndjson_files = list(folder.glob('*.ndjson'))
            json_gz_files = list(folder.glob('*.json.gz'))
            if ndjson_files or json_gz_files:
                sources.append(folder.name)
    
    return sorted(sources)


def upload_all_scraped_data(selected_sources=None):
    """Upload all or selected scraped data from sources to GCS"""
    
    print("=" * 70)
    print("FinWhiz - Upload Scraped Data to GCS")
    print("=" * 70)
    print()
    
    # Initialize client
    print("Initializing GCS client...")
    try:
        client = GCSClient(bucket_name="finwhiz-storage", project_id="finwhiz-ac215")
        print(f"Connected to: gs://{client.bucket_name}")
    except Exception as e:
        print(f"ERROR: Failed to connect to GCS: {e}")
        print()
        print("Make sure you're authenticated:")
        print("1. Service account: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")
        print("2. Or use: gcloud auth application-default login")
        sys.exit(1)
    print()
    
    # Find scraped data root
    print("Looking for scraped data...")
    scraped_data_root = find_scraped_data()
    
    if not scraped_data_root:
        print("ERROR: Scraped data not found!")
        print("Expected location: data/ or src/webscraping/data/")
        sys.exit(1)
    
    print(f"Found scraped data at: {scraped_data_root}")
    print()
    
    # Define all possible sources with their GCS paths
    all_sources = {
        "consumer_finance": "base-knowledge/scraped-data/consumer-finance",
        "irs": "base-knowledge/scraped-data/irs",
        "investorgov": "base-knowledge/scraped-data/investorgov",
        "finra": "base-knowledge/scraped-data/finra",
        "local_pdfs": "base-knowledge/scraped-data/local-pdfs",
        "fred": "base-knowledge/scraped-data/fred",
    }
    
    # Filter to selected sources if specified
    if selected_sources:
        sources = {k: v for k, v in all_sources.items() if k in selected_sources}
        print(f"Uploading selected sources: {', '.join(sources.keys())}")
    else:
        sources = all_sources
        print("Uploading all available sources")
    print()
    
    # Upload each source
    total_uploaded = 0
    uploaded_sources = []
    
    for source_name, gcs_prefix in sources.items():
        source_path = scraped_data_root / source_name
        
        # Check if source exists
        if not source_path.exists():
            print(f"Skipping {source_name}: folder not found")
            continue
        
        # Check for NDJSON and JSON.GZ files (flat structure)
       # NEW - checks .ndjson, .json.gz, and .jsonl.gz:
        ndjson_files = list(source_path.glob('*.ndjson'))
        json_gz_files = list(source_path.glob('*.json.gz'))
        jsonl_gz_files = list(source_path.glob('*.jsonl.gz'))
        all_files = ndjson_files + json_gz_files + jsonl_gz_files

        if not all_files:
            print(f"Skipping {source_name}: no .ndjson or .json.gz files found")
            continue

        print(f"Uploading {source_name}...")
        print(f"  Local:  {source_path}")
        print(f"  GCS:    gs://{client.bucket_name}/{gcs_prefix}/")
        print(f"  Files:  {len(ndjson_files)} .ndjson + {len(json_gz_files)} .json.gz + {len(jsonl_gz_files)} .jsonl.gz file(s)")
        
        count = client.upload_folder(
            local_folder=str(source_path),
            gcs_prefix=gcs_prefix
        )
        
        total_uploaded += count
        uploaded_sources.append(source_name)
        print(f"  Uploaded {count} files")
        print()
    
    # Summary
    print("=" * 70)
    print(f"Upload Complete!")
    print(f"  Sources: {', '.join(uploaded_sources) if uploaded_sources else 'none'}")
    print(f"  Total files: {total_uploaded}")
    print("=" * 70)
    print()
    
    # Verify upload
    if total_uploaded > 0:
        print("Verifying upload...")
        files = client.list_files(prefix="base-knowledge/scraped-data/")
        print(f"Total files in GCS: {len(files)}")
        print()
        
        if files:
            print("Sample files uploaded:")
            for file in files[:15]:
                print(f"  - {file}")
            if len(files) > 15:
                print(f"  ... and {len(files) - 15} more")
        
        print()
        print("SUCCESS: Data uploaded to GCS")
        print(f"View in console:")
        print(f"https://console.cloud.google.com/storage/browser/{client.bucket_name}/base-knowledge/scraped-data")
    else:
        print("WARNING: No files were uploaded")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Upload scraped data to GCS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload all sources
  python upload_all_scraped_data.py
  
  # Upload specific sources
  python upload_all_scraped_data.py --sources irs consumer_finance
  
  # List available sources
  python upload_all_scraped_data.py --list
        """
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        help="Specific sources to upload (e.g., irs consumer_finance)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available sources and exit"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Handle --list flag
    if args.list:
        print("=" * 70)
        print("Available Sources")
        print("=" * 70)
        data_root = find_scraped_data()
        if data_root:
            print(f"\nData directory: {data_root}\n")
            sources = list_available_sources(data_root)
            if sources:
                for source in sources:
                    source_path = data_root / source
                    ndjson_count = len(list(source_path.glob('*.ndjson')))
                    gz_count = len(list(source_path.glob('*.json.gz')))
                    print(f"  - {source}: {ndjson_count} .ndjson + {gz_count} .json.gz files")
            else:
                print("  No sources found with .ndjson or .json.gz files")
        else:
            print("\nERROR: Data directory not found")
        print()
        sys.exit(0)
    
    # Upload selected or all sources
    upload_all_scraped_data(selected_sources=args.sources)