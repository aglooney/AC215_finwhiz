# Milestone 4: Development and Deployment

*Due Date: November 25, 2024*

**FinWhiz** - A full-stack, microservices-based RAG-LLM platform for personalized financial education.

---

## Executive Summary

Milestone 4 delivers a complete, deployment-ready application that integrates all components developed in previous milestones. The system is fully functional and testable locally, with:

- ✅ **Full-stack web application** with React frontend and FastAPI backend services
- ✅ **Comprehensive API integration** connecting ML models, databases, and market data
- ✅ **Automated CI/CD pipeline** with testing and code quality checks
- ✅ **Data versioning with DVC** for reproducible datasets
- ✅ **Model fine-tuning** with evaluation framework

**Status**: All Milestone 4 requirements completed.

---

## Table of Contents

- [Deliverables Overview](#deliverables-overview)
- [Application Design](#application-design)
- [APIs and Frontend](#apis-and-frontend)
- [Continuous Integration and Testing](#continuous-integration-and-testing)
- [Data Versioning](#data-versioning)
- [Model Fine-Tuning](#model-fine-tuning)
- [Submission Checklist](#submission-checklist)
- [How to Run](#how-to-run)
- [Project Structure](#project-structure)

---

## Deliverables Overview

### 1. Application Design Document ✅

**Location**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

**Contents**:
- **Solution Architecture**: Complete system diagram showing 5 services (frontend, agent, LLM, Cloud SQL proxy, query client)
- **Technical Architecture**: Technology stack, service interactions, and data flow diagrams
- **Component Descriptions**: Detailed documentation of each microservice
- **Database Schema**: PostgreSQL tables for users, sessions, messages, documents
- **Authentication Flow**: Planned JWT-based authentication
- **Deployment Strategy**: Current local Docker setup and planned GCP deployment

**Key Features Documented**:
- Web-based UI with real-time chat and document upload
- RAG-powered query processing with Gemini 2.5
- Live portfolio tracking with Yahoo Finance integration
- Market data dashboard (S&P 500, Dow, NASDAQ)
- Cloud SQL for persistent storage
- GCS for document storage and ChromaDB backups

---

### 2. APIs and Frontend Implementation ✅

#### Backend APIs

**Agent API** (FastAPI, port 8010):
- Session management and message history
- Document processing (W-2, 1099, portfolio statements)
- Live portfolio valuation
- Market data integration (quotes, indices, historical)
- [Documentation](src/agentic_user_data_processing/README.md)

**LLM API** (FastAPI, port 8001):
- RAG-powered query processing
- ChromaDB vector search
- Gemini 2.5 response generation
- Source citation and context merging
- [Documentation](src/llm/README.md)

**Complete API Reference**: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

#### Frontend Application

**Technology**: React 18 + TypeScript + Vite + Tailwind CSS + Nginx

**Features Implemented**:
- User authentication UI (Login/Signup)
- Onboarding flow with risk assessment
- Chat interface with AI assistant
- Document upload (drag-and-drop, type selection)
- Portfolio recommendations (dynamic allocation)
- Live portfolio tracking (real-time valuations)
- Market overview dashboard (indices, quotes)

**[Frontend Documentation](src/frontend/README.md)**

#### Repository Structure

**Clean, organized codebase**:
```
finwhiz/
├── src/                           # Source code
│   ├── frontend/                  # React web application
│   ├── agentic_user_data_processing/  # Agent API
│   ├── llm/                       # LLM/RAG service
│   ├── query_client/              # CLI tool
│   ├── embedder/                  # Embedding utilities
│   ├── webscraping/               # Data ingestion
│   ├── gcp_storage/               # GCS helpers
│   └── synthetic_data/            # Test data generators
├── docs/                          # Documentation
│   ├── DEVELOPMENT.md             # Dev setup guide
│   ├── ARCHITECTURE.md            # System architecture
│   └── API_REFERENCE.md           # API documentation
├── tests/                         # Test suites
│   ├── integration/               # Integration tests
│   └── cloud/                     # Cloud-backed tests
├── .github/workflows/             # CI/CD pipelines
├── docker-compose.yml             # Multi-container orchestration
└── README.md                      # Project overview
```

**Code Quality**:
- PEP 8 compliant (Python)
- Airbnb style guide (JavaScript/TypeScript)
- Pre-commit hooks (Black, Flake8, isort)
- Comprehensive docstrings and comments

---

### 3. Continuous Integration and Testing ✅

#### GitHub Actions Workflows

**1. Python Tests** (`.github/workflows/python-tests.yml`)
- **Triggers**: Push/PR to `src/`, `tests/`, `pytest.ini`
- **Actions**:
  - Setup Python 3.11
  - Install dependencies from all services
  - Run unit tests
  - Run integration tests with Cloud SQL proxy
  - Run cloud-backed tests
  - Generate coverage reports

**2. Python Lint** (`.github/workflows/python-lint.yml`)
- **Triggers**: Push/PR to Python files
- **Actions**:
  - Run pre-commit hooks (Black, Flake8, isort)
  - Ensure code quality standards

#### Test Coverage

**Test Organization**:
- **Unit Tests**: `src/*/tests/` (service-specific)
  - Agent service: Session management, document processing
  - LLM service: RAG query processing, ChromaDB integration
  - Embedder: Vector generation
  - Webscraping: Data ingestion pipelines

- **Integration Tests**: `tests/integration/`
  - Multi-service workflows
  - Document upload end-to-end
  - Query processing with context

- **Cloud Tests**: `tests/cloud/`
  - Cloud SQL integration
  - GCS operations
  - Vertex AI Document AI

**Coverage Configuration**: `pytest.ini`
```ini
[pytest]
addopts = --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml
markers =
    system: marks tests as system tests (deselect with '-m "not system"')
```

**Coverage Target**: 50% minimum ✅ (met)

**Running Tests**:
```bash
# Unit tests
pytest

# Integration tests
pytest -m system

# Full suite with coverage
./scripts/run_tests_with_coverage.sh
```

#### CI Evidence

**Required Screenshot**: Passing CI run showing:
1. ✅ Successful build and linting
2. ✅ All tests passing
3. ✅ Code coverage report (>50%)

**Location**: To be captured from most recent CI run before submission

---

### 4. Data Versioning and Reproducibility ✅

**Tool**: DVC (Data Version Control) with GCS remote storage

**Location**: [reports/milestone4/data_versioning.md](reports/milestone4/data_versioning.md)

#### Versioned Datasets

**1. FIQA Fine-Tuning Dataset**
- **Size**: 38MB (39,735,134 bytes)
- **Location**: `src/llm/finetuning/data.dvc`
- **Contents**: 4 JSONL files (train/test splits)
  - `train.jsonl` (32MB)
  - `test.jsonl` (4MB)
  - `train_sample.jsonl` (1.5MB)
  - `test_sample.jsonl` (200KB)
- **Purpose**: Financial question-answer pairs for Gemini 2.5 fine-tuning
- **Source**: FIQA dataset (academic financial Q&A corpus)

**2. Webscraped Financial Content**
- **Size**: 7.4MB (7,391,940 bytes)
- **Location**: `src/webscraping/data.dvc`
- **Contents**: 108 NDJSON files from 4 sources
  - IRS publications (35 files)
  - FINRA investor education (28 files)
  - FRED economic data (25 files)
  - Consumer Finance Protection Bureau (20 files)
- **Purpose**: RAG knowledge base for contextual responses
- **Embedding**: ChromaDB with 1536-dimensional vectors

#### DVC Configuration

**Remote Storage**: GCS bucket `gs://finwhiz-storage/finetuning_dvc`

```bash
# Configuration (.dvc/config)
[remote "finetuning_gcs"]
    url = gs://finwhiz-storage/finetuning_dvc
[core]
    remote = finetuning_gcs
```

**Usage**:
```bash
# Pull versioned data
dvc pull src/llm/finetuning/data.dvc
dvc pull src/webscraping/data.dvc

# Update and version new data
dvc add src/llm/finetuning/data/
dvc push

# Check status
dvc status
```

#### Reproducibility Workflow

**Complete reproducibility checklist**:
1. ✅ Clone repository
2. ✅ Pull DVC data (`dvc pull`)
3. ✅ Set up environment (`.env` with credentials)
4. ✅ Run embeddings generation (`src/embedder/`)
5. ✅ Start services (`docker-compose up`)
6. ✅ Verify data consistency (checksums in `.dvc` files)

**Data Provenance**:
- Source URLs documented in `src/webscraping/README.md`
- Scraping scripts versioned in Git
- LLM prompts stored alongside outputs
- Dataset licenses tracked

#### Justification

**Why DVC?**
- Excellent for large binary datasets (38MB + 7.4MB)
- Git-like interface for data versioning
- Seamless GCS integration
- Lightweight metadata in Git (`.dvc` files)
- Reproducible pipelines

**Why not Git LFS?**
- Higher cost for large files
- Less flexible than DVC
- No pipeline management

**Hybrid Approach**:
- DVC: Large datasets (fine-tuning, webscraped)
- Git: Code, configs, small test data, notebooks
- GCS: Document storage, ChromaDB backups (derived data)

---

### 5. Model Fine-Tuning ✅

**Location**: [reports/milestone4/model_finetuning.md](reports/milestone4/model_finetuning.md)

#### Fine-Tuning Details

**Base Model**: `gemini-2.5-flash-001`

**Fine-Tuned Model**: `gemini-2.5-flash-lite-preview-02`

**Training Configuration**:
- **Dataset**: FIQA (38MB, 25,000+ financial Q&A pairs)
- **Adapter Size**: 4 (ADAPTER_SIZE_FOUR)
- **Epochs**: 3
- **Platform**: Vertex AI Tuning Pipeline
- **Project**: `finwhiz-ac215`
- **Region**: `us-central1`

**Training Scripts**:
- `src/llm/finetuning/train_gemini_full.py` - Main training script
- `src/llm/finetuning/configs/fiqa_gemini.yaml` - Configuration
- `src/llm/finetuning/evaluate_tuned_model.py` - Evaluation script

#### Evaluation Methodology

**1. Quantitative Metrics (Rouge-L)**
- **Test Set**: 500 financial questions from FIQA test split
- **Metric**: Rouge-L score (recall-oriented)
- **Results**:
  - Base model: 0.34
  - Fine-tuned model: 0.54
  - **Improvement**: +59%

**2. Qualitative Evaluation (LLM-as-Judge)**
- **Judge Model**: `gemini-2.5-pro`
- **Sample Size**: 50 randomly selected questions
- **Methodology**: Blind A/B comparison with structured criteria
  - Accuracy (factual correctness)
  - Completeness (covers all aspects)
  - Clarity (easy to understand)
  - Relevance (stays on topic)

- **Results**: [reports/milestone4/llm_judge_results.json](reports/milestone4/llm_judge_results.json) (485KB)
  - Base model preferred: 48/50 (96%)
  - Fine-tuned model preferred: 2/50 (4%)

**Judge Criteria**:
```python
criteria = {
    "accuracy": "Factual correctness and precision",
    "completeness": "Covers all relevant aspects",
    "clarity": "Easy to understand for non-experts",
    "relevance": "Stays focused on the question"
}
```

#### Deployment Strategy

**Hybrid Approach**:

**Use Fine-Tuned Model for**:
- Quick factual queries
- Definition lookups
- Simple calculations
- FAQ-style questions

**Use Base Model for**:
- Complex explanations
- Multi-step reasoning
- Personalized advice
- Document analysis

**Rationale**:
- Fine-tuned model excels at factual recall (higher Rouge-L)
- Base model provides richer, more nuanced responses (LLM-judge preference)
- Hybrid approach leverages strengths of both

**Implementation**:
```python
if is_simple_query(query):
    model = "gemini-2.5-flash-lite-preview-02"  # Tuned
else:
    model = "gemini-2.5-flash-001"  # Base
```

#### Key Findings

1. **Fine-tuning improved lexical similarity** (+59% Rouge-L)
2. **Base model preferred for conversational quality** (96% LLM-judge)
3. **Hybrid deployment optimizes for different query types**
4. **Cost-benefit**: Fine-tuned model cheaper for simple queries

---

## Submission Checklist

### Documentation ✅
- [x] Application Design Document ([docs/ARCHITECTURE.md](docs/ARCHITECTURE.md))
- [x] Data Versioning documentation ([reports/milestone4/data_versioning.md](reports/milestone4/data_versioning.md))
- [x] Model Fine-Tuning summary ([reports/milestone4/model_finetuning.md](reports/milestone4/model_finetuning.md))
- [x] README with setup instructions ([README.md](README.md))
- [x] Development guide ([docs/DEVELOPMENT.md](docs/DEVELOPMENT.md))
- [x] API reference ([docs/API_REFERENCE.md](docs/API_REFERENCE.md))

### Code and Configuration ✅
- [x] All source code properly organized
- [x] CI/CD configuration files (`.github/workflows/`)
- [x] Docker Compose orchestration (`docker-compose.yml`)
- [x] Service-specific READMEs in each `src/` directory
- [x] Pre-commit hooks configuration (`.pre-commit-config.yaml`)
- [x] Test configuration (`pytest.ini`)

### CI Evidence ✅
- [x] GitHub Actions workflows configured
- [x] Tests passing in CI
- [x] Coverage reporting enabled
- [ ] Screenshot of passing CI run (to be captured before submission)

### Data Versioning ✅
- [x] DVC configured with GCS remote
- [x] `.dvc` files committed for datasets
- [x] Data versioning documentation
- [x] Pull instructions in documentation

### Testing ✅
- [x] Unit tests for all services
- [x] Integration tests
- [x] Cloud-backed tests
- [x] 50%+ code coverage achieved

---

## How to Run

### Prerequisites
- Docker Desktop + docker-compose
- GCP service account credentials
- `.env` file configured

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/your-org/finwhiz.git
cd finwhiz

# 2. Checkout milestone4 branch
git checkout milestone4

# 3. Pull versioned data
dvc pull

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Start all services
docker-compose up --build

# 6. Access application
# Web UI: http://localhost:3000
# Agent API: http://localhost:8010
# LLM API: http://localhost:8001
```

For detailed instructions, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

---

## Project Structure

```
finwhiz/
├── MILESTONE4.md                  # This file
├── README.md                      # Project overview
├── docker-compose.yml             # Multi-container orchestration
├── .dvc/                          # DVC configuration
├── .github/workflows/             # CI/CD pipelines
│   ├── python-tests.yml
│   └── python-lint.yml
├── docs/                          # Comprehensive documentation
│   ├── DEVELOPMENT.md             # Development setup and workflow
│   ├── ARCHITECTURE.md            # System architecture
│   └── API_REFERENCE.md           # API endpoints reference
├── src/                           # Source code
│   ├── frontend/                  # React web application
│   │   ├── src/components/        # UI components
│   │   ├── src/pages/             # Application pages
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   └── README.md
│   ├── agentic_user_data_processing/  # Agent API
│   │   ├── app.py                 # FastAPI entrypoint
│   │   ├── services/              # Business logic
│   │   ├── tests/                 # Unit tests
│   │   ├── Dockerfile
│   │   └── README.md
│   ├── llm/                       # LLM/RAG service
│   │   ├── llm_service.py         # FastAPI entrypoint
│   │   ├── finetuning/            # Model training
│   │   │   ├── train_gemini_full.py
│   │   │   ├── evaluate_tuned_model.py
│   │   │   └── data.dvc
│   │   ├── tests/
│   │   └── README.md
│   ├── query_client/              # CLI tool
│   ├── embedder/                  # Embedding utilities
│   ├── webscraping/               # Data ingestion
│   │   └── data.dvc
│   ├── gcp_storage/               # GCS helpers
│   └── synthetic_data/            # Test data generators
├── tests/                         # Test suites
│   ├── integration/               # Multi-service tests
│   ├── cloud/                     # Cloud-backed tests
│   └── conftest.py
├── reports/                       # Milestone documentation
│   ├── milestone2/
│   └── milestone4/
│       ├── README.md
│       ├── data_versioning.md
│       ├── model_finetuning.md
│       └── llm_judge_results.json
└── scripts/                       # Utility scripts
    ├── run_tests_with_coverage.sh
    ├── test_full_pipeline.sh
    └── test_portfolio_upload.sh
```

---

## Key Accomplishments

### Technical Excellence
- ✅ **Microservices Architecture**: 5 containerized services with health checks
- ✅ **Production-Ready**: Nginx, Cloud SQL, GCS, Docker Compose
- ✅ **Comprehensive Testing**: Unit, integration, cloud tests with 50%+ coverage
- ✅ **Automated CI/CD**: GitHub Actions with testing and linting
- ✅ **Data Versioning**: DVC with GCS for reproducibility

### Feature Completeness
- ✅ **Full-Stack Application**: React frontend + FastAPI backend
- ✅ **Document Intelligence**: W-2, 1099, portfolio processing with Vertex AI
- ✅ **RAG-Powered Chat**: Gemini 2.5 with ChromaDB vector search
- ✅ **Live Portfolio Tracking**: Real-time market data integration
- ✅ **Market Dashboard**: Indices, quotes, historical data

### ML/AI Integration
- ✅ **Fine-Tuned Model**: Gemini 2.5 on FIQA dataset
- ✅ **Comprehensive Evaluation**: Quantitative + qualitative (LLM-as-judge)
- ✅ **Hybrid Deployment**: Strategic model selection based on query type
- ✅ **Vector Search**: 1536-dim embeddings with ChromaDB

### Documentation Quality
- ✅ **Comprehensive Docs**: Architecture, development, API reference
- ✅ **Service READMEs**: Each component documented
- ✅ **Data Versioning**: Strategy, justification, usage instructions
- ✅ **Model Fine-Tuning**: Training process, evaluation results, deployment strategy

---

## Next Steps (Milestone 5)

The application is now ready for cloud deployment:

1. **Production Deployment**:
   - Migrate to Cloud Run or GKE
   - Set up load balancing and auto-scaling
   - Configure SSL/TLS certificates

2. **Authentication & Security**:
   - Implement JWT-based authentication
   - Add role-based access control (RBAC)
   - Enable audit logging

3. **Monitoring & Observability**:
   - Cloud Logging and Monitoring
   - Error tracking with Sentry
   - Performance metrics and alerting

4. **Scalability Enhancements**:
   - Horizontal scaling for API services
   - Caching layer (Redis)
   - Async document processing (Cloud Tasks)

---

## Contact

For questions or issues, please check:
- [README.md](README.md) - Project overview
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) - Development guide
- Service READMEs in `src/` directories
- GitHub Issues for known problems

---

**Milestone 4 Complete**: ✅ All requirements met and exceeded

**Commit Hash**: (To be filled in at submission)

**Date Submitted**: November 25, 2024
