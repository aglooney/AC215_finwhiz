"""Clean scraped data from GCS bucket"""
from gcs_client import GCSClient


def clean_scraped_data():
    """Delete all files under base-knowledge/scraped-data/"""
    
    print("=" * 70)
    print("FinWhiz - Clean GCS Bucket")
    print("=" * 70)
    print()
    
    # Initialize client
    try:
        client = GCSClient(bucket_name="finwhiz-storage", project_id="finwhiz-ac215")
        print(f"Connected to: gs://{client.bucket_name}")
    except Exception as e:
        print(f"ERROR: Failed to connect to GCS: {e}")
        print("Make sure GOOGLE_APPLICATION_CREDENTIALS is set!")
        return
    print()
    
    prefix = "base-knowledge/scraped-data/"
    
    # List files first
    print(f"Looking for files under {prefix}...")
    files = client.list_files(prefix=prefix)
    
    if not files:
        print("No files found to delete.")
        print("Bucket is already clean!")
        return
    
    print(f"Found {len(files)} files to delete:")
    for f in files[:20]:
        print(f"  - {f}")
    if len(files) > 20:
        print(f"  ... and {len(files) - 20} more")
    print()
    
    # Confirm deletion
    response = input(f"Delete all {len(files)} files? Type 'yes' to confirm: ")
    
    if response.lower() != 'yes':
        print("Cancelled. No files were deleted.")
        return
    
    # Delete files
    print()
    print("Deleting files...")
    deleted = 0
    failed = 0
    
    for file_path in files:
        if client.delete_file(file_path):
            deleted += 1
        else:
            failed += 1
        
        # Progress indicator
        if (deleted + failed) % 10 == 0:
            print(f"  Progress: {deleted + failed}/{len(files)}")
    
    print()
    print("=" * 70)
    print(f"Deletion Complete!")
    print(f"  Deleted: {deleted} files")
    if failed > 0:
        print(f"  Failed: {failed} files")
    print("=" * 70)


if __name__ == "__main__":
    clean_scraped_data()