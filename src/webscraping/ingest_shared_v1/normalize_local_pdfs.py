"""Process local PDF files for FinWhiz ingestion."""
from __future__ import annotations

import argparse
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional

# Import from shared utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared import (
    pdf_to_blocks,
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
    import re
    value = re.sub(r'[^a-z0-9-]+', '-', value)
    return value.strip("-") or "document"


def process_pdf(
    pdf_path: Path,
    *,
    authority: str = "local",
    doctype: str = "document"
) -> list[IngestRecord]:
    """Process a local PDF file into records."""
    LOGGER.info("Processing PDF: %s", pdf_path.name)
    
    # Read PDF file
    try:
        pdf_bytes = pdf_path.read_bytes()
    except Exception as exc:
        LOGGER.error("FAILED to read %s: %s", pdf_path, exc)
        return []
    
    # Extract text blocks
    blocks = pdf_to_blocks(pdf_bytes)
    
    if not blocks:
        LOGGER.warning("WARNING: No content blocks from PDF %s", pdf_path.name)
        return []
    
    # Use filename as document ID and title
    doc_id = slugify(pdf_path.stem)
    title = pdf_path.stem.replace('_', ' ').replace('-', ' ').title()
    
    # Create one record per PDF page
    records = []
    for block in blocks:
        record = make_record(
            doc_id=doc_id,
            url=f"file://{pdf_path.absolute()}",
            title=title,
            year=None,
            section=None,
            text=block.text,
            doctype=doctype,
            authority=authority,
            page=block.page,
        )
        records.append(record)
    
    LOGGER.info("SUCCESS: Extracted %d pages from %s", len(records), pdf_path.name)
    return records


def write_local_ndjson(path: Path, records: list[IngestRecord]) -> None:
    """Write records to local NDJSON file."""
    serialized = "\n".join(json.dumps(record.to_dict(), ensure_ascii=False) 
                          for record in records)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")


def process_pdf_directory(
    input_dir: Path,
    output_dir: Path,
    *,
    authority: str = "local",
    doctype: str = "document",
    bucket: Optional[str] = None,
    gcs_prefix: Optional[str] = None
) -> None:
    """Process all PDFs in a directory."""
    
    # Find all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        LOGGER.warning("No PDF files found in %s", input_dir)
        return
    
    LOGGER.info("Found %d PDF files in %s", len(pdf_files), input_dir)
    
    success_count = 0
    failure_count = 0
    
    for pdf_path in pdf_files:
        # Process PDF
        records = process_pdf(pdf_path, authority=authority, doctype=doctype)
        
        if not records:
            failure_count += 1
            continue
        
        # Create output filename
        slug = slugify(pdf_path.stem)
        
        # Truncate slug if too long
        if len(slug) > 200:
            slug_hash = hashlib.md5(slug.encode()).hexdigest()[:8]
            slug = slug[:190] + "_" + slug_hash
        
        # Write to local filesystem
        local_path = output_dir / f"{slug}.ndjson"
        write_local_ndjson(local_path, records)
        LOGGER.info("SUCCESS: Wrote %d records to %s", len(records), local_path)
        
        # Upload to GCS if configured
        if bucket and gcs_prefix:
            gcs_path = f"{gcs_prefix.rstrip('/')}/{slug}.ndjson"
            upload_file_to_gcs(local_path, bucket, gcs_path)
        
        success_count += 1
    
    LOGGER.info("=" * 60)
    LOGGER.info("Summary: %d succeeded, %d failed out of %d total", 
                success_count, failure_count, len(pdf_files))
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
        bucket=args.bucket,
        gcs_prefix=args.gcs_prefix,
    )


if __name__ == "__main__":
    main()