"""Process local PDF files for FinWhiz ingestion."""
from __future__ import annotations

import argparse
import json
import logging
import hashlib
import re
from pathlib import Path
from typing import Optional

# Import from shared utilities - PROPER IMPORTS
from ingest_shared.shared import (
    pdf_to_blocks,
    chunk_blocks,  # ← Added chunking
    IngestRecord,
    make_record,
    upload_file_to_gcs,
)

LOGGER = logging.getLogger(__name__)


def slugify(value: str) -> str:
    """Convert string to URL-safe slug."""
    value = value.strip().lower()
    value = value.replace('.pdf', '')  # Remove .pdf extension
    value = value.replace('_', '-').replace(' ', '-')
    # Remove any non-alphanumeric characters except hyphens
    value = re.sub(r'[^a-z0-9-]+', '-', value)
    return value.strip("-") or "document"


def infer_year(filename: str) -> Optional[int]:
    """Try to extract year from filename."""
    match = re.search(r'(20\d{2})', filename)
    return int(match.group(1)) if match else None


def process_pdf(
    pdf_path: Path,
    *,
    authority: str = "local",
    doctype: str = "document",
    chunk_size: int = 1200,
) -> list[IngestRecord]:
    """Process a local PDF file into chunked records (like IRS/CF)."""
    LOGGER.info("Processing PDF: %s", pdf_path.name)
    
    # Read PDF file
    try:
        pdf_bytes = pdf_path.read_bytes()
    except Exception as exc:
        LOGGER.error("FAILED to read %s: %s", pdf_path, exc)
        return []
    
    # Extract text blocks from PDF
    blocks = pdf_to_blocks(pdf_bytes)
    
    if not blocks:
        LOGGER.warning("WARNING: No content blocks from PDF %s", pdf_path.name)
        return []
    
    # Convert to dict format for chunking
    block_dicts = [{"text": block.text, "page": block.page} for block in blocks]
    
    # CHUNK the PDF content (like IRS/CF)
    chunks = chunk_blocks(block_dicts, max_chars=chunk_size)
    
    if not chunks:
        LOGGER.warning("WARNING: No chunks produced from %s", pdf_path.name)
        return []
    
    # Use filename as document ID and title
    doc_id = slugify(pdf_path.stem)
    title = pdf_path.stem.replace('_', ' ').replace('-', ' ').title()
    year = infer_year(pdf_path.stem)
    
    # Create multiple records with DEDUPLICATION (like IRS/CF)
    records: list[IngestRecord] = []
    seen_hashes: set[str] = set()
    
    for idx, chunk in enumerate(chunks):
        # Deduplicate using SHA1 hash
        digest = hashlib.sha1(chunk.text.encode("utf-8")).hexdigest()
        if digest in seen_hashes:
            continue
        seen_hashes.add(digest)
        
        records.append(
            make_record(
                doc_id=doc_id,
                url=f"file://{pdf_path.name}",  # Simplified path
                title=title,
                year=year,
                section=chunk.section,
                chunk_id=idx,
                text=chunk.text,
                doctype=doctype,
                authority=authority,
                page=chunk.start_page,
            )
        )
    
    LOGGER.info("SUCCESS: Created %d chunks from %s", len(records), pdf_path.name)
    return records


def write_local_ndjson(path: Path, records: list[IngestRecord]) -> None:
    """Write records to local NDJSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def process_pdf_directory(
    input_dir: Path,
    output_dir: Path,
    *,
    authority: str = "local",
    doctype: str = "document",
    chunk_size: int = 1200,
    bucket: Optional[str] = None,
    gcs_prefix: Optional[str] = None,
) -> None:
    """Process all PDFs in a directory."""
    
    # Find all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        LOGGER.warning("No PDF files found in %s", input_dir)
        return
    
    LOGGER.info("Found %d PDF files in %s", len(pdf_files), input_dir)
    LOGGER.info("Chunking mode: ENABLED (~%d chars per chunk, like IRS)", chunk_size)
    
    success_count = 0
    failure_count = 0
    total_records = 0
    
    for pdf_path in pdf_files:
        # Process PDF with chunking
        records = process_pdf(
            pdf_path, 
            authority=authority, 
            doctype=doctype,
            chunk_size=chunk_size,
        )
        
        if not records:
            failure_count += 1
            continue
        
        # Create output filename
        slug = slugify(pdf_path.stem)
        
        # Truncate slug if too long
        if len(slug) > 200:
            slug_hash = hashlib.md5(slug.encode()).hexdigest()[:8]
            slug = slug[:190] + "_" + slug_hash
        
        # Write to local filesystem (flat structure)
        local_path = output_dir / f"{slug}.ndjson"
        write_local_ndjson(local_path, records)
        LOGGER.info("SUCCESS: Wrote %d chunks to %s", len(records), local_path)
        
        total_records += len(records)
        
        # Upload to GCS if configured
        if bucket and gcs_prefix:
            gcs_path = f"{gcs_prefix.rstrip('/')}/{slug}.ndjson"
            upload_file_to_gcs(local_path, bucket, gcs_path)
        
        success_count += 1
    
    LOGGER.info("=" * 60)
    LOGGER.info("Summary: %d PDFs succeeded, %d failed out of %d total", 
                success_count, failure_count, len(pdf_files))
    LOGGER.info("Total chunks created: %d (chunked at %d chars)", total_records, chunk_size)
    LOGGER.info("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process local PDF files for FinWhiz ingest"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("pdf_data"),
        help="Directory containing PDF files to process"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/local_pdfs"),
        help="Directory to store NDJSON output"
    )
    parser.add_argument(
        "--authority",
        type=str,
        default="local",
        help="Authority/source name for these documents"
    )
    parser.add_argument(
        "--doctype",
        type=str,
        default="document",
        help="Document type for these PDFs"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1200,
        help="Characters per chunk (default: 1200, like IRS)"
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default=None,
        help="Optional GCS bucket name"
    )
    parser.add_argument(
        "--gcs-prefix",
        type=str,
        default=None,
        help="Path prefix inside the GCS bucket"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging verbosity"
    )
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    process_pdf_directory(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        authority=args.authority,
        doctype=args.doctype,
        chunk_size=args.chunk_size,
        bucket=args.bucket,
        gcs_prefix=args.gcs_prefix,
    )


if __name__ == "__main__":
    main()