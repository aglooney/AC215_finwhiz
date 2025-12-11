# FinWhiz

FinWhiz is our end-to-end, Retrieval-Augmented Generation-Large Language Model (RAG-LLM) platform that delivers financial education in two modes:

1. **General Knowledge** – the chatbot retrieves curated public resources (FINRA, IRS, Consumer Finance, etc.) through a vector database to provide additional context and augment LLM responses.
2. **Personalized Guidance** – users can upload their own documents (currently supporting W‑2s, 1099 forms, and Fidelity portfolio summaries). An agentic service extracts key features, stores them securely, and blends that context with RAG results so answers stay user-specific.

The deployed system includes a production web UI with a user-specific dashboard (portfolio holdings plus live yfinance market data) and synthetic portfolio data for comprehensive testing.

The system is fully containerized and orchestrated with Docker Compose to support repeatable deployments and testing.

---

## Repository Map

| Component | Path | Description | Documentation |
|-----------|------|-------------|----------------|
| **Agent Service** | `src/agentic_user_data_processing/` | FastAPI service that manages chat sessions, stores uploaded W‑2s/1099s/portfolios, and surfaces structured context for the LLM. | [README](src/agentic_user_data_processing/README.md) |
| **LLM / RAG Service** | `src/llm/` | Hosts Gemini 2.5 via Vertex AI, retrieves Chroma context, merges agent data, and answers queries. | [README](src/llm/README.md) |
| **Query Client** | `src/query_client/` | Interactive CLI wrapper used for manual QA and demos. | [README](src/query_client/README.md) |
| **Embedding Utilities** | `src/embedder/` | Scripts for building and uploading document embeddings to Chroma / GCS. | [README](src/embedder/README.md) |
| **Webscraping Pipelines** | `src/webscraping/` | Data ingestion + chunking pipelines for public financial sources. | [README](src/webscraping/README.md) |
| **GCS Utilities** | `src/gcp_storage/` | Shared GCS helper library and upload scripts for scraped data. | [README](src/gcp_storage/README.md) |
| **Synthetic Data** | `src/synthetic_data/` | W‑2 and 1099 generator containers used for testing the agentic workflow. | [README](src/synthetic_data/README.md) |
| **Milestone Reports** | `reports/` | Documentation and logs for milestones (e.g., pipeline runs). | [Milestone 2](reports/milestone2/README.md), [Milestone 4](reports/milestone4/README.md), [Milestone 5](reports/milestone5/README.md) |

---

## Prerequisites and Setup

At a high level you will need:
- Docker Desktop (or Docker Engine) with the docker-compose plugin.
- A GCP project with service-account credentials that can access Vertex AI and the configured GCS buckets.
- Node.js 20+ (for local frontend development).

See `QUICKSTART.md` for detailed environment variables, how to bring up the stack, and how to run basic validation tests end to end.

## Usage Details and Examples

- **General education question**  
  Open the app in your browser (local dev or the public URL), start a new session, and ask a question like:  
  “What is a Roth IRA and how is it different from a traditional 401(k)?”  
  The LLM service uses the financial knowledge base (RAG) to return an educational answer with citations.

- **Personalized guidance from uploaded documents**  
  From the “Upload Documents” section in the UI, upload a W‑2 or 1099 PDF, wait for processing to complete, then ask:  
  “Based on the W‑2 I just uploaded, what is my total taxable wages and how much federal tax was withheld?”  
  The agent service extracts structured fields, and the LLM uses them to tailor the explanation to your document.

- **Portfolio dashboard and live market view**  
  Complete the onboarding flow (age, retirement age, risk tolerance, goal), upload your Fidelity account summary PDF, and navigate to the dashboard.  
  Review the suggested allocation (stocks/bonds/cash), then open the portfolio tab to see your holdings with live yfinance prices and day‑to‑day performance.  
  You can then ask the chat: “Looking at my current holdings, where am I most concentrated and what does that mean from a diversification perspective?”

### Testing
To mirror CI locally:
- `pytest` for unit tests
- `pytest --cov=src --cov=tests --cov-report=term-missing` for coverage (latest GA: unit ~57%, combined >60%)

### Linting & Formatting (Black + Flake8 via pre-commit)
We pin formatter/linter versions with [pre-commit](https://pre-commit.com), which keeps local runs in sync with CI.

1. Install tooling once per machine:
   ```bash
   pip install pre-commit
   pre-commit install
   pre-commit install --hook-type pre-push
   ```
   The default hook runs on `git commit`; the additional `pre-push` hook re-checks the whole repo before uploading.

2. To run manually (e.g., before opening a PR):
   ```bash
   pre-commit run --all-files
   ```

3. When pushing:
   ```bash
   git add <files>
   git commit -m "Message"
   git push
   ```
   The `pre-push` hook executes Black/Flake8 inside pre-commit’s managed virtualenvs. Fix any reported issues, re-stage, and push again. GitHub Actions also runs `pre-commit run --all-files` to keep CI aligned with local checks.

---

## Deployment Instructions (GKE + Pulumi + CI/CD)

FinWhiz is deployed to Google Kubernetes Engine using Pulumi and GitHub Actions. (Note: An active billing account may not be currently tied to FinWhiz to avoid large billing costs mainly incured by CloudSQL).

### Public URL

The public endpoint for the production deployment is:

```text
https://136.116.192.125.sslip.io
```

### Deployment Options

**Option 1 – GitHub Actions (recommended)**

- Push or merge changes into the `main` branch.
- The `Deploy` workflow (`.github/workflows/deploy.yml`) builds images, updates the GKE cluster, and refreshes the ingress.

**Option 2 – Manual Pulumi deployment**

From the repository root:

```bash
cd src/deployment
sh docker-shell.sh

cd deploy_images
pulumi up --stack dev --refresh -y

cd ../deploy_k8s
pulumi up --stack dev --refresh -y
```

See `src/deployment/README.md` and `reports/milestone5/README.md` for more details about the cluster, services, and Pulumi stacks.

---

## Security & Privacy
- User-uploaded documents stay in the `fw_user_uploads` bucket and are referenced by session metadata in Postgres.
- Secrets (service-account keys, env files) are kept outside version control under `secrets/`.
- FinWhiz is an educational tool only—it is **not** a registered financial advisor.

---

## Known Issues & Limitations

- **Billing and cluster lifecycle** – GKE/Vertex/Cloud SQL incur cost; if billing credits expire or the billing account changes, re-enable billing and re-provision the cluster (public URL may change when the load balancer is rebuilt).
- **Secrets and CI scope** – Cloud-backed tests and deployments need GCP secrets (service account JSON, Cloud SQL credentials). Without them, cloud/system tests are skipped and only unit/integration tests run.
- **Coverage tracking** – Latest GitHub Actions: unit-only coverage ~57%; combined unit + integration slightly over 60%. Therefore, smoke testing after deployment of major changes is recommended to confirm expected behavior and catch any faulty behavior not covered by code tests.
