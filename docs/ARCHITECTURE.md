# FinWhiz Architecture

*Last Updated: November 25, 2024*

Comprehensive documentation of the FinWhiz system architecture, including services, data flow, and technology stack.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Service Components](#service-components)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Database Schema](#database-schema)
- [Authentication Flow](#authentication-flow)
- [Deployment Architecture](#deployment-architecture)
- [Security Considerations](#security-considerations)

---

## System Overview

FinWhiz is a full-stack, microservices-based RAG-LLM platform for personalized financial education. The system combines:

1. **Retrieval-Augmented Generation (RAG)** - Curated financial content from IRS, FINRA, FRED, etc.
2. **Document Processing** - AI-powered extraction from W-2s, 1099s, and portfolio statements
3. **Real-time Market Data** - Live stock quotes, indices, and historical data
4. **Conversational AI** - Powered by Google Gemini 2.5 via Vertex AI
5. **Web Interface** - React-based dashboard for chat, document upload, and portfolio tracking

### Key Features

- **General Knowledge Mode**: RAG-enhanced responses using curated public financial resources
- **Personalized Guidance**: Context-aware responses using uploaded user documents
- **Live Portfolio Tracking**: Real-time portfolio valuation with market data integration
- **Document Intelligence**: Automated extraction from tax forms and financial statements
- **Market Analytics**: Current quotes, indices, and historical price data

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER BROWSER                               │
│                         http://localhost:3000                           │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ HTTP/HTTPS
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND SERVICE                                 │
│                      (React + TypeScript + Nginx)                        │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    React Application                             │   │
│  │                                                                   │   │
│  │  Components:                                                      │   │
│  │  ├── Login/Signup (Authentication)                               │   │
│  │  ├── Onboarding (User profiling)                                 │   │
│  │  ├── Dashboard (Main interface)                                  │   │
│  │  ├── ChatInterface (AI conversation)                             │   │
│  │  ├── DocumentUpload (W-2, 1099, Portfolio)                       │   │
│  │  ├── PortfolioRecommendation (Asset allocation)                  │   │
│  │  ├── LivePortfolio (Real-time tracking)                          │   │
│  │  └── MarketOverview (Market dashboard)                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  Nginx Reverse Proxy:                                                    │
│  ├── /api/agent/* → http://agent:8010                                   │
│  └── /api/llm/*   → http://llm:8001                                     │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │
                ┌───────────────┴────────────────┐
                │                                │
                ▼                                ▼
┌────────────────────────────┐      ┌────────────────────────────┐
│      AGENT SERVICE         │      │       LLM SERVICE          │
│       (FastAPI)            │      │       (FastAPI)            │
│      Port: 8010            │      │      Port: 8001            │
│                            │      │                            │
│ Endpoints:                 │      │ Endpoints:                 │
│ ├── POST /sessions         │      │ ├── POST /query            │
│ ├── POST /{id}/messages    │      │ └── GET /health            │
│ ├── POST /{id}/w2          │      │                            │
│ ├── POST /{id}/1099        │      │ Features:                  │
│ ├── POST /{id}/portfolio   │      │ ├── RAG Query Processing   │
│ ├── GET /{id}/context      │      │ ├── ChromaDB Integration   │
│ ├── GET /{id}/portfolio/   │      │ ├── Gemini 2.5 LLM         │
│ │   live                   │      │ ├── Vector Embeddings      │
│ ├── GET /{id}/portfolio/   │      │ └── Context Merging        │
│ │   analytics              │      │                            │
│ ├── GET /market/quote/{t}  │      │ Models:                    │
│ ├── GET /market/indices    │      │ ├── Base: gemini-2.5-      │
│ └── GET /market/history/{t}│      │ │   flash-001              │
│                            │      │ └── Tuned: gemini-2.5-     │
│ Services:                  │      │     flash-lite (fine-tuned)│
│ ├── Document Processing    │      │                            │
│ ├── Vertex AI Extraction   │      │ Vector DB:                 │
│ ├── GCS Storage            │◄─────┤ ChromaDB (embedded)        │
│ ├── Market Data (yfinance) │      │ ├── 7.4MB webscraped data  │
│ └── Database Operations    │      │ └── 1536-dim embeddings    │
└────────────┬───────────────┘      └────────────────────────────┘
             │
             │
             ▼
┌─────────────────────────────┐    ┌────────────────────────────┐
│   CLOUD SQL PROXY           │    │     GOOGLE CLOUD           │
│   (PostgreSQL Connector)    │    │        STORAGE             │
│   Port: 5432                │    │                            │
│                             │    │ Buckets:                   │
│ Connects to:                │    │ ├── fw_ws                  │
│ finwhiz-ac215:us-central1:  │    │ │   └── chroma_storage/    │
│ finwhiz-cloud-sql           │    │ │       (vector backups)   │
│                             │    │ ├── fw_user_uploads        │
└─────────────┬───────────────┘    │ │   └── session docs       │
              │                    │ └── finwhiz-storage         │
              ▼                    │     └── finetuning_dvc/     │
┌──────────────────────────────┐   │         (DVC remote)        │
│    CLOUD SQL DATABASE        │   └────────────────────────────┘
│  (PostgreSQL 15)             │              ▲
│  GCP-managed, HA             │              │
│                              │              │ Used by:
│ Tables:                      │              │ - Agent (doc storage)
│ ├── users                    │              │ - LLM (chroma backups)
│ ├── sessions                 │              │ - DVC (data versioning)
│ ├── messages                 │
│ └── documents                │
│                              │   ┌────────────────────────────┐
│ Features:                    │   │    VERTEX AI PLATFORM      │
│ ├── Automatic backups        │   │                            │
│ ├── High availability        │   │ Services Used:             │
│ ├── Encrypted at rest        │   │ ├── Gemini 2.5 Flash       │
│ └── Connection pooling       │   │ │   (Base model)           │
└──────────────────────────────┘   │ ├── Fine-tuned Model       │
                                   │ │   (Custom endpoint)      │
                                   │ ├── Document AI            │
                                   │ │   (W-2/1099 extraction)  │
                                   │ └── Text Embeddings        │
                                   │     (textembedding-gecko)  │
                                   └────────────────────────────┘
```

---

## Service Components

### 1. Frontend Service

**Technology**: React 18 + TypeScript + Vite + Tailwind CSS + Nginx

**Purpose**: Web-based user interface

**Key Responsibilities:**
- User authentication (Login/Signup)
- Onboarding flow for user profiling
- Chat interface for AI conversations
- Document upload interface
- Portfolio visualization and live tracking
- Market data dashboard

**Components:**

| Component | File | Purpose |
|-----------|------|---------|
| Login | `Login.tsx` | User authentication |
| Signup | `Signup.tsx` | User registration |
| Onboarding | `Onboarding.tsx` | New user setup wizard |
| Dashboard | `Dashboard.tsx` | Main application interface |
| ChatInterface | `ChatInterface.tsx` | AI conversation UI |
| DocumentUpload | `DocumentUpload.tsx` | File upload for W-2/1099/portfolio |
| PortfolioRecommendation | `PortfolioRecommendation.tsx` | Asset allocation display |
| LivePortfolio | `LivePortfolio.tsx` | Real-time portfolio tracking |
| MarketOverview | `MarketOverview.tsx` | Market indices and quotes |

**Nginx Configuration:**
- Serves static React build
- Reverse proxies API requests to backend services
- Handles compression and caching
- Routes `/api/agent/*` to Agent service
- Routes `/api/llm/*` to LLM service

---

### 2. Agent Service

**Technology**: FastAPI + Python 3.11 + SQLAlchemy

**Purpose**: Session management, document processing, market data integration

**Key Responsibilities:**
- Create and manage user sessions
- Log messages and conversation history
- Process uploaded documents (W-2, 1099, portfolio)
- Extract data using Vertex AI Document AI
- Store documents in GCS
- Provide live portfolio valuations
- Fetch real-time market data
- Serve portfolio analytics

**Dependencies:**
- Cloud SQL (via proxy) for data persistence
- GCS for document storage
- Vertex AI for document extraction
- Yahoo Finance API for market data

**Key Services:**

| Service Module | Purpose |
|----------------|---------|
| `context.py` | Build session context for LLM queries |
| `storage.py` | GCS document upload/download |
| `extraction.py` | W-2 field extraction via Vertex AI |
| `extraction_1099.py` | 1099 field extraction |
| `extraction_portfolio.py` | Portfolio statement parsing |
| `pdf_utils.py` | PDF flattening and preprocessing |
| `yfinance_service.py` | Market data fetching |

---

### 3. LLM Service

**Technology**: FastAPI + Python 3.11 + ChromaDB + Vertex AI

**Purpose**: RAG-powered query processing with conversational AI

**Key Responsibilities:**
- Process natural language queries
- Retrieve relevant context from ChromaDB
- Merge session context from Agent service
- Generate responses using Gemini 2.5
- Provide source citations
- Manage vector embeddings

**Data Sources:**
- **Webscraped Content** (7.4MB, 108 files):
  - IRS publications
  - FINRA investor education
  - Federal Reserve (FRED) data
  - Consumer Finance Protection Bureau
- **Fine-tuning Dataset** (38MB, FIQA):
  - Financial question-answer pairs
  - Used for model fine-tuning

**Models:**
- **Base Model**: `gemini-2.5-flash-001` (general queries)
- **Fine-tuned Model**: `gemini-2.5-flash-lite-preview-02` (specialized financial Q&A)

**Vector Database:**
- **ChromaDB** (embedded, in-process)
- 1536-dimensional embeddings
- Collection: `finwhiz_docs`
- Backup: GCS bucket `fw_ws/chroma_storage/`

---

### 4. Cloud SQL Proxy

**Technology**: Google Cloud SQL Connector (Docker image)

**Purpose**: Secure connection to Cloud SQL database

**Configuration:**
- Connects to: `finwhiz-ac215:us-central1:finwhiz-cloud-sql`
- Exposes PostgreSQL on port 5432
- Uses service account credentials
- Automatic connection management

**Benefits:**
- Encrypted connections
- No need for IP whitelisting
- Automatic credential management
- Connection pooling

---

### 5. Query Client (Optional)

**Technology**: Python CLI tool

**Purpose**: Interactive command-line interface for testing and demos

**Usage:**
- Manual QA testing
- API demonstrations
- Development debugging
- Alternative to web UI

**Status**: Maintained for compatibility, web UI is primary interface

---

## Data Flow

### 1. User Onboarding Flow

```
User Browser
    │
    │ 1. Submit profile (age, retirement age, goals, risk tolerance)
    ▼
Frontend (Onboarding.tsx)
    │
    │ 2. Calculate portfolio allocation
    │ 3. Store in localStorage
    ▼
Dashboard
    │
    │ 4. Display recommendations
    ▼
PortfolioRecommendation.tsx
```

**No backend interaction** - client-side only for privacy

---

### 2. Chat Query Flow

```
User Browser
    │
    │ 1. User types question
    ▼
ChatInterface.tsx
    │
    │ 2. POST /api/llm/query
    │    {query, session_id, top_k}
    ▼
LLM Service
    │
    │ 3. Embed query (Vertex AI)
    ├─► 4. Retrieve from ChromaDB (top_k docs)
    │
    │ 5. GET agent:8010/sessions/{id}/context
    ▼
Agent Service
    │
    │ 6. Query database for session data
    │ 7. Return messages + documents
    ▼
LLM Service
    │
    │ 8. Merge RAG context + session context
    │ 9. Call Gemini 2.5 with prompt
    ▼
Vertex AI (Gemini)
    │
    │ 10. Generate response
    ▼
LLM Service
    │
    │ 11. Extract sources, format response
    │ 12. Return {response, sources}
    ▼
ChatInterface.tsx
    │
    │ 13. Display message + sources
    ▼
User Browser
```

---

### 3. Document Upload Flow

```
User Browser
    │
    │ 1. Select file (PDF), choose type (W-2/1099/Portfolio)
    ▼
DocumentUpload.tsx
    │
    │ 2. POST /api/agent/sessions/{id}/{doc_type}
    │    FormData: {file: PDF}
    ▼
Agent Service
    │
    │ 3. Read PDF bytes
    │ 4. Flatten PDF (remove form fields)
    ├─► 5. Upload to GCS (fw_user_uploads bucket)
    │
    │ 6. Call Vertex AI Document AI
    ▼
Vertex AI Document AI
    │
    │ 7. Extract fields (OCR + ML)
    │ 8. Return structured data
    ▼
Agent Service
    │
    │ 9. Parse extracted fields
    │ 10. Create document record in database
    ├─► 11. INSERT INTO documents
    │
    │ 12. Return {document_id, extracted_data, gcs_uri}
    ▼
DocumentUpload.tsx
    │
    │ 13. Display success + extracted fields
    ▼
User Browser
```

**Database Record:**
```sql
INSERT INTO documents (
    session_id,
    document_type,
    gcs_uri,
    extracted_data,
    created_at
) VALUES (
    'session-uuid',
    'w2',
    'gs://fw_user_uploads/...',
    '{"wages": 75000, ...}',
    NOW()
);
```

---

### 4. Live Portfolio Flow

```
User Browser
    │
    │ 1. Click "View Live Portfolio"
    ▼
LivePortfolio.tsx
    │
    │ 2. GET /api/agent/sessions/{id}/portfolio/live
    ▼
Agent Service
    │
    │ 3. Query database for portfolio document
    ├─► 4. SELECT extracted_data FROM documents
    │       WHERE session_id = ? AND document_type = 'portfolio'
    │
    │ 5. Extract holdings (symbols, shares, cost basis)
    │ 6. For each holding, call yfinance_service
    ▼
Yahoo Finance API (yfinance)
    │
    │ 7. Fetch current prices
    │ 8. Return {symbol, price, change, ...}
    ▼
Agent Service
    │
    │ 9. Calculate current values
    │ 10. Calculate gains/losses
    │ 11. Aggregate portfolio totals
    │ 12. Return {holdings[], total_value, gains}
    ▼
LivePortfolio.tsx
    │
    │ 13. Display portfolio table with live data
    ▼
User Browser
```

---

### 5. Market Data Flow

```
User Browser
    │
    │ 1. View market overview
    ▼
MarketOverview.tsx
    │
    │ 2. GET /api/agent/market/indices
    ▼
Agent Service (yfinance_service)
    │
    │ 3. Fetch current S&P 500, Dow, NASDAQ
    ├─► 4. yfinance.Ticker('^GSPC')
    │   5. yfinance.Ticker('^DJI')
    │   6. yfinance.Ticker('^IXIC')
    │
    │ 7. Return {indices: [...]}
    ▼
MarketOverview.tsx
    │
    │ 8. Display indices with charts
    ▼
User Browser
```

**Also supports:**
- `/market/quote/{ticker}` - Individual stock quotes
- `/market/history/{ticker}` - Historical price data for charting

---

## Technology Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.3.1 | UI framework |
| TypeScript | 5.2.2 | Type safety |
| Vite | 5.4.8 | Build tool + dev server |
| Tailwind CSS | 3.4.1 | Utility-first CSS |
| Axios | 1.6.7 | HTTP client |
| Lucide React | 0.344.0 | Icon library |
| Nginx | 1.25 (Alpine) | Web server + proxy |

### Backend - Agent Service

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11 | Runtime |
| FastAPI | 0.115.4 | Web framework |
| SQLAlchemy | 2.0.36 | ORM |
| Psycopg | 3.2.3 | PostgreSQL driver |
| Google Cloud Storage | 2.18.2 | GCS client |
| Vertex AI SDK | 1.71.1 | Document AI + LLM |
| yfinance | 0.2.49 | Market data |
| PyPDF2 | 3.0.1 | PDF processing |
| pypdfium2 | 4.30.1 | PDF flattening |

### Backend - LLM Service

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11 | Runtime |
| FastAPI | 0.115.4 | Web framework |
| ChromaDB | 0.5.20 | Vector database |
| Vertex AI SDK | 1.71.1 | Gemini 2.5 + embeddings |
| LangChain | 0.3.7 | LLM orchestration |
| Sentence Transformers | 3.3.1 | Embeddings (backup) |

### Infrastructure

| Technology | Version | Purpose |
|------------|---------|---------|
| Docker | 24+ | Containerization |
| Docker Compose | 2.20+ | Multi-container orchestration |
| Cloud SQL | PostgreSQL 15 | Managed database |
| Cloud SQL Proxy | 2.11.3 | Database connector |
| Google Cloud Storage | - | Object storage |
| Vertex AI | - | ML platform |

### Development Tools

| Tool | Purpose |
|------|---------|
| Black | Python code formatter |
| Flake8 | Python linter |
| isort | Import organizer |
| pre-commit | Git hook manager |
| pytest | Testing framework |
| coverage.py | Code coverage |

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_external_id ON users(external_id);
```

### Sessions Table

```sql
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
```

### Messages Table

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(session_id),
    role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

### Documents Table

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(session_id),
    document_type VARCHAR(50) NOT NULL,  -- 'w2', '1099', 'portfolio'
    gcs_uri TEXT NOT NULL,
    extracted_data JSONB,  -- Flexible schema for different document types
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_documents_session_id ON documents(session_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_extracted_data ON documents USING gin(extracted_data);
```

**Extracted Data Examples:**

W-2:
```json
{
  "employee_name": "John Doe",
  "employee_ssn": "XXX-XX-1234",
  "wages": 75000.00,
  "federal_tax_withheld": 12000.00
}
```

Portfolio:
```json
{
  "account_number": "12345678",
  "holdings": [
    {"symbol": "AAPL", "shares": 100, "value": 17500.00}
  ],
  "total_value": 125000.00
}
```

---

## Authentication Flow

**Current Status**: Authentication UI components exist but not enforced

**Planned Implementation:**

```
User Browser
    │
    │ 1. Submit email + password
    ▼
Login.tsx
    │
    │ 2. POST /auth/login
    ▼
Agent Service
    │
    │ 3. Verify credentials (database)
    │ 4. Generate JWT token
    │ 5. Return {token, user_id}
    ▼
Frontend
    │
    │ 6. Store JWT in localStorage
    │ 7. Include in all API requests:
    │    Authorization: Bearer <token>
    ▼
Protected Routes
```

**JWT Payload (planned):**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "exp": 1732550400,  // Expiration timestamp
  "iat": 1732464000   // Issued at timestamp
}
```

---

## Deployment Architecture

### Current Setup (Development)

```
Local Machine (Docker Compose)
├── Frontend Container (port 3000)
├── Agent Container (port 8010)
├── LLM Container (port 8001)
└── Cloud SQL Proxy Container (port 5432)
    └── Connects to GCP Cloud SQL
```

### Production Architecture (Milestone 5)

**Planned deployment to Google Cloud Platform:**

```
Cloud Load Balancer (HTTPS)
    │
    ├─► Cloud Run (Frontend)
    │   └─► Cloud Run (Agent API)
    │       └─► Cloud Run (LLM API)
    │
    ├─► Cloud SQL (PostgreSQL)
    ├─► Cloud Storage (GCS)
    └─► Vertex AI
```

**Benefits:**
- Auto-scaling based on traffic
- Managed SSL certificates
- Global load balancing
- Zero-downtime deployments
- Cost-effective (pay-per-use)

---

## Security Considerations

### Current Security Measures

1. **Secrets Management**:
   - All credentials in `secrets/` directory
   - `.gitignore` prevents accidental commits
   - Environment variables for configuration

2. **Database Security**:
   - Cloud SQL with encryption at rest
   - Connection via Cloud SQL Proxy (encrypted)
   - No direct database exposure

3. **Document Storage**:
   - GCS with IAM-controlled access
   - Service account-based authentication
   - Documents isolated by session

4. **API Security**:
   - CORS configured (restrictive in production)
   - Input validation via Pydantic models
   - PDF file type validation

### Planned Security Enhancements

1. **Authentication & Authorization**:
   - JWT-based authentication
   - Role-based access control (RBAC)
   - Session timeout and refresh tokens

2. **Data Protection**:
   - PII encryption in database
   - Document access logs
   - Audit trail for sensitive operations

3. **API Hardening**:
   - Rate limiting (100 req/min)
   - API key authentication
   - Request size limits

4. **Infrastructure**:
   - Network segmentation (VPC)
   - WAF (Web Application Firewall)
   - DDoS protection
   - Secret Manager for credentials

---

## Scalability Considerations

### Current Limitations

- Single instance per service
- In-memory ChromaDB (not shared)
- No caching layer
- Synchronous document processing

### Future Enhancements

1. **Horizontal Scaling**:
   - Multiple frontend instances (Cloud Run)
   - Multiple API instances with load balancing
   - Shared ChromaDB (Chroma Cloud or Vertex AI Vector Search)

2. **Caching**:
   - Redis for session caching
   - CDN for static assets
   - Query result caching

3. **Async Processing**:
   - Cloud Tasks for document processing
   - Pub/Sub for event-driven architecture
   - Background jobs for portfolio updates

4. **Database**:
   - Read replicas for query scaling
   - Connection pooling
   - Query optimization and indexing

---

## Monitoring & Observability

**Planned Implementation:**

1. **Logging**:
   - Structured JSON logs
   - Cloud Logging integration
   - Log levels: DEBUG, INFO, WARNING, ERROR

2. **Metrics**:
   - Request latency (p50, p95, p99)
   - Error rates by endpoint
   - Document processing times
   - LLM query durations

3. **Tracing**:
   - Distributed tracing with Cloud Trace
   - Request flow visualization
   - Performance bottleneck identification

4. **Alerting**:
   - Error rate thresholds
   - Latency spikes
   - Service downtime
   - Cost anomalies

---

## Additional Resources

- **API Documentation**: [docs/API_REFERENCE.md](API_REFERENCE.md)
- **Development Setup**: [docs/DEVELOPMENT.md](DEVELOPMENT.md)
- **Service READMEs**: [src/*/README.md](../src/)
- **Milestone Reports**: [reports/milestone4/README.md](../reports/milestone4/README.md)

---

*This architecture document reflects the current state as of Milestone 4. Future milestones will address production deployment, scalability, and advanced features.*
