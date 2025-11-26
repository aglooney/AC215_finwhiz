# Test Suite Overview

This directory contains every test target executed by the CI workflow. Tests are grouped by scope so you can run only what you need while developing or debugging. We currently have 47% of the code covered by unit tests.

## 1. Unit Tests (`tests/unit`, `src/*/tests`)

- **What they cover**: isolated modules such as the new `gcp_storage` helpers plus package-level unit suites inside each service (`src/llm/tests`, `src/embedder/tests`, etc.).
- **Prereqs**: no external services. Fake credentials are created during CI; locally you can leave `FINWHIZ_TEST_MODE=1` and skip secrets.
- **Run**:
  ```bash
  uv pip install --system pytest pytest-asyncio pytest-cov
  uv pip install --system -e src/llm -e src/embedder -e src/agentic_user_data_processing -e src/query_client -e src/webscraping
  pytest src/llm/tests src/embedder/tests src/agentic_user_data_processing/tests src/query_client/tests src/webscraping/tests tests/unit
  ```

## 2. Integration Tests (`tests/integration`)

- **What they cover**: multi-service flows (e.g., query client upload -> agent -> embedder).
- **Prereqs**: still run in `FINWHIZ_TEST_MODE=1` using fake credentials.
- **Run**:
  ```bash
  pytest tests/integration
  ```

## 3. Cloud-Backed Tests (`tests/cloud`)

- **What they cover**: live GCS, Vertex AI extractors, Cloud SQL CRUD.
- **Prereqs**:
  - Secrets: `VERTEXAI_SERVICE_ACCOUNT_JSON`, `CLOUDSQL_PASSWORD`, `CLOUDSQL_PROXY_JSON`.
  - Cloud SQL proxy running on `127.0.0.1:5432`.
  - Fixture PDFs present in `gs://finwhiz-storage/cloud_testing/` (`w2_000.pdf`, `1099int_001.pdf`, `portfolio_001.pdf`).
- **Run**:
  ```bash
  export VERTEXAI_CREDENTIALS=/path/to/vertex.json
  export GOOGLE_APPLICATION_CREDENTIALS=$VERTEXAI_CREDENTIALS
  ./cloud-sql-proxy finwhiz-ac215:us-central1:finwhiz-cloud-sql --credentials-file=/path/to/proxy.json --port 5432 &
  pytest tests/cloud
  ```

CI automatically fetches the PDFs to `tests/cloud_fixtures/` before running these tests.

## 4. System Test (`tests/system/test_full_pipeline.py`)

- **What it covers**: brings up the `agent`, `llm`, and `cloudsql-proxy` containers (via `docker compose up`) and executes `test_full_pipeline.sh`, which simulates a user session end to end.
- **Prereqs**:
  - Same secrets as cloud tests.
  - Artifact Registry images (`us-central1-docker.pkg.dev/finwhiz-ac215/finwhiz-img/finwhiz:<tag>`) published for `cloudsql-proxy`, `agent`, and `llm`.
  - `RUN_SYSTEM_TESTS=1`.
- **Run**:
  ```bash
  docker compose up -d cloudsql-proxy llm agent
  RUN_SYSTEM_TESTS=1 pytest tests/system
  docker compose down
  ```
  The CI workflow will skip system tests gracefully if Docker fails because of disk limits (logs note the skip and other jobs still finish).

## 6. Tests Coverage

Unit Tests:
![Unit Test Coverage](imgs/unit_tests.jpeg)

Cloud Backend Integration Tests:
![Integration Test Coverage](imgs/integration_test.jpeg)

Full System Tests still in progress
