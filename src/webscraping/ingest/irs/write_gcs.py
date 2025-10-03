"""Helpers for writing NDJSON payloads to Google Cloud Storage."""
from __future__ import annotations

import json
from typing import Iterable

from google.cloud import storage


def write_ndjson_gcs(bucket: str, path: str, records: Iterable[dict]) -> None:
    client = storage.Client()
    blob = client.bucket(bucket).blob(path)
    data = "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
    blob.upload_from_string(data, content_type="application/x-ndjson")
