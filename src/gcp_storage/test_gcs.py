"""Test GCS connection and operations"""

import sys
import tempfile
from pathlib import Path

from gcs_client import GCSClient
from dotenv import load_dotenv
import os

load_dotenv()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.environ.get("BUCKET_CREDENTIALS")
SERVICE_ACCOUNT_KEY = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    None
)

def test_gcs():
    """Test all GCS operations"""
    
    print("Testing GCS connection...\n")
    
    # Initialize client
    client = GCSClient(bucket_name="finwhiz-storage", project_id="finwhiz-ac215")
    
    # Test 1: Bucket exists
    print("Test 1: Check bucket exists")
    if client.bucket.exists():
        print("PASS: Bucket exists\n")
    else:
        print("FAIL: Bucket not found\n")
        sys.exit(1)
    
    # Test 2: Upload test file
    print("Test 2: Upload test file")
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("FinWhiz test file - GCS connection works!")
        test_file = f.name
    
    success = client.upload_file(test_file, "test/test-file.txt")
    print(f"{'PASS' if success else 'FAIL'}: Upload test\n")
    
    # Test 3: Check file exists
    print("Test 3: Check file exists")
    exists = client.file_exists("test/test-file.txt")
    print(f"{'PASS' if exists else 'FAIL'}: File exists check\n")
    
    # Test 4: List files
    print("Test 4: List files in test/ folder")
    files = client.list_files(prefix="test/")
    print(f"PASS: Found {len(files)} file(s)")
    for file in files:
        print(f"  - {file}")
    print()
    
    # Test 5: Download file
    print("Test 5: Download file")
    download_path = "/tmp/downloaded-test.txt"
    success = client.download_file("test/test-file.txt", download_path)
    if success:
        with open(download_path, 'r') as f:
            content = f.read()
            print(f"PASS: Downloaded successfully")
            print(f"  Content: {content}\n")
    else:
        print("FAIL: Download failed\n")
    
    # Test 6: Delete test file
    print("Test 6: Clean up test file")
    success = client.delete_file("test/test-file.txt")
    print(f"{'PASS' if success else 'FAIL'}: Cleanup\n")
    
    # Cleanup local files
    Path(test_file).unlink(missing_ok=True)
    if Path(download_path).exists():
        Path(download_path).unlink()
    
    print("All tests complete!")


if __name__ == "__main__":
    test_gcs()