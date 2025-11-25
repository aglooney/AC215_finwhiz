# FinWhiz

*Last Updated: November 25, 2024*

FinWhiz is a full-stack, microservices-based RAG-LLM platform that delivers personalized financial education through conversational AI, document intelligence, and real-time market data.

## Features

### 🤖 Conversational AI
- **General Knowledge Mode**: RAG-enhanced responses using curated financial content from IRS, FINRA, and FRED.
- **Personalized Guidance**: Context-aware responses leveraging uploaded user documents (W-2s, 1099s, portfolio statements)
- **Source Citations**: Transparent responses with document references and relevance scores

### 📄 Document Intelligence
- **W-2 Processing**: Automated extraction of wages, tax withholdings, and employer information
- **1099 Processing**: Intelligent parsing of interest income, dividends, and payer details
- **Portfolio Analysis**: Extraction of holdings, valuations, and account information from statements
- **AI-Powered Extraction**: Vertex AI Document AI for accurate field recognition

### 📈 Live Portfolio Tracking
- **Real-Time Valuation**: Current market prices for all holdings
- **Gain/Loss Analysis**: Automatic calculation of performance vs. cost basis
- **Portfolio Analytics**: Asset allocation, sector breakdown, and risk metrics
- **Market Dashboard**: Live quotes, major indices (S&P 500, Dow, NASDAQ), and historical data

### 🌐 Web Interface
- **User Onboarding**: Personalized setup with risk assessment
- **Chat Interface**: Natural language interaction with AI assistant
- **Document Upload**: Drag-and-drop file upload with processing status
- **Portfolio Recommendations**: Dynamic asset allocation based on age, goals, and risk tolerance
- **Market Overview**: Real-time market data visualization

---

## Quick Start

### Prerequisites
- Docker Desktop (or Docker Engine) + docker-compose plugin
- GCP service account with access to Vertex AI, Cloud Storage, and Cloud SQL
- Credentials stored in `secrets/` directory

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/finwhiz.git
   cd finwhiz
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your GCP credentials and configuration
   ```

3. **Start all services:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - **Web UI**: http://localhost:3000
   - **Agent API**: http://localhost:8010/health
   - **LLM API**: http://localhost:8001/health

For detailed setup instructions, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

---

## Architecture Overview

```
Browser (localhost:3000)
    │
    ▼
Frontend (React + Nginx)
    │
    ├─► Agent API (FastAPI) ──► Cloud SQL Proxy ──► Cloud SQL (PostgreSQL)
    │                        └─► GCS Buckets
    │                        └─► Vertex AI Document AI
    │                        └─► Yahoo Finance API
    │
    └─► LLM API (FastAPI) ────► ChromaDB (Vector Store)
                              └─► Vertex AI (Gemini 2.5)
```

**Key Technologies:**
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Backend**: FastAPI, Python 3.11, SQLAlchemy
- **Database**: Cloud SQL (PostgreSQL 15)
- **Storage**: Google Cloud Storage
- **AI/ML**: Vertex AI (Gemini 2.5, Document AI, Embeddings)
- **Vector DB**: ChromaDB
- **Infrastructure**: Docker, Docker Compose, Nginx

For comprehensive architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Repository Structure

```
finwhiz/
├── docs/                           # Documentation
│   ├── DEVELOPMENT.md              # Development setup and workflow
│   ├── ARCHITECTURE.md             # System architecture and design
│   └── API_REFERENCE.md            # Complete API documentation
│
├── src/                            # Source code
│   ├── frontend/                   # React web application
│   │   ├── src/
│   │   │   ├── components/         # UI components
│   │   │   │   ├── Login.tsx
│   │   │   │   ├── Signup.tsx
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── DocumentUpload.tsx
│   │   │   │   ├── PortfolioRecommendation.tsx
│   │   │   │   ├── LivePortfolio.tsx
│   │   │   │   └── MarketOverview.tsx
│   │   │   ├── pages/              # Application pages
│   │   │   │   ├── Onboarding.tsx
│   │   │   │   └── Dashboard.tsx
│   │   │   └── services/           # API clients
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   └── README.md
│   │
│   ├── agentic_user_data_processing/  # Agent API service
│   ├── llm/                           # LLM/RAG service
│   ├── query_client/                  # CLI tool (optional)
│   ├── embedder/                      # Embedding utilities
│   ├── webscraping/                   # Data ingestion pipelines
│   ├── gcp_storage/                   # GCS helper library
│   └── synthetic_data/                # Test data generators
│
├── tests/                          # Test suites
│   ├── integration/                # Integration tests
│   ├── cloud/                      # Cloud-backed tests
│   └── conftest.py
│
├── reports/                        # Milestone documentation
│   ├── milestone2/
│   └── milestone4/
│       ├── README.md               # MS4 overview
│       ├── data_versioning.md      # DVC strategy
│       └── model_finetuning.md     # Fine-tuning details
│
├── .github/workflows/              # CI/CD pipelines
│   ├── python-tests.yml            # Automated testing
│   └── python-lint.yml             # Code quality checks
│
├── docker-compose.yml              # Multi-container orchestration
├── .dvc/                           # Data versioning
├── .env.example                    # Environment template
└── README.md                       # This file
```

---

## Service Components

| Service | Technology | Port | Documentation | Purpose |
|---------|------------|------|---------------|---------|
| **Frontend** | React + Nginx | 3000 | [README](src/frontend/README.md) | Web UI with authentication, chat, document upload, portfolio tracking |
| **Agent API** | FastAPI | 8010 | [README](src/agentic_user_data_processing/README.md) | Session management, document processing, market data |
| **LLM Service** | FastAPI + ChromaDB | 8001 | [README](src/llm/README.md) | RAG-powered query processing with Gemini 2.5 |
| **Query Client** | Python CLI | - | [README](src/query_client/README.md) | Interactive command-line interface (optional) |
| **Embedder** | Python | - | [README](src/embedder/README.md) | Document embedding generation and upload |
| **Webscraping** | Python | - | [README](src/webscraping/README.md) | Data ingestion from IRS, FINRA, FRED, Consumer Finance |
| **GCS Utilities** | Python | - | [README](src/gcp_storage/README.md) | Google Cloud Storage helper library |
| **Synthetic Data** | Python | - | [README](src/synthetic_data/README.md) | W-2, 1099, and portfolio test data generators |
| **Cloud SQL Proxy** | GCP Connector | 5432 | - | Secure connection to Cloud SQL database |

---

## API Endpoints

### Agent API (port 8010)

**Session Management:**
- `POST /sessions/` - Create new session
- `POST /sessions/{id}/messages` - Log message
- `GET /sessions/{id}/context` - Get session context

**Document Upload:**
- `POST /sessions/{id}/w2` - Upload W-2 form
- `POST /sessions/{id}/1099` - Upload 1099 form
- `POST /sessions/{id}/portfolio` - Upload portfolio statement

**Portfolio Features:**
- `GET /sessions/{id}/portfolio/live` - Real-time portfolio values
- `GET /sessions/{id}/portfolio/analytics` - Portfolio analysis

**Market Data:**
- `GET /market/quote/{ticker}` - Stock quote
- `GET /market/indices` - Market indices (S&P 500, Dow, NASDAQ)
- `GET /market/history/{ticker}` - Historical prices

### LLM API (port 8001)

- `POST /query` - RAG-powered query processing
- `GET /health` - Service health check

For complete API documentation, see [docs/API_REFERENCE.md](docs/API_REFERENCE.md).

---

## Data Versioning

FinWhiz uses **DVC (Data Version Control)** for reproducible data management:

### DVC-Tracked Datasets

1. **FIQA Fine-Tuning Dataset** (38MB)
   - Location: `src/llm/finetuning/data.dvc`
   - Content: 4 JSONL files with financial Q&A pairs
   - Purpose: Gemini 2.5 fine-tuning

2. **Webscraped Financial Content** (7.4MB)
   - Location: `src/webscraping/data.dvc`
   - Content: 108 NDJSON files from IRS, FINRA, FRED, Consumer Finance
   - Purpose: RAG knowledge base

### DVC Configuration

```bash
# Remote storage
dvc remote default finetuning_gcs
dvc remote modify finetuning_gcs url gs://finwhiz-storage/finetuning_dvc

# Pull data
dvc pull src/llm/finetuning/data.dvc
dvc pull src/webscraping/data.dvc

# Push updates
dvc add src/llm/finetuning/data/
dvc push
```

For detailed data versioning strategy, see [reports/milestone4/data_versioning.md](reports/milestone4/data_versioning.md).

---

## Model Fine-Tuning

FinWhiz uses a fine-tuned **Gemini 2.5 Flash Lite** model for specialized financial Q&A:

- **Base Model**: `gemini-2.5-flash-001`
- **Fine-Tuned Model**: `gemini-2.5-flash-lite-preview-02`
- **Training Data**: FIQA dataset (38MB, financial questions)
- **Adapter Size**: 4 (ADAPTER_SIZE_FOUR)
- **Epochs**: 3

### Evaluation Results

| Metric | Base Model | Fine-Tuned Model | Improvement |
|--------|-----------|-----------------|-------------|
| Rouge-L Score | 0.34 | 0.54 | +59% |
| LLM-as-Judge (gemini-2.5-pro) | 48/50 wins | 2/50 wins | Base preferred |

**Deployment Strategy**: Hybrid approach
- Fine-tuned model for quick, factual queries
- Base model for comprehensive explanations

For complete fine-tuning documentation, see [reports/milestone4/model_finetuning.md](reports/milestone4/model_finetuning.md).

---

## Testing

### Run Tests

```bash
# Unit tests with coverage
pytest

# Integration tests
pytest -m system

# Full test suite (CI-equivalent)
./scripts/run_tests_with_coverage.sh
```

### Test Coverage

- **Target**: 50% minimum (Milestone 4 requirement)
- **Unit Tests**: All services
- **Integration Tests**: Multi-service workflows
- **Cloud Tests**: GCS, Cloud SQL, Vertex AI

### CI/CD

GitHub Actions workflows:
- `.github/workflows/python-tests.yml` - Automated testing on push/PR
- `.github/workflows/python-lint.yml` - Code quality checks (Black, Flake8)

---

## Development Workflow

### Option 1: Local Frontend + Docker Backend (Recommended)

```bash
# Start backend services
./start-dev.sh

# In another terminal, start frontend
cd src/frontend
npm run dev
```

### Option 2: Full Docker

```bash
docker-compose up --build
```

### Code Quality

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push

# Run manually
pre-commit run --all-files
```

For complete development guide, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

---

## Environment Configuration

Create a `.env` file (use `.env.example` as template):

```bash
# GCP Credentials
GOOGLE_APPLICATION_CREDENTIALS=secrets/service-account-key.json
BUCKET_CREDENTIALS=secrets/service-account-key.json
VERTEXAI_CREDENTIALS=secrets/vertexai-service-account.json

# GCS Buckets
GCS_BUCKET=fw_ws
GCS_PREFIX=chroma_storage
USER_UPLOAD_BUCKET=fw_user_uploads

# Database (Cloud SQL via Proxy)
DATABASE_URL=postgresql+psycopg://finwhiz:password@cloudsql-proxy:5432/finwhiz

# Service URLs
AGENT_URL=http://agent:8010
LLM_URL=http://llm:8001

# Chroma Configuration
CHROMA_PATH=/app/src/chroma_storage
COLLECTION_NAME=finwhiz_docs
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check service health
docker ps
curl http://localhost:8010/health
curl http://localhost:8001/health

# View logs
docker-compose logs -f

# Clean restart
docker-compose down && docker-compose up --build
```

### Frontend Can't Connect

1. Verify backend services are running
2. Check browser console for errors
3. Ensure `/api/*` routes proxy correctly (nginx.conf)

### Document Upload Fails

1. Verify GCS credentials in `.env`
2. Check file is PDF format
3. Review agent logs: `docker logs finwhiz_agent`

For comprehensive troubleshooting, see [docs/DEVELOPMENT.md#troubleshooting](docs/DEVELOPMENT.md#troubleshooting).

---

## Security & Privacy

- **Document Storage**: User uploads isolated by session in GCS with IAM-controlled access
- **Database**: Cloud SQL with encryption at rest, connections via Cloud SQL Proxy
- **Secrets**: All credentials in `secrets/` directory, never committed to version control
- **Authentication**: Login/Signup UI implemented (enforcement planned for Milestone 5)
- **Disclaimer**: FinWhiz is an **educational tool only** – not a registered financial advisor

---

## Milestone 4 Deliverables

✅ **Application Design & Code Organization**
- Well-structured, containerized microservices
- Clear separation of concerns (API, LLM, UI, data)
- Comprehensive documentation

✅ **APIs & Frontend**
- RESTful APIs with FastAPI
- React + TypeScript web UI
- Full end-to-end integration

✅ **CI/CD & Testing**
- GitHub Actions workflows
- Unit, integration, and cloud tests
- 50%+ code coverage

✅ **Data Versioning**
- DVC with GCS remote storage
- 38MB fine-tuning data + 7.4MB webscraped data
- Reproducible workflows

✅ **Model Fine-Tuning**
- Gemini 2.5 Flash Lite fine-tuned on FIQA
- Comprehensive evaluation (quantitative + LLM-as-judge)
- Hybrid deployment strategy

For submission details, see [MILESTONE4.md](MILESTONE4.md).

---

## Project Milestones

- ✅ **Milestone 1**: Data collection and initial prototyping
- ✅ **Milestone 2**: Containerized pipeline with RAG and document processing
- ✅ **Milestone 3**: Vertex AI integration and workflow optimization
- ✅ **Milestone 4**: Full-stack application with CI/CD and fine-tuning
- 🚀 **Milestone 5**: Production deployment to GCP (Cloud Run/GKE)

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Complete development setup and workflow guide |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and design patterns |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | Comprehensive API endpoint documentation |
| [reports/milestone4/README.md](reports/milestone4/README.md) | Milestone 4 overview and deliverables |
| [reports/milestone4/data_versioning.md](reports/milestone4/data_versioning.md) | Data versioning strategy and usage |
| [reports/milestone4/model_finetuning.md](reports/milestone4/model_finetuning.md) | Fine-tuning methodology and results |

---

## Contributing

1. **Code Style**: Follow PEP 8 for Python, Airbnb guide for JavaScript
2. **Pre-commit Hooks**: Run `pre-commit install` to enable automatic formatting
3. **Testing**: Write tests for new features, maintain 50%+ coverage
4. **Documentation**: Update READMEs when changing functionality
5. **Commits**: Use descriptive commit messages

---

## License

This project is for educational purposes as part of AC215 (MLOps) at Harvard University.

---

## Team

FinWhiz is developed by the AC215 FinWhiz team.

---

## Acknowledgments

- **Harvard AC215**: MLOps course and teaching staff
- **Google Cloud**: Vertex AI, Cloud SQL, Cloud Storage
- **Financial Data Sources**: IRS, FINRA, FRED
- **Open Source**: React, FastAPI, ChromaDB, and the broader Python/JavaScript ecosystems

---

*For issues or questions, check service logs and review the troubleshooting sections in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).*
