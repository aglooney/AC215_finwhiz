"""Shared utilities for web scraping and document ingestion."""
from .fetch import fetch_url, resolve_url, FetchResult
from .write_gcs import (
    write_ndjson_local,
    write_ndjson_local_and_gcs,
    write_ndjson_gcs,
    upload_file_to_gcs,
)
from .parse_html import extract_main_html, HtmlBlock, iter_text as iter_html_text
from .parse_pdf import pdf_to_blocks, PdfBlock, iter_text as iter_pdf_text
from .chunk import chunk_blocks, Chunk
from .schema import IngestRecord, make_record

__all__ = [
    "fetch_url",
    "resolve_url",
    "FetchResult",
    "write_ndjson_local",
    "write_ndjson_local_and_gcs",
    "write_ndjson_gcs",
    "upload_file_to_gcs",
    "extract_main_html",
    "HtmlBlock",
    "iter_html_text",
    "pdf_to_blocks",
    "PdfBlock",
    "iter_pdf_text",
    "chunk_blocks",
    "Chunk",
    "IngestRecord",
    "make_record",
]