# Webscraping & Ingestion Pipelines

This package collects the data-ingestion workflows that populate the FinWhiz knowledge base. Each ingestion target (IRS, FINRA, Investor.gov, Consumer Finance) shares a common structure for crawling, parsing, chunking, and exporting content to GCS.

## Layout

- `ingest_shared/` – Consolidated v2 pipelines (Python packages per source with Typer CLIs).
- `ingest_shared_v1/` – Legacy scripts kept for reference.
- `config/` – Shared configuration defaults (selectors, routing rules, etc.).
- `Dockerfile` + `pyproject.toml` – Container definition and dependencies.

Typical pipeline stages:

1. **Crawl** – collect raw HTML/PDF using the source-specific crawler (`src/crawl/run_crawl.py`).
2. **Transform** – clean and chunk the documents (`src/transform/run_transform.py`, `chunkers.py`).
3. **Export** – write chunked JSON/NDJSON locally and optionally upload to GCS (`to_gcs.py`).

## Running an Ingestion Job

Example (FINRA):
```bash
docker build -t finwhiz_webscrape -f src/webscraping/Dockerfile .
docker run --rm \
  -v "$(pwd)":/app \
  finwhiz_webscrape \
  python -m webscraping.ingest_shared.finra.src.crawl.run_crawl
```
Follow with the transform + export commands documented in the source-specific README (see the `ingest_shared/<source>/` subdirectories).

Outputs ultimately land in `data/` locally and `gs://fw_ws/...` in the cloud, where they are picked up by the embedding job.

## Notes

- Pipelines now import shared helpers from `ingest_shared/shared/` to minimize duplication.
- The container is not part of the default docker-compose stack; it is invoked manually when new data needs to be collected.
