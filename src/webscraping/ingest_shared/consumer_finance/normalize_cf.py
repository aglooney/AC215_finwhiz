"""Driver for consumer finance document ingestion and normalization with link following."""
from __future__ import annotations

import argparse
import json
import logging
import re
import hashlib
from pathlib import Path
from typing import Iterable, Optional, Set
from urllib.parse import urlparse, urljoin

import yaml
from bs4 import BeautifulSoup

# Import from shared utilities
from ingest_shared.shared import (
    FetchResult,
    fetch_url,
    pdf_to_blocks,
    chunk_blocks,
    IngestRecord,
    make_record,
    upload_file_to_gcs,
)

# Keep consumer finance specific HTML parser
from ingest_shared.consumer_finance.parse_html_cf import extract_main_html

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
    if "ask-cfpb" in url_lower:
        return "faq"
    if "consumer-tools" in url_lower:
        return "guide"
    if "owning-a-home" in url_lower:
        return "guide"
    if "paying-for-college" in url_lower:
        return "guide"
    if any(token in url_lower for token in ("publication", "pub")):
        return "publication"
    return "webpage"


def extract_links(html: str, base_url: str) -> Set[str]:
    """Extract all links from HTML that match consumer finance patterns."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        
        # Skip anchors and javascript
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue
        
        # Resolve relative URLs
        if not href.startswith("http"):
            href = urljoin(base_url, href)
        
        # Only include consumerfinance.gov links
        if "consumerfinance.gov" in href:
            # Clean up the URL (remove fragments, trailing slashes for comparison)
            clean_url = href.split("#")[0].rstrip("/")
            links.add(clean_url)
    
    return links


def should_follow_links(url: str, config: dict) -> bool:
    """Check if this URL should have its links followed."""
    follow_pages = config.get("follow_links_from", [])
    
    for pattern in follow_pages:
        if re.search(pattern, url):
            return True
    
    return False


def filter_links(links: Set[str], allow_patterns: list[str], deny_patterns: list[str]) -> Set[str]:
    """Filter links based on allow and deny patterns."""
    filtered = set()
    
    for link in links:
        # Check deny patterns first
        if deny_patterns and any(re.search(pattern, link) for pattern in deny_patterns):
            continue
        
        # Check allow patterns
        if allow_patterns:
            if any(re.search(pattern, link) for pattern in allow_patterns):
                filtered.add(link)
        else:
            filtered.add(link)
    
    return filtered


def process_fetch_result(
    result: FetchResult, 
    *, 
    doc_hint: Optional[str] = None,
    authority: str = "consumerfinance.gov",
    default_doctype: str = "webpage",
    chunk_size: int = 1200,
) -> list[IngestRecord]:
    """Route to HTML or PDF processor based on content type."""
    if result.is_html or isinstance(result.content, str):
        return process_html(
            result, 
            doc_hint=doc_hint, 
            authority=authority, 
            default_doctype=default_doctype,
            chunk_size=chunk_size,
        )
    if result.is_pdf or isinstance(result.content, (bytes, bytearray)):
        return process_pdf(
            result, 
            doc_hint=doc_hint, 
            authority=authority,
            default_doctype=default_doctype,
            chunk_size=chunk_size,
        )
    
    LOGGER.warning("Unsupported content type for %s (%s)", result.url, result.content_type)
    return []


def process_html(
    result: FetchResult, 
    *, 
    doc_hint: Optional[str] = None,
    authority: str = "consumerfinance.gov",
    default_doctype: str = "webpage",
    chunk_size: int = 1200,
) -> list[IngestRecord]:
    """Process HTML with CHUNKING (like IRS) - MULTIPLE records per page."""
    title, blocks = extract_main_html(str(result.content))
    
    if not blocks:
        LOGGER.warning("No content blocks extracted from %s", result.url)
        return []
    
    # Convert to dict format for chunking
    block_dicts = [{"text": block.text, "tag": block.tag} for block in blocks]
    
    # CHUNK the content with configurable size
    chunks = chunk_blocks(block_dicts, max_chars=chunk_size)
    
    if not chunks:
        LOGGER.warning("No chunks produced from %s", result.url)
        return []
    
    doc_id = slugify(title or doc_hint or result.url)
    year = infer_year(title) or infer_year(result.url)
    doctype = determine_doctype(result.url) or default_doctype

    # Create multiple records (one per chunk) with DEDUPLICATION (like IRS)
    records: list[IngestRecord] = []
    seen_hashes: set[str] = set()
    
    for idx, chunk in enumerate(chunks):
        # Deduplicate using SHA1 hash (like IRS)
        digest = hashlib.sha1(chunk.text.encode("utf-8")).hexdigest()
        if digest in seen_hashes:
            continue
        seen_hashes.add(digest)
        
        records.append(
            make_record(
                doc_id=doc_id,
                url=result.url,
                title=title or doc_hint or result.url,
                year=year,
                section=chunk.section,  # Track sections (like IRS)
                chunk_id=idx,
                text=chunk.text,
                doctype=doctype,
                authority=authority,
            )
        )
    
    return records


def process_pdf(
    result: FetchResult, 
    *, 
    doc_hint: Optional[str] = None,
    authority: str = "consumerfinance.gov",
    default_doctype: str = "publication",
    chunk_size: int = 1200,
) -> list[IngestRecord]:
    """Process PDF with CHUNKING (like IRS) - creates chunked records."""
    blocks = pdf_to_blocks(bytes(result.content))
    
    if not blocks:
        LOGGER.warning("No content blocks from PDF %s", result.url)
        return []
    
    # Convert to dict format for chunking
    block_dicts = [{"text": block.text, "page": block.page} for block in blocks]
    
    # CHUNK the PDF content with configurable size
    chunks = chunk_blocks(block_dicts, max_chars=chunk_size)
    
    doc_id = slugify(doc_hint or result.url.split("/")[-1])
    year = infer_year(result.url)
    title = doc_hint or result.url.split("/")[-1]
    doctype = determine_doctype(result.url) or default_doctype
    
    # Create multiple records with deduplication (like IRS)
    records: list[IngestRecord] = []
    seen_hashes: set[str] = set()
    
    for idx, chunk in enumerate(chunks):
        digest = hashlib.sha1(chunk.text.encode("utf-8")).hexdigest()
        if digest in seen_hashes:
            continue
        seen_hashes.add(digest)
        
        records.append(
            make_record(
                doc_id=doc_id,
                url=result.url,
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
    
    return records


def write_local_ndjson(path: Path, records: list[IngestRecord]) -> None:
    """Write records to local ndjson file."""
    # Handle long paths
    parts = []
    for part in path.parts:
        if len(part) > 200:
            parts.append(hashlib.md5(part.encode()).hexdigest())
        else:
            parts.append(part)
    
    path = Path(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


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
    """Main ingestion orchestrator with link following (1-level depth only)."""
    config = load_config(config_path)
    
    # Load config values
    seeds: list[str] = config.get("seeds", [])
    allow_domains: list[str] = config.get("allow_domains", [])
    authority: str = config.get("authority", "consumerfinance.gov")
    default_doctype: str = config.get("default_doctype", "webpage")
    chunk_size: int = config.get("chunk_size", 1200)  # Get chunk size from config
    
    # Link following config
    link_allow_patterns: list[str] = config.get("link_allow_patterns", [])
    link_deny_patterns: list[str] = config.get("link_deny_patterns", [])
    
    # Filter and limit seeds
    seeds = filter_allowed(seeds, allow_domains)
    if max_pages is None:
        max_pages = config.get("max_pages")
    
    # Track all URLs to process and already seen
    urls_to_process = list(seeds)
    seen_urls: Set[str] = set(seeds)
    seed_urls: Set[str] = set(seeds)  # Track original seeds for depth control
    
    # Limit initial seeds if max_pages specified
    if max_pages is not None:
        urls_to_process = urls_to_process[:int(max_pages)]
        seen_urls = set(urls_to_process)
        seed_urls = set(urls_to_process)

    LOGGER.info("Starting with %d seed URLs from ConsumerFinance.gov", len(urls_to_process))
    LOGGER.info("Link following mode: 1-level depth (only from seed pages)")
    LOGGER.info("Chunking mode: ENABLED (~%d chars per chunk, like IRS)", chunk_size)

    # Process each URL
    success_count = 0
    failure_count = 0
    total_processed = 0
    total_records = 0
    
    while urls_to_process and (max_pages is None or total_processed < max_pages):
        url = urls_to_process.pop(0)
        total_processed += 1
        
        # Mark if this is a seed URL or discovered URL
        is_seed = url in seed_urls
        url_type = "SEED" if is_seed else "DISCOVERED"
        
        LOGGER.info("[%d/%s] Fetching %s", total_processed, url_type, url)
        
        try:
            result = fetch_url(url)
        except Exception as exc:
            LOGGER.error("FAILED to fetch %s: %s", url, exc)
            failure_count += 1
            continue

        # Extract records from this page (NOW WITH CONFIGURABLE CHUNKING!)
        records = process_fetch_result(
            result, 
            authority=authority, 
            default_doctype=default_doctype,
            chunk_size=chunk_size,  # Pass chunk size from config
        )
        
        if not records:
            LOGGER.warning("WARNING: No records produced for %s", url)
            failure_count += 1
        else:
            # Write to local filesystem - flat structure
            slug = slugify(records[0].title or url)
            
            # Truncate slug if too long
            if len(slug) > 200:
                slug_hash = hashlib.md5(slug.encode()).hexdigest()[:8]
                slug = slug[:190] + "_" + slug_hash
            
            local_path = output_dir / f"{slug}.ndjson"  # ← FLAT STRUCTURE
            write_local_ndjson(local_path, records)
            LOGGER.info("SUCCESS: Wrote %d records (chunked) to %s", len(records), local_path)
            
            total_records += len(records)

            # Upload to GCS if configured
            if bucket and gcs_prefix:
                gcs_path = f"{gcs_prefix.rstrip('/')}/{slug}.ndjson"  # ← FLAT STRUCTURE
                upload_file_to_gcs(local_path, bucket, gcs_path)
            
            success_count += 1
        
        # Extract and follow links ONLY from seed pages (depth 1 only)
        if is_seed and should_follow_links(url, config) and result.is_html:
            LOGGER.info("LINKS: Extracting links from SEED page: %s", url)
            links = extract_links(str(result.content), url)
            filtered_links = filter_links(links, link_allow_patterns, link_deny_patterns)
            
            new_links = filtered_links - seen_urls
            if new_links:
                LOGGER.info("FOUND: %d new links to follow (depth 1 only)", len(new_links))
                urls_to_process.extend(sorted(new_links))
                seen_urls.update(new_links)
        elif not is_seed:
            LOGGER.debug("SKIP: Skipping link extraction (not a seed page)")
    
    LOGGER.info("=" * 60)
    LOGGER.info("Summary: %d pages succeeded, %d failed out of %d total", 
                success_count, failure_count, total_processed)
    LOGGER.info("Total records created: %d (chunked at %d chars)", total_records, chunk_size)
    LOGGER.info("Total URLs discovered: %d", len(seen_urls))
    LOGGER.info("Seed URLs: %d", len(seed_urls))
    LOGGER.info("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Normalize consumer finance documents for FinWhiz ingest"
    )
    parser.add_argument(
        "--config", 
        type=Path, 
        default=Path(__file__).parent / "consumer_finance_config.yaml",
        help="Path to consumer_finance_config.yaml"
    )
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("data/consumer_finance"), 
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