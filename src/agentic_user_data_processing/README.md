# Agentic User Data Processing

This package houses the agent microservice that:

- Tracks active chat sessions and message history.
- Accepts W-2 PDF uploads, stores the raw files in GCS, and extracts structured fields via Gemini.
- Serves a compact context object (recent chat summary + W-2 data) so downstream services can personalize responses.

## High-Level Components

- `app.py` — FastAPI entrypoint exposing session/message/document endpoints.
- `db.py` — SQLAlchemy session management and lifecycle hooks.
- `models.py` — Database schema (users, sessions, messages, documents, extracted fields).
- `schemas.py` — Pydantic request/response models.
- `services/` — Helpers for storage, extraction, and context assembly.

## Environment Expectations

Environment variables are loaded via `.env` (see repository root):

- `DATABASE_URL` — SQLAlchemy-compatible Postgres URL.
- `GOOGLE_APPLICATION_CREDENTIALS` — Path to service account JSON (e.g., `secrets/finwhiz-sa.json`).
- `USER_UPLOAD_BUCKET` — GCS bucket for user documents (e.g., `fw_user_uploads`).

Secrets belong in the local `secrets/` folder (gitignored) and are mounted into the container at runtime.
