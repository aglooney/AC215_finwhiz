# Milestone 2 Report – FinWhiz

This report summarizes the artifacts delivered for **Milestone 2: MLOps Infrastructure**.

## 1. Infrastructure Overview

| Component | Status | Notes |
|-----------|--------|-------|
| Dockerized services | ✅ | `postgres`, `llm`, `agent`, `query_client`, `synthetic_data`, `webscraping`, `gcp_storage`, `embedder`. |
| End-to-end pipeline | ✅ | `docker-compose up --build postgres llm agent query_client` + `./test_full_pipeline.sh`. |
| Vertex AI integration | ✅ | LLM container uses `gemini-2.5-pro` via service-account credentials. |
| Chroma vector store | ✅ | Snapshot synced from GCS (`fw_ws/chroma_storage`). |
| Agentic user data | ✅ | W‑2 ingestion with auto-flatten, Postgres session store. |
| UI mock-up | ✅ | Clickable Figma prototype (link shared in stakeholder deck). |
| Environment screenshot | ⭕️ TODO | Capture Docker Desktop / terminal view showing running containers. |

## 2. How to Run the Pipeline

```bash
# from repo root
docker-compose up --build postgres llm agent query_client

# in a second terminal
./test_full_pipeline.sh
```

The script will:
1. Create a session (`POST /sessions/`).
2. Upload a synthetic W‑2 (`POST /sessions/<id>/w2`).
3. Log a user message (`POST /sessions/<id>/messages`).
4. Retrieve the combined agent context.
5. Query the LLM (`POST /query`).

See [`test_full_pipeline.md`](test_full_pipeline.md) for sample output showing extracted W‑2 fields and the LLM’s personalized summary.

## 3. Additional Tests

- **GCS Connectivity** – `src/gcp_storage/test_gcs.py` verifies upload/list/download/delete against the configured bucket.
- **Manual CLI QA** – use the query-client console (`docker-compose` terminal) to ask follow-up questions and confirm the agent persists chat history.

## 4. Mock-up / UI Status

- Figma prototype demonstrates the planned chat + upload experience.  
- Info icons and overlays explain how each UI event maps to backend calls (agent service, RAG retrieval).
- Link available in the team’s stakeholder presentation (also referenced in the milestone slide deck).

## 5. Deliverables Checklist

- [x] Virtual environment & container setup instructions (root README + container READMEs).
- [x] Containerized RAG pipeline with documentation.
- [x] Logs proving end-to-end run (`test_full_pipeline.log`).
- [x] UI mock-up updated for Milestone 2.
- [ ] Screenshot of running environment (to be attached before submission).

## 6. Next Actions

1. Capture and archive the required Docker/terminal screenshot.
2. Extend automated testing (integration tests for multiple document types).
3. Continue UI build-out toward a thin working prototype.
