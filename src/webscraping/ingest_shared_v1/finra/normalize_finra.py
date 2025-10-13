"""Driver for FINRA document ingestion and normalization."""
from __future__ import annotations

import argparse
import json
import logging
import re
import hashlib
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse

import yaml

# Import from shared utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared import (
    FetchResult,
    fetch_url,
    extract_main_html,
    pdf_to_blocks,
    IngestRecord,
    make_record,
    upload_file_to_gcs,
)

LOGGER = logging.getLogger(__name__)


def infer_year(value: Optional[str]) -> Optional[int]:
    """Extract 4-digit year from string."""
    if not value:
        return None
    match = re.search(r"(20\d{2})", value)
    return int(match.group(1)) if match else None


def slugify(value: str) -> str:
    """Convert string to URL-safe slug."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "document"


def determine_doctype(url: str) -> str:
    """Infer document type from URL patterns."""
    url_lower = url.lower()
    
    if "calculator" in url_lower:
        return "calculator"
    if "tools-and-calculators" in url_lower:
        return "tools"
    if "publications" in url_lower:
        return "publication"
    if "personal-finance" in url_lower:
        return "guide"
    if "investing-basics" in url_lower:
        return "basics"
    if "investment-products" in url_lower:
        return "product-guide"
    
    return "guide"


def process_fetch_result(
    result: FetchResult, 
    *, 
    doc_hint: Optional[str] = None,
    authority: str = "finra.org",
    default_doctype: str = "guide"
) -> list[IngestRecord]:
    """Route to HTML or PDF processor based on content type."""
    if result.is_html or isinstance(result.content, str):
        return process_html(result, doc_hint=doc_hint, authority=authority, 
                          default_doctype=default_doctype)
    if result.is_pdf or isinstance(result.content, (bytes, bytearray)):
        return process_pdf(result, doc_hint=doc_hint, authority=authority,
                         default_doctype=default_doctype)
    
    LOGGER.warning("Unsupported content type for %s (%s)", result.url, result.content_type)
    return []


def process_html(
    result: FetchResult, 
    *, 
    doc_hint: Optional[str] = None,
    authority: str = "finra.org",
    default_doctype: str = "guide"
) -> list[IngestRecord]:
    """Process HTML - ONE record per page (no chunking)."""
    title, blocks = extract_main_html(str(result.content))
    
    if not blocks:
        LOGGER.warning("No content blocks extracted from %s", result.url)
        return []
    
    # Combine all text into one record
    all_text = "\n".join(block.text for block in blocks)
    
    # Validate we have meaningful content
    if len(all_text.strip()) < 100:
        LOGGER.warning("Insufficient content from %s (only %d chars)", result.url, len(all_text))
        return []
    
    doc_id = slugify(title or doc_hint or result.url)
    year = infer_year(title) or infer_year(result.url)
    doctype = determine_doctype(result.url) or default_doctype

    record = make_record(
        doc_id=doc_id,
        url=result.url,
        title=title or doc_hint or result.url,
        year=year,
        section=None,
        text=all_text,
        doctype=doctype,
        authority=authority,
    )
    
    return [record]


def process_pdf(
    result: FetchResult, 
    *, 
    doc_hint: Optional[str] = None,
    authority: str = "finra.org",
    default_doctype: str = "publication"
) -> list[IngestRecord]:
    """Process PDF - ONE record per PDF page."""
    blocks = pdf_to_blocks(bytes(result.content))
    
    if not blocks:
        LOGGER.warning("No content blocks from PDF %s", result.url)
        return []
    
    doc_id = slugify(doc_hint or result.url.split("/")[-1])
    year = infer_year(result.url)
    title = doc_hint or result.url.split("/")[-1]
    doctype = determine_doctype(result.url) or default_doctype
    
    # Create one record per PDF page
    records = []
    for block in blocks:
        record = make_record(
            doc_id=doc_id,
            url=result.url,
            title=title,
            year=year,
            section=None,
            text=block.text,
            doctype=doctype,
            authority=authority,
            page=block.page,
        )
        records.append(record)
    
    return records


def write_local_ndjson(path: Path, records: Iterable[IngestRecord]) -> None:
    """Write records to local NDJSON file."""
    serialized = "\n".join(json.dumps(record.to_dict(), ensure_ascii=False) 
                          for record in records)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")


def load_config(path: Path) -> dict:
    """Load YAML configuration."""
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def filter_allowed(seeds: list[str], allow_domains: list[str]) -> list[str]:
    """Filter URLs to only allowed domains."""
    if not allow_domains:
        return seeds
    
    allowed = []
    allowed_set = {domain.lower() for domain in allow_domains}
    
    for url in seeds:
        domain = urlparse(url).netloc.lower()
        if domain in allowed_set:
            allowed.append(url)
        else:
            LOGGER.warning("Skipping %s; domain not in allowlist", url)
    
    return allowed


def ingest_from_config(
    config_path: Path, 
    *, 
    output_dir: Path, 
    bucket: Optional[str],
    gcs_prefix: Optional[str], 
    max_pages: Optional[int] = None
) -> None:
    """Main ingestion orchestrator."""
    config = load_config(config_path)
    
    # Load config values
    seeds: list[str] = config.get("seeds", [])
    allow_domains: list[str] = config.get("allow_domains", [])
    authority: str = config.get("authority", "finra.org")
    default_doctype: str = config.get("default_doctype", "guide")
    
    # Filter and limit seeds
    seeds = filter_allowed(seeds, allow_domains)
    if max_pages is None:
        max_pages = config.get("max_pages")
    if max_pages is not None:
        seeds = seeds[:int(max_pages)]

    LOGGER.info("Processing %d URLs from FINRA.org", len(seeds))

    # Process each URL
    success_count = 0
    failure_count = 0
    
    for idx, url in enumerate(seeds, 1):
        LOGGER.info("[%d/%d] Fetching %s", idx, len(seeds), url)
        
        try:
            result = fetch_url(url)
        except Exception as exc:
            LOGGER.error("FAILED to fetch %s: %s", url, exc)
            failure_count += 1
            continue

        records = process_fetch_result(
            result, 
            authority=authority, 
            default_doctype=default_doctype
        )
        
        if not records:
            LOGGER.warning("WARNING: No records produced for %s", url)
            failure_count += 1
            continue

        # Write to local filesystem - flat structure with descriptive names
        slug = slugify(records[0].title or url)
        
        # Truncate slug if too long (keep it under 200 chars for safety)
        if len(slug) > 200:
            # Keep first 190 chars + hash of full slug for uniqueness
            slug_hash = hashlib.md5(slug.encode()).hexdigest()[:8]
            slug = slug[:190] + "_" + slug_hash
        
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
                success_count, failure_count, len(seeds))
    LOGGER.info("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Normalize FINRA documents for FinWhiz ingest"
    )
    parser.add_argument(
        "--config", 
        type=Path, 
        default=Path(__file__).parent / "finra_config.yaml",
        help="Path to finra_config.yaml"
    )
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("data/finra"), 
        help="Directory to store NDJSON output"
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
        "--max-pages", 
        type=int, 
        default=None, 
        help="Override maximum pages from config"
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
    
    ingest_from_config(
        args.config,
        output_dir=args.output_dir,
        bucket=args.bucket,
        gcs_prefix=args.gcs_prefix,
        max_pages=args.max_pages,
    )


if __name__ == "__main__":
    main()