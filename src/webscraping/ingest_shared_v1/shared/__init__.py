"""Shared utilities for FinWhiz web scraping."""
from __future__ import annotations

from .fetch import FetchResult, fetch_url, resolve_url
from .parse_html import HtmlBlock, extract_main_html, iter_text as iter_html_text
from .parse_pdf import PdfBlock, pdf_to_blocks, iter_text as iter_pdf_text
from .schema import IngestRecord, make_record
from .write_gcs import upload_file_to_gcs, write_ndjson_gcs

__all__ = [
    # Fetching
    "FetchResult",
    "fetch_url",
    "resolve_url",
    # HTML parsing
    "HtmlBlock",
    "extract_main_html",
    "iter_html_text",
    # PDF parsing
    "PdfBlock",
    "pdf_to_blocks",
    "iter_pdf_text",
    # Schema
    "IngestRecord",
    "make_record",
    # GCS writing
    "upload_file_to_gcs",
    "write_ndjson_gcs",
]