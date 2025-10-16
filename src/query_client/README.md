# Query Client (Interactive CLI)

This container provides a lightweight terminal interface for talking to FinWhiz. It is used for manual QA, demos, and exploratory testing during Milestone 2.

## Features

- Starts an interactive prompt (`interactive_query.py`) that forwards user questions to the LLM service.
- Automatically creates a session with the agent service and logs both user and assistant turns.
- Relies on the agent service to persist chat history and W‑2 uploads, so the LLM receives full context.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LLM_URL` | Base URL for the LLM service (default `http://llm:8001`). |
| `AGENT_URL` | Base URL for the agentic user-data service (default `http://agent:8010`). |

These are set in `docker-compose.yml` and inherit additional configuration from the root `.env`.

## Running

```bash
docker-compose up --build postgres llm agent query_client
```

The `query_client` container attaches to your terminal. Example usage:

```
Started session 9e7a... for user f2bc...

Enter your query (or 'exit' to quit): What did I upload earlier?
```

The CLI forwards the query to `/query` and prints the LLM answer. It will continue prompting until you type `exit`.

## Testing Workflow

- Upload a W‑2 using the companion script (`./test_full_pipeline.sh`) or the curl commands documented in `reports/ms2/`.
- Switch to the CLI terminal and ask follow-up questions (“Summarize my W‑2”, “What federal tax was withheld?”).
- Inspect the agent context via `curl http://127.0.0.1:8010/sessions/<session_id>/context` to confirm chat history is logged.
