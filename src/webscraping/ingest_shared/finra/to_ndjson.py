"""Convert FINRA chunks to shared NDJSON format for consistency with IRS/Consumer Finance."""
from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import Optional

# Import shared utilities
from ingest_shared.shared import (
    IngestRecord,
    make_record,
    write_ndjson_local,
    upload_file_to_gcs,
)

# Import FINRA utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from common.io_utils import iter_paths, read_json_gz, ensure_dir

LOGGER = logging.getLogger(__name__)


def slugify(value: str) -> str:
    """Convert string to URL-safe slug."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "document"


def infer_year(value: Optional[str]) -> Optional[int]:
    """Extract 4-digit year from string."""
    if not value:
        return None
    match = re.search(r"(20\d{2})", value)
    return int(match.group(1)) if match else None


def convert_finra_chunk_to_record(chunk: dict, chunk_idx: int) -> IngestRecord:
    """Convert a FINRA chunk to IngestRecord format.
    
    Args:
        chunk: FINRA chunk dictionary with keys like:
            - id, source_url, title, section, publish_date, content, etc.
        chunk_idx: Index of this chunk
        
    Returns:
        IngestRecord compatible with IRS/Consumer Finance format
    """
    # Extract fields from FINRA chunk
    title = chunk.get("title", "")
    url = chunk.get("source_url", "")
    content = chunk.get("content", "")
    publish_date = chunk.get("publish_date")
    section_list = chunk.get("section", [])
    
    # Create doc_id from title
    doc_id = slugify(title or url)
    
    # Extract year from publish_date or URL
    year = infer_year(publish_date) or infer_year(url)
    
    # Section is the last item in breadcrumb path
    section = section_list[-1] if section_list else None
    
    # Create record using shared schema
    return make_record(
        doc_id=doc_id,
        url=url,
        title=title,
        year=year,
        section=section,
        chunk_id=chunk_idx,
        text=content,
        authority="finra.org",
        doctype="education",
        language="en",
    )


def convert_finra_to_ndjson(
    chunks_dir: Path,
    output_dir: Path,
    *,
    bucket: Optional[str] = None,
    gcs_prefix: Optional[str] = None,
) -> None:
    """Convert all FINRA chunk files to shared NDJSON format.
    
    Args:
        chunks_dir: Directory containing FINRA chunk .json.gz files
        output_dir: Output directory (e.g., data/finra/)
        bucket: Optional GCS bucket name
        gcs_prefix: Optional GCS prefix (e.g., base-knowledge/scraped-data/finra)
    """
    ensure_dir(output_dir)
    
    # Track documents by doc_id to group chunks together
    documents: dict[str, list[IngestRecord]] = {}
    
    total_chunks = 0
    for chunk_file in iter_paths(chunks_dir, ".json.gz"):
        LOGGER.info(f"Processing {chunk_file}")
        chunks = read_json_gz(chunk_file)
        
        for chunk in chunks:
            # Create record
            record = convert_finra_chunk_to_record(chunk, chunk_idx=total_chunks)
            
            # Group by doc_id
            if record.doc_id not in documents:
                documents[record.doc_id] = []
            documents[record.doc_id].append(record)
            
            total_chunks += 1
    
    LOGGER.info(f"Converted {total_chunks} chunks into {len(documents)} documents")
    
    # Write each document as a separate NDJSON file
    for doc_id, records in documents.items():
        # Create path: data/finra/doc-slug.ndjson (flat structure)
        local_path = output_dir / f"{doc_id}.ndjson"  # ← FLAT STRUCTURE
        
        # Write locally
        write_ndjson_local(local_path, [r.to_dict() for r in records])
        LOGGER.info(f"Wrote {len(records)} records to {local_path}")
        
        # Upload to GCS if configured
        if bucket and gcs_prefix:
            gcs_path = f"{gcs_prefix.rstrip('/')}/{doc_id}.ndjson"  # ← FLAT STRUCTURE
            upload_file_to_gcs(local_path, bucket, gcs_path)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert FINRA chunks to shared NDJSON format"
    )
    parser.add_argument(
        "--chunks-dir",
        type=Path,
        default=Path("data/chunks"),
        help="Directory containing FINRA chunk files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/finra"),
        help="Output directory for NDJSON files",
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default=None,
        help="Optional GCS bucket name",
    )
    parser.add_argument(
        "--gcs-prefix",
        type=str,
        default=None,
        help="Path prefix inside the GCS bucket",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging verbosity",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    convert_finra_to_ndjson(
        chunks_dir=args.chunks_dir,
        output_dir=args.output_dir,
        bucket=args.bucket,
        gcs_prefix=args.gcs_prefix,
    )


if __name__ == "__main__":
    main()