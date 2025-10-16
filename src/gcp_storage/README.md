# FinWhiz Storage Utilities

Helpers for interacting with Google Cloud Storage (GCS). These scripts are shared across the webscraping, embedding, and agent pipelines.

## Capabilities

- Upload newly scraped/processed datasets to project buckets.
- Download or list existing artifacts (Chroma snapshots, PDF archives, etc.).
- Clean old prefixes when regenerating datasets.
- Perform smoke tests to validate credentials before longer jobs.

## Key Files

| File | Purpose |
|------|---------|
| `gcs_client.py` | Reusable wrapper over the GCS SDK (upload/download/list/delete). |
| `gcp_config.py` | Central configuration for bucket + project IDs. |
| `upload_all_scraped_data.py` | Bulk uploader for the latest chunked datasets. |
| `clean_bucket.py` | Removes objects by prefix (handy when refreshing data). |
| `test_gcs.py` | End-to-end sanity check – upload → list → download → delete. |

## Running Locally

```bash
pip install google-cloud-storage python-dotenv
python test_gcs.py
```

Set `GOOGLE_APPLICATION_CREDENTIALS` (or update `.env`) so the scripts can authenticate. Buckets and project IDs default to values in `gcp_config.py` but can be overridden via environment variables.

These utilities can also be executed inside ad-hoc containers if preferred; just mount the repository and secrets directory when running `docker run`.
