# Agentic User Data Processing

*Last Updated: November 25, 2024*

This package houses the agent microservice that provides session management, document processing, and market data integration for FinWhiz.

## Features

### Session Management
- Track active chat sessions and message history
- Store user context for personalized AI responses
- Provide conversation history for LLM context

### Document Processing
- Accept W-2, 1099, and portfolio PDF uploads
- Store raw (flattened) files in Google Cloud Storage
- Extract structured fields via Vertex AI Document AI
- Support for multiple document types per session

### Portfolio Features
- Real-time portfolio valuation with live market data
- Portfolio analytics (asset allocation, gains/losses)
- Integration with uploaded portfolio statements

### Market Data
- Real-time stock quotes via Yahoo Finance
- Major market indices (S&P 500, Dow, NASDAQ)
- Historical price data for charting and analysis

---

## High-Level Components

| File/Directory | Purpose |
|----------------|---------|
| `app.py` | FastAPI entrypoint exposing all REST API endpoints |
| `db.py` | SQLAlchemy session management and lifecycle hooks |
| `models.py` | Database schema (users, sessions, messages, documents) |
| `schemas.py` | Pydantic request/response models for API validation |
| `services/` | Helper modules for various service operations |
| `services/context.py` | Assemble session context for LLM queries |
| `services/storage.py` | GCS upload/download operations |
| `services/extraction.py` | W-2 field extraction via Vertex AI |
| `services/extraction_1099.py` | 1099 field extraction via Vertex AI |
| `services/extraction_portfolio.py` | Portfolio statement parsing |
| `services/pdf_utils.py` | PDF flattening and preprocessing |
| `services/yfinance_service.py` | Yahoo Finance integration for market data |

---

## API Endpoints

### Health Check
- `GET /health` - Service health status

### Session Management
- `POST /sessions/` - Create new session
- `POST /sessions/{session_id}/messages` - Add message to session
- `GET /sessions/{session_id}/context` - Retrieve session context

### Document Upload
- `POST /sessions/{session_id}/w2` - Upload W-2 form (PDF)
- `POST /sessions/{session_id}/1099` - Upload 1099 form (PDF)
- `POST /sessions/{session_id}/portfolio` - Upload portfolio statement (PDF)

### Portfolio Features (NEW)
- `GET /sessions/{session_id}/portfolio/live` - Real-time portfolio values
- `GET /sessions/{session_id}/portfolio/analytics` - Portfolio analysis and metrics

### Market Data (NEW)
- `GET /market/quote/{ticker}` - Get stock quote (e.g., AAPL, GOOGL)
- `GET /market/indices` - Get major market indices
- `GET /market/history/{ticker}` - Get historical price data

For complete API documentation with request/response examples, see [docs/API_REFERENCE.md](../../docs/API_REFERENCE.md).

---

## Environment Configuration

Environment variables are loaded via `.env` (see repository root):

```bash
# Database
DATABASE_URL=postgresql+psycopg://finwhiz:password@cloudsql-proxy:5432/finwhiz
DB_USER=finwhiz
DB_PASS=your_password
DB_NAME=finwhiz
DB_HOST=cloudsql-proxy

# GCS Storage
GOOGLE_APPLICATION_CREDENTIALS=secrets/service-account-key.json
USER_UPLOAD_BUCKET=fw_user_uploads

# Market Data
MARKET_DATA_PROVIDER=yfinance  # Yahoo Finance
```

**Important**: Secrets belong in the local `secrets/` folder (gitignored) and are mounted into the container at runtime.

---

## Supported Document Types

The service supports multiple document types per session:

### 1. W-2 Forms
**Endpoint**: `POST /sessions/{session_id}/w2`

**Extracted Fields**:
- Employee name, SSN
- Employer name, EIN
- Wages, tips, other compensation
- Federal tax withheld
- Social Security wages and tax
- Medicare wages and tax
- State wages and tax

### 2. 1099 Forms
**Endpoint**: `POST /sessions/{session_id}/1099`

**Extracted Fields**:
- Payer name and TIN
- Recipient name and TIN
- Interest income
- Federal tax withheld
- State tax withheld

### 3. Portfolio Statements
**Endpoint**: `POST /sessions/{session_id}/portfolio`

**Extracted Fields**:
- Account number and holder name
- Statement date
- Total portfolio value
- Holdings (symbol, shares, value)
- Asset allocation

**Supported Formats**: Fidelity portfolio statements (other brokers may be added in the future)

Each document type is processed independently and made available in the session context for personalized AI responses.

---

## Document Processing Flow

1. **Upload**: Client uploads PDF via multipart/form-data
2. **Flatten**: PDF forms are flattened using `pypdfium2` to ensure compatibility
3. **Store**: Flattened PDF uploaded to GCS bucket (`fw_user_uploads/session_id/filename.pdf`)
4. **Extract**: Vertex AI Document AI processes the PDF and extracts structured fields
5. **Save**: Extracted data stored in database as JSONB in `documents.extracted_data`
6. **Context**: Document data available via `/sessions/{id}/context` for LLM queries

---

## Live Portfolio Valuation

The `/portfolio/live` endpoint provides real-time portfolio valuation:

1. Retrieves uploaded portfolio statement from database
2. Extracts holdings (symbol, shares, cost basis)
3. Fetches current prices from Yahoo Finance
4. Calculates current values and gains/losses
5. Returns comprehensive portfolio snapshot

**Example Response**:
```json
{
  "total_value": 132450.00,
  "total_gain_loss": 7450.00,
  "holdings": [
    {
      "symbol": "AAPL",
      "shares": 100,
      "current_price": 182.50,
      "current_value": 18250.00,
      "cost_basis": 17500.00,
      "gain_loss": 750.00,
      "gain_loss_pct": 4.29
    }
  ]
}
```

---

## Market Data Integration

### Stock Quotes
Real-time stock quotes via Yahoo Finance:
```bash
curl http://localhost:8010/market/quote/AAPL
```

Returns price, change, volume, market cap, P/E ratio, and more.

### Market Indices
Current values for major indices:
```bash
curl http://localhost:8010/market/indices
```

Returns S&P 500, Dow Jones, and NASDAQ with current values and changes.

### Historical Data
Historical price data for charting:
```bash
curl "http://localhost:8010/market/history/AAPL?period=1mo&interval=1d"
```

Supports various periods (1d to max) and intervals (1m to 3mo).

---

## Manual Smoke Test

### 1. Start Services

```bash
docker-compose up --build agent cloudsql-proxy
```

### 2. Create Session

```bash
SESSION_ID=$(curl -s -X POST http://127.0.0.1:8010/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user-123"}' | jq -r '.session_id')
echo "Session ID: $SESSION_ID"
```

### 3. Upload Documents

```bash
# Upload W-2
curl -X POST http://127.0.0.1:8010/sessions/$SESSION_ID/w2 \
  -F "file=@src/synthetic_data/w2/outputs/w2_000.pdf"

# Upload 1099
curl -X POST http://127.0.0.1:8010/sessions/$SESSION_ID/1099 \
  -F "file=@src/synthetic_data/int_1099/outputs/1099int_001.pdf"

# Upload portfolio
curl -X POST http://127.0.0.1:8010/sessions/$SESSION_ID/portfolio \
  -F "file=@path/to/fidelity_statement.pdf"
```

### 4. Get Session Context

```bash
curl http://127.0.0.1:8010/sessions/$SESSION_ID/context | jq
```

The response will include `w2_fields`, `form1099_fields`, and `portfolio_fields` with extracted data from each document type.

### 5. Get Live Portfolio Values

```bash
curl http://127.0.0.1:8010/sessions/$SESSION_ID/portfolio/live | jq
```

### 6. Get Market Data

```bash
# Stock quote
curl http://127.0.0.1:8010/market/quote/AAPL | jq

# Market indices
curl http://127.0.0.1:8010/market/indices | jq

# Historical data (1 month, daily)
curl "http://127.0.0.1:8010/market/history/GOOGL?period=1mo&interval=1d" | jq
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    external_id VARCHAR UNIQUE,
    user_id VARCHAR,
    created_at TIMESTAMP
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP
);
```

### Messages Table
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(session_id),
    role VARCHAR(50),  -- 'user' or 'assistant'
    content TEXT,
    created_at TIMESTAMP
);
```

### Documents Table
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(session_id),
    document_type VARCHAR(50),  -- 'w2', '1099', 'portfolio'
    gcs_uri TEXT,
    extracted_data JSONB,  -- Flexible schema per document type
    created_at TIMESTAMP
);
```

---

## Testing

### Unit Tests
```bash
pytest src/agentic_user_data_processing/tests/
```

### Integration Tests
```bash
pytest tests/integration/test_agent_file_upload_workflow.py
```

### Cloud Tests
```bash
# Requires running Cloud SQL proxy
pytest tests/cloud/test_agent_db.py
```

---

## Development

### Running Locally (with Docker)

```bash
docker-compose up --build agent
```

The service will be available at http://localhost:8010

### Running Tests with Coverage

```bash
pytest src/agentic_user_data_processing/tests/ --cov=src/agentic_user_data_processing --cov-report=html
```

### Debugging

View logs:
```bash
docker logs finwhiz_agent -f
```

Access database:
```bash
psql postgresql://finwhiz:password@localhost:5432/finwhiz
```

---

## Dependencies

Key Python packages:
- **FastAPI** (0.115.4) - Web framework
- **SQLAlchemy** (2.0.36) - ORM
- **Psycopg** (3.2.3) - PostgreSQL driver
- **Google Cloud Storage** (2.18.2) - GCS client
- **Vertex AI SDK** (1.71.1) - Document AI + LLM
- **yfinance** (0.2.49) - Yahoo Finance API
- **PyPDF2** (3.0.1) - PDF processing
- **pypdfium2** (4.30.1) - PDF flattening

See `pyproject.toml` for complete dependency list.

---

## Related Documentation

- **API Reference**: [docs/API_REFERENCE.md](../../docs/API_REFERENCE.md)
- **Architecture**: [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md)
- **Development Guide**: [docs/DEVELOPMENT.md](../../docs/DEVELOPMENT.md)
- **Main README**: [README.md](../../README.md)

---

*For issues or questions, check the logs and review the troubleshooting section in the development guide.*
