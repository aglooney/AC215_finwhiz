# Embedding Utilities

This container builds and publishes embeddings for the FinWhiz RAG corpus.

## Responsibilities

- Load raw text chunks (IRS, FINRA, Consumer Finance, local PDFs) from the webscraping pipelines.
- Generate vector embeddings using the configured sentence-transformer (`jinaai/jina-embeddings-v3`).
- Persist embeddings to a local Chroma store and/or upload the snapshot to GCS so the LLM container can sync it.

## Key Files

| File | Purpose |
|------|---------|
| `embedding.py` | Entrypoint script for creating/populating the Chroma collection. |
| `Dockerfile` | Defines the runtime for batch embedding jobs. |
| `pyproject.toml` / `uv.lock` | Dependencies (managed with `uv`). |

## Running

The embedding job is run on demand (not part of the default compose stack):

```bash
docker build -t finwhiz_embedder -f src/embedder/Dockerfile .
docker run --rm \
  -v "$(pwd)":/app \
  finwhiz_embedder \
  python embedding.py
```

> Ensure your `.env` and `secrets/` folders are available so the script can push the resulting Chroma snapshot back to GCS.

## Output

- Local Chroma directory: `src/chroma_storage/`
- Optional upload: `gs://fw_ws/chroma_storage/...`

These outputs are consumed by the LLM service (`ensure_chroma_local`) during startup.
