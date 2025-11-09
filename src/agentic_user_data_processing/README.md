# Agentic User Data Processing

This package houses the agent microservice that:

- Tracks active chat sessions and message history.
ocker hub- Accepts W-2, 1099, and Fidelity portfolio PDF uploads, stores the raw (flattened) files in GCS, and extracts structured fields via Gemini.
- Serves a compact context object (recent chat summary + document data) so downstream services can personalize responses.

## High-Level Components

- `app.py` — FastAPI entrypoint exposing session/message/document endpoints.
- `db.py` — SQLAlchemy session management and lifecycle hooks.
- `models.py` — Database schema (users, sessions, messages, documents, extracted fields).
- `schemas.py` — Pydantic request/response models.
- `services/` — Helpers for storage, extraction, context assembly, and PDF preprocessing.

## Environment Expectations

Environment variables are loaded via `.env` (see repository root):

- `DATABASE_URL` — SQLAlchemy-compatible Postgres URL.
- `GOOGLE_APPLICATION_CREDENTIALS` — Path to service account JSON (e.g., `secrets/finwhiz-sa.json`).

Secrets belong in the local `secrets/` folder (gitignored) and are mounted into the container at runtime.

## Supported Document Types

The service supports multiple document types per session:

- **W-2 Forms** (`/sessions/{session_id}/w2`) — Employee wage and tax statements
- **1099 Forms** (`/sessions/{session_id}/1099`) — Interest income reports  
- **Portfolio Summaries** (`/sessions/{session_id}/portfolio`) — Fidelity portfolio statements

Each document type is processed independently and made available in the session context.

## Manual Smoke Test

1. Start the agent and Postgres containers:
   ```bash
   docker-compose up --build agent postgres
   ```
2. Create a session:
   ```bash
   SESSION_ID=$(curl -s -X POST http://127.0.0.1:8010/sessions/ \
     -H "Content-Type: application/json" \
     -d '{"user_id": "EXAMPLE-USER-ID"}' | jq -r .id)
   ```
3. Upload documents (the service auto-flattens PDFs using `pdftk`):
   ```bash
   # Upload W-2
   curl -X POST http://127.0.0.1:8010/sessions/$SESSION_ID/w2 \
     -F file=@synthetic_data/w2/outputs/w2_000.pdf
   
   # Upload 1099
   curl -X POST http://127.0.0.1:8010/sessions/$SESSION_ID/1099 \
     -F file=@synthetic_data/int_1099/outputs/1099int_001.pdf
   
   # Upload portfolio
   curl -X POST http://127.0.0.1:8010/sessions/$SESSION_ID/portfolio \
     -F file=@Fidelity_statement.pdf
   ```
4. Fetch the merged context:
   ```bash
   curl http://127.0.0.1:8010/sessions/$SESSION_ID/context
   ```

The response will include `w2_fields`, `form1099_fields`, and `portfolio_fields` with extracted data from each document type.
