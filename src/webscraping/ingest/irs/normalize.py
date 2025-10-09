"""Driver for IRS document ingestion and normalization."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse

import yaml

from .chunk import chunk_blocks
from .fetch import FetchResult, fetch_url
from .parse_html import extract_main_html
from .parse_pdf import pdf_to_blocks
from .schema import IngestRecord, make_record
from .write_gcs import write_ndjson_gcs

LOGGER = logging.getLogger(__name__)


def infer_year(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    match = re.search(r"(20\d{2})", value)
    return int(match.group(1)) if match else None


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "document"


def determine_doctype(url: str) -> str:
    url_lower = url.lower()
    if "instructions" in url_lower:
        return "instruction"
    if any(token in url_lower for token in ("publication", "pub")):
        return "publication"
    return "webpage"


def process_fetch_result(result: FetchResult, *, doc_hint: Optional[str] = None) -> list[IngestRecord]:
    if result.is_html or isinstance(result.content, str):
        return process_html(result, doc_hint=doc_hint)
    if result.is_pdf or isinstance(result.content, (bytes, bytearray)):
        return process_pdf(result, doc_hint=doc_hint)
    LOGGER.warning("Unsupported content type for %s (%s)", result.url, result.content_type)
    return []


def process_html(result: FetchResult, *, doc_hint: Optional[str] = None) -> list[IngestRecord]:
    title, blocks = extract_main_html(str(result.content))
    block_dicts = [{"text": block.text, "tag": block.tag} for block in blocks]
    chunks = chunk_blocks(block_dicts)

    doc_id = slugify(title or doc_hint or result.url)
    year = infer_year(title) or infer_year(result.url)
    doctype = determine_doctype(result.url)

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
                title=title or doc_hint or result.url,
                year=year,
                section=chunk.section,
                chunk_id=idx,
                text=chunk.text,
                doctype=doctype,
            )
        )
    return records


def process_pdf(result: FetchResult, *, doc_hint: Optional[str] = None) -> list[IngestRecord]:
    blocks = pdf_to_blocks(bytes(result.content))
    block_dicts = [{"text": block.text, "page": block.page} for block in blocks]
    chunks = chunk_blocks(block_dicts)

    doc_id = slugify(doc_hint or result.url.split("/")[-1])
    year = infer_year(result.url)
    title = doc_hint or result.url.split("/")[-1]
    doctype = determine_doctype(result.url)

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
                page=chunk.start_page,
            )
        )
    return records


def write_local_ndjson(path: Path, records: Iterable[IngestRecord]) -> None:
    serialized = "\n".join(json.dumps(record.to_dict(), ensure_ascii=False) for record in records)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def filter_allowed(seeds: list[str], allow_domains: list[str]) -> list[str]:
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


def ingest_from_config(config_path: Path, *, output_dir: Path, bucket: Optional[str],
                       gcs_prefix: Optional[str], max_pages: Optional[int] = None) -> None:
    config = load_config(config_path)
    seeds: list[str] = config.get("seeds", [])
    allow_domains: list[str] = config.get("allow_domains", [])
    seeds = filter_allowed(seeds, allow_domains)

    if max_pages is None:
        max_pages = config.get("max_pages")

    if max_pages is not None:
        seeds = seeds[: int(max_pages)]

    for url in seeds:
        LOGGER.info("Fetching %s", url)
        try:
            result = fetch_url(url)
        except Exception as exc:  # pragma: no cover - network failures handled at runtime
            LOGGER.error("Failed to fetch %s: %s", url, exc)
            continue

        records = process_fetch_result(result)
        if not records:
            LOGGER.warning("No records produced for %s", url)
            continue

        slug = slugify(records[0].title or url)
        year = records[0].year or "unknown"
        local_path = output_dir / slug / str(year) / f"{slug}.ndjson"
        write_local_ndjson(local_path, records)
        LOGGER.info("Wrote %d records to %s", len(records), local_path)

        if bucket and gcs_prefix:
            gcs_path = f"{gcs_prefix.rstrip('/')}/{slug}/{year}/{slug}.ndjson"
            LOGGER.info("Uploading %s to gs://%s/%s", slug, bucket, gcs_path)
            write_ndjson_gcs(bucket, gcs_path, (record.to_dict() for record in records))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize IRS documents for FinWhiz ingest")
    parser.add_argument("--config", type=Path, default=str(Path(__file__).parent/"crawl_config.yaml"), help="Path to crawl_config.yaml")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/tmp"), help="Directory to store NDJSON output"
    )
    parser.add_argument("--bucket", type=str, default=None, help="Optional GCS bucket name")
    parser.add_argument(
        "--gcs-prefix", type=str, default=None, help="Path prefix inside the GCS bucket"
    )
    parser.add_argument(
        "--max-pages", type=int, default=None, help="Override maximum pages from config"
    )
    parser.add_argument(
        "--log-level", type=str, default="INFO", help="Logging verbosity"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    ingest_from_config(
        args.config,
        output_dir=args.output_dir,
        bucket=args.bucket,
        gcs_prefix=args.gcs_prefix,
        max_pages=args.max_pages,
    )


if __name__ == "__main__":
    main()
