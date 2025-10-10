"""GCS Client for FinWhiz - Interact with Google Cloud Storage"""

import logging
from pathlib import Path
from typing import List

from google.cloud import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GCSClient:
    """Client for Google Cloud Storage operations"""
    
    def __init__(self, bucket_name: str = "finwhiz-storage", project_id: str = "finwhiz-ac215"):
        """
        Initialize GCS client
        
        Args:
            bucket_name: GCS bucket name
            project_id: GCP project ID
        """
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)
        
        logger.info(f"Initialized GCS client for bucket: {bucket_name}")
    
    def upload_file(self, local_path: str, gcs_path: str) -> bool:
        """
        Upload a file to GCS
        
        Args:
            local_path: Path to local file
            gcs_path: Destination path in bucket (e.g., 'base-knowledge/data.json')
        
        Returns:
            True if successful
        """
        try:
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_filename(local_path)
            logger.info(f"Uploaded {local_path} -> gs://{self.bucket_name}/{gcs_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            return False
    
    def upload_folder(self, local_folder: str, gcs_prefix: str) -> int:
        """
        Upload entire folder to GCS recursively
        
        Args:
            local_folder: Local folder path
            gcs_prefix: Prefix in bucket (e.g., 'base-knowledge/scraped-data/')
        
        Returns:
            Number of files uploaded
        """
        local_path = Path(local_folder)
        if not local_path.exists():
            logger.error(f"Folder not found: {local_folder}")
            return 0
        
        count = 0
        for file_path in local_path.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(local_path)
                gcs_path = f"{gcs_prefix.rstrip('/')}/{relative_path}"
                
                if self.upload_file(str(file_path), gcs_path):
                    count += 1
        
        logger.info(f"Uploaded {count} files from {local_folder}")
        return count
    
    def download_file(self, gcs_path: str, local_path: str) -> bool:
        """
        Download a file from GCS
        
        Args:
            gcs_path: Path in bucket
            local_path: Local destination path
        
        Returns:
            True if successful
        """
        try:
            blob = self.bucket.blob(gcs_path)
            blob.download_to_filename(local_path)
            logger.info(f"Downloaded gs://{self.bucket_name}/{gcs_path} -> {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download {gcs_path}: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[str]:
        """
        List files in bucket with optional prefix
        
        Args:
            prefix: Filter by prefix (e.g., 'base-knowledge/')
        
        Returns:
            List of file paths
        """
        blobs = self.bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]
    
    def file_exists(self, gcs_path: str) -> bool:
        """
        Check if file exists in bucket
        
        Args:
            gcs_path: Path to check
        
        Returns:
            True if file exists
        """
        blob = self.bucket.blob(gcs_path)
        return blob.exists()
    
    def delete_file(self, gcs_path: str) -> bool:
        """
        Delete a file from GCS
        
        Args:
            gcs_path: Path to file
        
        Returns:
            True if successful
        """
        try:
            blob = self.bucket.blob(gcs_path)
            blob.delete()
            logger.info(f"Deleted gs://{self.bucket_name}/{gcs_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {gcs_path}: {e}")
            return False


if __name__ == "__main__":
    # Quick test
    client = GCSClient()
    print(f"Connected to bucket: {client.bucket_name}")
    print(f"Bucket exists: {client.bucket.exists()}")