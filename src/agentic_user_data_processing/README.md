# Agentic User Data Processing

This package houses the agent microservice that:

- Tracks active chat sessions and message history.
- Accepts W-2 PDF uploads, stores the raw (flattened) files in GCS, and extracts structured fields via Gemini.
- Serves a compact context object (recent chat summary + W-2 data) so downstream services can personalize responses.

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
3. Upload a PDF (the service auto-flattens using `pdftk`):
   ```bash
   curl -X POST http://127.0.0.1:8010/sessions/$SESSION_ID/w2 \
     -F file=@synthetic_data/w2/outputs/w2_000.pdf
   ```
4. Fetch the merged context:
   ```bash
   curl http://127.0.0.1:8010/sessions/$SESSION_ID/context
   ```

The `w2_fields` block should now contain populated values even for fillable forms.
