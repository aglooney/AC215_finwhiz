# FinWhiz LLM / RAG Service

This container hosts the FinWhiz Large Language Model API. It combines three responsibilities:

1. **Context Retrieval** – embeds incoming queries with `jinaai/jina-embeddings-v3` and fetches relevant documents from the local ChromaDB cache (synced from GCS).
2. **Agent Integration** – calls the agentic user-data service to pull session chat history and extracted W‑2 fields.
3. **LLM Invocation** – forwards the aggregated context to Vertex AI (`gemini-2.5-pro`) and returns the answer + context for auditing.

## Key Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Builds the runtime (FastAPI + embeddings + Vertex AI SDK). |
| `pyproject.toml` / `uv.lock` | Dependency lockfiles (managed with `uv`). |
| `llm_service.py` | FastAPI application (`POST /query`, `GET /health`). |
| `chroma_utils.py` | Syncs the Chroma snapshot from GCS on container start. |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `VERTEXAI_CREDENTIALS` | Path (inside the container) to the Vertex AI service-account JSON. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Same as above (kept for compatibility). |
| `GCS_BUCKET` | Bucket holding the Chroma snapshot (default `fw_ws`). |
| `GCS_PREFIX` | Prefix for the Chroma backup (default `chroma_storage`). |
| `CHROMA_PATH` | Local path used by Chroma (default `/app/src/chroma_storage`). |
| `COLLECTION_NAME` | Chroma collection name (`finwhiz_docs`). |
| `AGENT_URL` | Base URL of the agent service (`http://agent:8010`). |

All secrets (service-account JSON) live in `secrets/` on the host and are mounted/read via environment variables in `docker-compose.yml`.

## Running Locally

```bash
# from repo root
docker-compose up --build postgres llm agent
```

The service exposes:
- `POST /query` – accepts `{"query": "...", "session_id": "...", "top_k": 5}` and returns `{"answer": "...", "context": "..."}`.
- `GET /health` – readiness probe used by Docker Compose.

## Testing

1. Ensure a Chroma snapshot exists in GCS (`fw_ws/chroma_storage/...`).
2. Start the stack: `docker-compose up --build postgres llm agent`.
3. Use the CLI or script:
   ```bash
   ./test_full_pipeline.sh  # uploads W‑2, logs chat, queries the LLM
   ```
4. Inspect logs: `docker-compose logs llm`.

Sample output and Milestone 2 evidence are archived in `reports/ms2/`.
