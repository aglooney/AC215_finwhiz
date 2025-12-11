# Milestone 5: Final Project Delivery – FinWhiz

In this report we summarize the final state of the FinWhiz project for Milestone 5. The focus is on production deployment, CI/CD, ML workflow integration, and public-facing presentation materials.

---

## 1. Production Deployment (GKE + Pulumi)

### 1.1 Deployed Architecture

FinWhiz is deployed to a Google Kubernetes Engine (GKE) cluster using Pulumi:

- **Cluster** – GKE cluster `finwhiz-cluster` with a dedicated node pool (2–3 nodes) and Workload Identity.
- **Namespace** – Kubernetes namespace `finwhiz-namespace` for all app workloads.
- **Services**:
  - `frontend` – React + Nginx UI (port 80 in-cluster, exposed via HTTP(S) Load Balancer).
  - `agent` – FastAPI agentic service (port 8010) for sessions and document uploads.
  - `llm` – FastAPI RAG/LLM service (port 8001) for retrieval + Vertex Gemini calls.
  - `cloudsql-proxy` – sidecar deployment exposing Cloud SQL (Postgres) inside the cluster.
- **Data Stores**:
  - **Cloud SQL** – relational database backing sessions, messages, and document metadata.
  - **GCS** – Chroma snapshot bucket (`fw_ws`), user uploads bucket (`fw_user_uploads`), and DVC remote (`finwhiz-storage`).
  - **Chroma** – vector store running inside the `llm` container, synchronized from GCS on startup.

The current public endpoint for the application is below. (Note: An active billing account may not be linked to FinWhiz to preserve billing costs incurred mainly through usage of CloudSQL).

```text
https://136.116.192.125.sslip.io
```

Architecture diagrams for this deployment are captured in:

- `reports/milestone5/Solution_Architecture_Diagram.png`
- `reports/milestone5/technical_architecture_diagram.png`

### 1.2 Pulumi Infrastructure Code

Infrastructure and deployment are managed as code under `src/deployment`:

- `deploy_images` – Pulumi project that:
  - Builds Docker images for `frontend`, `agent`, `llm`, and `query_client`.
  - Pushes versioned tags to Artifact Registry (`<region>-docker.pkg.dev/.../finwhiz`).
- `deploy_k8s` – Pulumi project that:
  - Creates the VPC network, subnet, NAT, and GKE cluster.
  - Configures Workload Identity and a Kubernetes Service Account (`api-ksa`).
  - Deploys Kubernetes resources (Deployments, Services, Cloud SQL proxy).
  - Configures HTTP(S) Load Balancer and ingress, exporting `app_url`.

Minimal manual deployment flow (for verification, if needed):

```bash
cd src/deployment
sh docker-shell.sh

cd deploy_images
pulumi up --stack dev --refresh -y

cd ../deploy_k8s
pulumi up --stack dev --refresh -y
```

Pulumi outputs include the cluster name, namespace, ingress name, IP address, and final `app_url`.

### 1.3 Scaling and Reliability

Scaling and reliability are provided at the cluster and service levels:

- **Node pool autoscaling** – GKE node pool is configured with `min_node_count=2`, `max_node_count=3`, `auto_repair`, and `auto_upgrade`.
- **Pod scaling** – each service can be scaled using standard Kubernetes commands. Example:

```bash
kubectl scale deployment llm --replicas=3 -n finwhiz-namespace
kubectl get pods -n finwhiz-namespace
```

- **Health checks** – both `agent` and `llm` expose `/health` endpoints used by tests and can be wired into readiness/liveness probes.

These settings allow us to demonstrate basic scaling behavior by adjusting replicas under synthetic load.

---

## 2. CI/CD Pipeline (GitHub Actions)

GitHub Actions is used for linting, testing, and production deployment. Workflows live in `.github/workflows`:

### 2.1 Linting and Tests

- **Python Lint** (`python-lint.yml`)
  - Triggers on pushes and pull requests touching Python sources.
  - Runs `pre-commit run --all-files` (Black, Flake8, and other hooks).

- **Python Tests** (`python-tests.yml`)
  - **Unit tests job**:
    - Installs dependencies with `uv`.
    - Runs service-level unit tests:
      - `src/llm/tests`
      - `src/embedder/tests`
      - `src/agentic_user_data_processing/tests`
      - `src/query_client/tests`
      - `src/webscraping/tests`
  - **Integration tests job**:
    - Depends on unit tests.
    - Runs cross-service integration tests under `tests/integration`.
    - When GCP secrets are configured, runs:
      - Cloud-backed tests under `tests/cloud` (GCS, Vertex, Cloud SQL via Cloud SQL Proxy).
  - System tests are scaffolded under `tests/system` and wired into the workflow, but are currently disabled in CI to avoid quota and image-size issues. They can be executed locally using `docker-compose` when needed.

Test coverage is collected with `pytest` and `pytest-cov`. Latest GitHub Actions results: unit-only coverage is ~57%, and combined unit + integration suites are above 60%, satisfying the Milestone 5 target of **≥ 60% line coverage** across services.

Below are the code areas that are not covered by testing: 
- Pulumi deployment code under src/deployment/
- Some webscraping pipelines in src/webscraping/ingest_shared/* 
- Fine-tuning scripts in src/llm/finetuning/ 
- Synthetic data generators beyond basic smoke tests

### 2.2 Deployment Workflow

- **Deploy** (`deploy.yml`)
  - Triggers on:
    - `push` to `main`
    - Manual `workflow_dispatch`
  - Steps:
    - Checks out the repository and installs Python and `uv`.
    - Installs Pulumi CLI.
    - Authenticates to GCP using the `VERTEXAI_SERVICE_ACCOUNT_JSON` secret.
    - Ensures the Pulumi state bucket exists in GCS.
    - Installs deployment dependencies under `src/deployment`.
    - Logs into the Pulumi backend (`gs://finwhiz-ac215-pulumi-state-bucket`).
    - Optionally primes `kubectl` for the cluster.
    - Runs `src/deployment/deploy.sh`, which:
      - Builds and pushes images via the `deploy_images` Pulumi stack.
      - Applies Kubernetes changes via the `deploy_k8s` Pulumi stack.

A successful merge to `main` results in a fresh build and rollout to the GKE cluster with no additional manual steps.

---

## 3. ML Workflow and Model Management

The ML workflow for FinWhiz combines data preprocessing, fine-tuning, evaluation, and selective deployment.

### 3.1 Data and Versioning

- **Training data** – FIQA financial QA dataset, tracked with DVC:
  - DVC file: `src/llm/finetuning/data.dvc`
  - Remote: `gs://finwhiz-storage/finetuning_dvc`
- **Scraped financial content** – RAG corpus managed under `src/webscraping` and versioned via DVC (see `reports/milestone4/data_versioning.md`).
- **Buckets**:
  - Fine-tuning datasets and artifacts: stored under `gs://finwhiz-storage/finetuning/...`.
  - Chroma snapshots: stored under `gs://fw_ws/chroma_storage...`.

To reproduce the training data locally:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=secrets/service-account-key.json
dvc pull src/llm/finetuning/data.dvc
```

### 3.2 Training and Evaluation

- **Training script** – `src/llm/finetuning/train_gemini_full.py`:
  - Downloads FIQA from HuggingFace.
  - Converts it to Gemini JSONL format.
  - Uploads train/validation JSONL to GCS.
  - Submits a Gemini 2.5 Flash Lite fine-tuning job using the Vertex AI SDK.
  - Records the tuning job info in `src/llm/finetuning/data/tuning_job_info.json`.

- **Evaluation script** – `src/llm/finetuning/evaluate_tuned_model.py`:
  - Compares the tuned endpoint vs. base Gemini on the FIQA test split.
  - Writes metrics and predictions to `data/evaluation_compare.json`.

- **LLM-as-judge** – `reports/milestone4/llm_judge.py`:
  - Uses Gemini as a judge model to compare tuned vs. base responses.
  - Outputs win/tie/loss statistics and rationales in `reports/milestone4/llm_judge_results.json`.

Details of the fine-tuning experiments, dataset, and evaluation results are documented in `reports/milestone4/model_finetuning.md`.

### 3.3 Retraining and Promotion Strategy

The workflow for ML models is:

1. **Update data** – new FIQA-style data or proprietary datasets are added and tracked via DVC.
2. **Pull & train** – run `train_gemini_full.py` (or a similar training entrypoint) to launch a new tuning job on Vertex AI.
3. **Evaluate** – run `evaluate_tuned_model.py` and the LLM judge to compare tuned vs. base responses.
4. **Gate deployment** – only promote tuned models that:
   - Match or exceed base model accuracy on the test set.
   - Pass qualitative checks via the LLM judge.
5. **Update serving config** – point the LLM service to the tuned endpoint (via configuration or environment variables) while keeping the base model as a fallback.

This loop supports automated or semi-automated retraining triggered by new data or code changes, with validation checks before a model is promoted to production.

---

## 4. Presentation and Showcase Materials

### 4.1 Video and Blog Post

- **Video walkthrough:
  - https://youtu.be/FL_5ymxJkDg
- **Medium blog post:
  - https://medium.com/@gillianschriever_31774/finwhiz-an-ai-financial-education-assistant-for-millennials-and-gen-z-63da72dcc7f0?postPublishedType=repub

### 4.2 Demo Day Materials

- **Live application URL**:

  ```text
  https://136.116.192.125.sslip.io
  ```

- **Slide deck** – video and user demo materials:
  - https://docs.google.com/presentation/d/1XO2t_sbO1JommtVPfW4I4mOQRxzK_md43Igc1eTuA-c/edit?usp=sharing

---

## 5. Known Issues and Next Steps

- **Coverage tracking** – Latest GitHub Actions: unit-only coverage ~57%; combined unit + integration >60% (meets target). Rerun `pytest --cov` after significant changes to keep coverage above the 60% threshold and note any newly uncovered areas.
- **Cloud dependencies and billing** – The deployment depends on GKE, Cloud SQL, GCS, and Vertex AI. If billing credits expire or a billing account changes, re-enable billing and re-provision the cluster/load balancer (public URL may change).
- **System tests in CI** – Full system tests are wired into the workflow but disabled by default to avoid resource limits; they can be run locally when deeper end-to-end validation is needed.

These items are tracked for future refinement but do not affect the core Milestone 5 deliverables (production deployment, CI/CD, ML workflow wiring, and public communication artifacts).
