# FinWhiz

FinWhiz is our end-to-end, Retrieval-Augmented Generation-Large Language Model (RAG-LLM) platform that delivers financial education in two modes:

1. **General Knowledge** – the chatbot retrieves curated public resources (FINRA, IRS, Consumer Finance, etc.) through a vector database to provide additional context and augment LLM responses.
2. **Personalized Guidance** – users can upload their own documents (currently supporting W‑2s). An agentic service extracts key features, stores them securely, and blends that context with RAG results so answers stay user-specific.

The system is fully containerized and orchestrated with Docker Compose to support repeatable deployments and testing.

Visit the ```reports/milestone2/README.md``` to see logs for milestone 2.

---

## Repository Map

| Component | Path | Description | Documentation |
|-----------|------|-------------|----------------|
| **Agent Service** | `src/agentic_user_data_processing/` | FastAPI service that manages chat sessions, stores uploaded W‑2s, and surfaces structured context for the LLM. | [README](src/agentic_user_data_processing/README.md) |
| **LLM / RAG Service** | `src/llm/` | Hosts Gemini 2.5 via Vertex AI, retrieves Chroma context, merges agent data, and answers queries. | [README](src/llm/README.md) |
| **Query Client** | `src/query_client/` | Interactive CLI wrapper used for manual QA and demos. | [README](src/query_client/README.md) |
| **Embedding Utilities** | `src/embedder/` | Scripts for building and uploading document embeddings to Chroma / GCS. | [README](src/embedder/README.md) |
| **Webscraping Pipelines** | `src/webscraping/` | Data ingestion + chunking pipelines for public financial sources. | [README](src/webscraping/README.md) |
| **GCS Utilities** | `src/gcp_storage/` | Shared GCS helper library and upload scripts for scraped data. | [README](src/gcp_storage/README.md) |
| **Synthetic Data** | `src/synthetic_data/` | W‑2 generator container used for testing the agentic workflow testing. | [README](src/synthetic_data/README.md) |
| **Milestone Reports** | `reports/` | Documentation and logs for milestones (e.g., pipeline runs). | [Milestone 2](reports/milestone2/README.md) |

---

## Quick Start

### Prerequisites
- Docker Desktop (or Docker Engine) + docker-compose plugin  
- GCP service account with access to Vertex AI and the configured GCS buckets with local copies of JSON keys stored in `secrets/`

### Environment Configuration
Create a `.env` file at the repository root (see `.env.example` for a template). Minimum variables:

```bash
GOOGLE_APPLICATION_CREDENTIALS=secrets/<vertexai-service-account>.json
VERTEXAI_CREDENTIALS=secrets/<vertexai-service-account>.json
GCS_BUCKET=fw_ws
GCS_PREFIX=chroma_storage
DATABASE_URL=postgresql+psycopg://finwhiz:finwhiz@postgres:5432/finwhiz
AGENT_URL=http://agent:8010
LLM_URL=http://llm:8001
```

Put matching credentials for any additional buckets into `secrets/`.

### Run the Pipeline
```bash
docker-compose up --build
```
This composes:
- **postgres** – session + document metadata  
- **llm** – RAG/LLM API with Vertex AI + Chroma  
- **agent** – chat + W‑2 ingestion microservice  
- **query_client** – interactive user interface

Once the services are healthy you can open a second terminal to validate the stack:
```bash
bash test_full_pipeline.sh
```
The script creates a session, uploads a synthetic W‑2, posts a user message, and queries the LLM. Sample logs are archived in `reports/milestone2/test_full_pipeline.log`.

Additional utilities:
```bash
# Verify GCS connectivity
cd src/gcp_storage
python test_gcs.py
```

---

## Application Mock-up

An interactive Figma prototype illustrates the planned UI flow (chat + document upload + backend context panels). The link and screenshots are documented in `reports/milestone2/README.md`.

---

## Milestone 2 Artifacts

- **Containers** – Each major service has a dedicated Dockerfile and `pyproject.toml`.
- **Pipeline Proof** – `docker-compose.yaml`, `test_full_pipeline.sh`, and accompanying logs.
- **Reports** – `reports/milestone2/` consolidates testing evidence, instructions, and outstanding TODOs (e.g., screenshot of running containers).
- **Mock-up** – Updated Figma prototype demonstrating chat + upload flow.

See the [Milestone 2 report](reports/milestone2/README.md) for details, test output, and remaining tasks.

---

## Security & Privacy
- User-uploaded documents stay in the `fw_user_uploads` bucket and are referenced by session metadata in Postgres.
- Secrets (service-account keys, env files) are kept outside version control under `secrets/`.
- FinWhiz is an educational tool only—it is **not** a registered financial advisor.

---

## Next Steps
- Add support for additional IRS forms and user-uploaded document types.
- Expand integration tests (full RAG QA with multiple document types).
- Create web-UI and backend.
