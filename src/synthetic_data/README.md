# Synthetic W-2 Generator

Containerized pipeline module for producing synthetic W-2 PDFs from the IRS fillable template. The generated records let the team exercise FinWhiz’s upload flow without touching real personal data.

## Layout
- `assets/` – fillable template PDF plus field metadata (`copy_b_field_map.yaml`).
- `src/synthetic_w2/` – generator, PDF filler, and Typer CLI.
- `tests/` – unit/integration tests (placeholder for now).
- `outputs/` – sample artifacts (ignored by git).

## Usage (local dev)
```bash
uv sync --project synthetic_data/w2
PYTHONPATH=synthetic_data/w2/src \
  uv run --project synthetic_data/w2 -m synthetic_w2 --count 3 --seed 42 --output-dir synthetic_data/w2/outputs
```

Each synthetic employee produces a paired `w2_<idx>.json` (ground-truth structure) and `w2_<idx>.pdf` (filled Copy B). If `pdftk` is installed the PDF is flattened; otherwise the CLI logs a warning and leaves form fields editable.

## Container usage
Build from the project root so the Docker build context includes the repository:
```bash
docker build -t synthetic_data -f src/synthetic_data/Dockerfile .
```
Generate documents (override CLI args as needed). Mount a host directory if you want the PDFs outside the container:
```bash
docker run --rm --ti \
  -v "$(pwd)":/app \
  synthetic_data \
```

The container entrypoint is the Typer CLI (`python -m synthetic_w2`), so any arguments after the image name are forwarded.

## Next steps
- Flesh out unit tests for the generator and PDF filler.
- Wire the container into `docker-compose` / `make` targets as the broader pipeline evolves.
- Connect the generated artifacts to the ingestion/RAG pipeline when ready.
