"""
GCP Configuration for FinWhiz

This module centralizes all GCP-related configuration.
Values can be overridden using environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# GCP Project Settings
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "finwhiz-ac215")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")

# GCS Bucket Settings
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "finwhiz-storage")

# Bucket Path Prefixes
BASE_KNOWLEDGE_PREFIX = "base-knowledge"
USER_UPLOADS_PREFIX = "user-uploads"
SCRAPED_DATA_PREFIX = f"{BASE_KNOWLEDGE_PREFIX}/scraped-data"
SYNTHETIC_DATA_PREFIX = f"{BASE_KNOWLEDGE_PREFIX}/synthetic-data"

# Service Account (if using)
SERVICE_ACCOUNT_KEY = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    None
)


def verify_config():
    """Verify all required configuration is set"""
    required = {
        "GCP_PROJECT_ID": GCP_PROJECT_ID,
        "GCS_BUCKET_NAME": GCS_BUCKET_NAME,
    }
    
    missing = [k for k, v in required.items() if not v]
    
    if missing:
        raise ValueError(f"Missing required config: {', '.join(missing)}")
    
    return True


def print_config():
    """Print current configuration (for debugging)"""
    print("GCP Configuration:")
    print(f"  Project ID: {GCP_PROJECT_ID}")
    print(f"  Region: {GCP_REGION}")
    print(f"  Bucket: {GCS_BUCKET_NAME}")
    print(f"  Base Knowledge Path: {SCRAPED_DATA_PREFIX}")


if __name__ == "__main__":
    verify_config()
    print_config()