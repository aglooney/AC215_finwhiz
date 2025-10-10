# FinWhiz Storage Module

This module provides utilities for interacting with Google Cloud Storage (GCS).

## Purpose

- Upload scraped data to GCS
- Download data for processing
- Manage files in cloud storage
- Shared utility for all containers

## Files

- `gcs_client.py`: Core GCS client with upload/download/list operations
- `test_gcs.py`: Test script to verify GCS connection
- `upload_scraped_data.py`: Script to upload scraped data (example for team)

## Setup

### Install Dependencies
```bash
pip install google-cloud-storage