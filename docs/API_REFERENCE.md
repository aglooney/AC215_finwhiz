# FinWhiz API Reference

*Last Updated: November 25, 2024*

Complete reference documentation for all FinWhiz backend APIs.

## Table of Contents

- [Overview](#overview)
- [Agent API](#agent-api)
- [LLM API](#llm-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Overview

FinWhiz exposes two main REST APIs:

| Service | Base URL (Docker) | Base URL (Local) | Purpose |
|---------|------------------|------------------|---------|
| **Agent API** | `http://agent:8010` | `http://localhost:8010` | Session management, document uploads, market data |
| **LLM API** | `http://llm:8001` | `http://localhost:8001` | RAG-powered query processing |

### Common Headers

```http
Content-Type: application/json
Accept: application/json
```

### Response Format

All endpoints return JSON responses with consistent structure:

**Success Response:**
```json
{
  "data": { ... },
  "status": "success"
}
```

**Error Response:**
```json
{
  "detail": "Error message",
  "status": "error"
}
```

---

## Agent API

Base URL: `http://localhost:8010`

### Health Check

Check if the Agent service is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok"
}
```

**Example:**
```bash
curl http://localhost:8010/health
```

---

### Session Management

#### Create Session

Create a new chat session for a user.

**Endpoint:** `POST /sessions/`

**Request Body:**
```json
{
  "user_id": "string"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "user_id": "string",
  "created_at": "2024-11-25T10:00:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8010/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123"}'
```

**Notes:**
- Creates user if doesn't exist
- Session IDs are UUIDs
- Sessions persist in database

---

#### Add Message to Session

Log a user or assistant message to a session.

**Endpoint:** `POST /sessions/{session_id}/messages`

**Path Parameters:**
- `session_id` (string, required): Session UUID

**Request Body:**
```json
{
  "role": "user",  // or "assistant"
  "content": "string"
}
```

**Response:**
```json
{
  "message_id": "uuid",
  "session_id": "uuid",
  "role": "user",
  "content": "string",
  "created_at": "2024-11-25T10:00:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8010/sessions/SESSION_ID/messages \
  -H "Content-Type: application/json" \
  -d '{"role": "user", "content": "What is a 401k?"}'
```

---

#### Get Session Context

Retrieve all context for a session (messages, documents, user data).

**Endpoint:** `GET /sessions/{session_id}/context`

**Path Parameters:**
- `session_id` (string, required): Session UUID

**Response:**
```json
{
  "session_id": "uuid",
  "user_id": "string",
  "messages": [
    {
      "role": "user",
      "content": "string",
      "created_at": "timestamp"
    }
  ],
  "documents": [
    {
      "document_type": "w2",
      "extracted_data": { ... },
      "uploaded_at": "timestamp"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8010/sessions/SESSION_ID/context
```

**Use Cases:**
- Retrieve chat history
- Get uploaded documents
- Build context for LLM queries

---

### Document Upload

#### Upload W-2 Form

Upload and extract data from a W-2 PDF document.

**Endpoint:** `POST /sessions/{session_id}/w2`

**Path Parameters:**
- `session_id` (string, required): Session UUID

**Request Body:**
- Content-Type: `multipart/form-data`
- Field: `file` (PDF file)

**Response:**
```json
{
  "document_id": "uuid",
  "document_type": "w2",
  "gcs_uri": "gs://bucket/path/to/file.pdf",
  "extracted_data": {
    "employee_name": "John Doe",
    "employee_ssn": "XXX-XX-1234",
    "employer_name": "Acme Corp",
    "employer_ein": "12-3456789",
    "wages": 75000.00,
    "federal_tax_withheld": 12000.00,
    "social_security_wages": 75000.00,
    "medicare_wages": 75000.00
  },
  "uploaded_at": "2024-11-25T10:00:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8010/sessions/SESSION_ID/w2 \
  -F "file=@/path/to/w2.pdf"
```

**Notes:**
- Only PDF files accepted
- Uses Vertex AI Document AI for extraction
- Stored in GCS bucket
- Flattens PDF forms before extraction

---

#### Upload 1099 Form

Upload and extract data from a 1099 PDF document.

**Endpoint:** `POST /sessions/{session_id}/1099`

**Path Parameters:**
- `session_id` (string, required): Session UUID

**Request Body:**
- Content-Type: `multipart/form-data`
- Field: `file` (PDF file)

**Response:**
```json
{
  "document_id": "uuid",
  "document_type": "1099",
  "gcs_uri": "gs://bucket/path/to/file.pdf",
  "extracted_data": {
    "payer_name": "Big Bank",
    "payer_tin": "12-3456789",
    "recipient_name": "John Doe",
    "recipient_tin": "XXX-XX-1234",
    "interest_income": 1250.00,
    "federal_tax_withheld": 125.00
  },
  "uploaded_at": "2024-11-25T10:00:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8010/sessions/SESSION_ID/1099 \
  -F "file=@/path/to/1099.pdf"
```

---

#### Upload Portfolio Statement

Upload and extract data from a portfolio statement PDF.

**Endpoint:** `POST /sessions/{session_id}/portfolio`

**Path Parameters:**
- `session_id` (string, required): Session UUID

**Request Body:**
- Content-Type: `multipart/form-data`
- Field: `file` (PDF file)

**Response:**
```json
{
  "document_id": "uuid",
  "document_type": "portfolio",
  "gcs_uri": "gs://bucket/path/to/file.pdf",
  "extracted_data": {
    "account_number": "12345678",
    "account_holder": "John Doe",
    "statement_date": "2024-11-01",
    "total_value": 125000.00,
    "holdings": [
      {
        "symbol": "AAPL",
        "shares": 100,
        "value": 17500.00
      },
      {
        "symbol": "GOOGL",
        "shares": 50,
        "value": 14250.00
      }
    ]
  },
  "uploaded_at": "2024-11-25T10:00:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8010/sessions/SESSION_ID/portfolio \
  -F "file=@/path/to/portfolio.pdf"
```

**Supported Formats:**
- Fidelity portfolio statements
- Other formats may be added in the future

---

### Portfolio Features

#### Get Live Portfolio Values

Get real-time market values for portfolio holdings.

**Endpoint:** `GET /sessions/{session_id}/portfolio/live`

**Path Parameters:**
- `session_id` (string, required): Session UUID

**Response:**
```json
{
  "session_id": "uuid",
  "last_updated": "2024-11-25T15:30:00Z",
  "total_value": 132450.00,
  "holdings": [
    {
      "symbol": "AAPL",
      "shares": 100,
      "current_price": 182.50,
      "current_value": 18250.00,
      "cost_basis": 17500.00,
      "gain_loss": 750.00,
      "gain_loss_pct": 4.29
    },
    {
      "symbol": "GOOGL",
      "shares": 50,
      "current_price": 139.75,
      "current_value": 6987.50,
      "cost_basis": 14250.00,
      "gain_loss": -7262.50,
      "gain_loss_pct": -50.96
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8010/sessions/SESSION_ID/portfolio/live
```

**Notes:**
- Requires prior portfolio upload
- Uses Yahoo Finance for current prices
- Updates in real-time
- Calculates gains/losses based on portfolio statement cost basis

---

#### Get Portfolio Analytics

Get detailed analytics and insights for a portfolio.

**Endpoint:** `GET /sessions/{session_id}/portfolio/analytics`

**Path Parameters:**
- `session_id` (string, required): Session UUID

**Response:**
```json
{
  "session_id": "uuid",
  "generated_at": "2024-11-25T15:30:00Z",
  "total_value": 132450.00,
  "total_gain_loss": -6512.50,
  "total_gain_loss_pct": -4.69,
  "asset_allocation": {
    "stocks": {
      "value": 125450.00,
      "percentage": 94.71
    },
    "bonds": {
      "value": 5000.00,
      "percentage": 3.78
    },
    "cash": {
      "value": 2000.00,
      "percentage": 1.51
    }
  },
  "sector_allocation": {
    "Technology": 65.32,
    "Healthcare": 20.15,
    "Finance": 14.53
  },
  "performance": {
    "ytd_return": 8.45,
    "one_year_return": 12.34,
    "volatility": 15.67
  },
  "risk_metrics": {
    "beta": 1.15,
    "sharpe_ratio": 0.85,
    "max_drawdown": -12.45
  }
}
```

**Example:**
```bash
curl http://localhost:8010/sessions/SESSION_ID/portfolio/analytics
```

**Notes:**
- Comprehensive portfolio analysis
- Includes asset allocation, sector breakdown
- Performance metrics calculated
- Risk assessment included

---

### Market Data

#### Get Stock Quote

Get current quote data for a stock ticker.

**Endpoint:** `GET /market/quote/{ticker}`

**Path Parameters:**
- `ticker` (string, required): Stock symbol (e.g., "AAPL", "GOOGL")

**Response:**
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "current_price": 182.50,
  "change": 2.35,
  "change_percent": 1.30,
  "open": 180.15,
  "high": 183.25,
  "low": 179.80,
  "volume": 52435678,
  "market_cap": 2847600000000,
  "pe_ratio": 29.45,
  "dividend_yield": 0.52,
  "52_week_high": 199.62,
  "52_week_low": 164.08,
  "last_updated": "2024-11-25T15:30:00Z"
}
```

**Example:**
```bash
curl http://localhost:8010/market/quote/AAPL
```

**Notes:**
- Uses Yahoo Finance API
- Real-time quotes (15-minute delay for free tier)
- Returns 404 if ticker not found

---

#### Get Market Indices

Get current values for major market indices.

**Endpoint:** `GET /market/indices`

**Response:**
```json
{
  "indices": [
    {
      "symbol": "^GSPC",
      "name": "S&P 500",
      "value": 4567.89,
      "change": 23.45,
      "change_percent": 0.52
    },
    {
      "symbol": "^DJI",
      "name": "Dow Jones Industrial Average",
      "value": 35789.12,
      "change": 145.67,
      "change_percent": 0.41
    },
    {
      "symbol": "^IXIC",
      "name": "NASDAQ Composite",
      "value": 14256.78,
      "change": 78.90,
      "change_percent": 0.56
    }
  ],
  "last_updated": "2024-11-25T15:30:00Z"
}
```

**Example:**
```bash
curl http://localhost:8010/market/indices
```

**Notes:**
- Returns S&P 500, Dow Jones, NASDAQ
- Updated in real-time
- Useful for market overview dashboards

---

#### Get Historical Stock Data

Get historical price data for a stock.

**Endpoint:** `GET /market/history/{ticker}`

**Path Parameters:**
- `ticker` (string, required): Stock symbol

**Query Parameters:**
- `period` (string, optional): Time period (default: "1mo")
  - Valid values: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
- `interval` (string, optional): Data interval (default: "1d")
  - Valid values: "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"

**Response:**
```json
{
  "symbol": "AAPL",
  "period": "1mo",
  "interval": "1d",
  "data": [
    {
      "date": "2024-10-25",
      "open": 178.50,
      "high": 180.25,
      "low": 177.80,
      "close": 179.92,
      "volume": 45678901,
      "adj_close": 179.92
    },
    {
      "date": "2024-10-26",
      "open": 180.00,
      "high": 182.15,
      "low": 179.50,
      "close": 181.45,
      "volume": 48901234,
      "adj_close": 181.45
    }
  ]
}
```

**Example:**
```bash
# Get 1 month of daily data
curl "http://localhost:8010/market/history/AAPL?period=1mo&interval=1d"

# Get 1 year of weekly data
curl "http://localhost:8010/market/history/GOOGL?period=1y&interval=1wk"
```

**Notes:**
- Historical data from Yahoo Finance
- Useful for charting and analysis
- Adjust period/interval based on use case

---

## LLM API

Base URL: `http://localhost:8001`

### Health Check

Check if the LLM service is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok"
}
```

**Example:**
```bash
curl http://localhost:8001/health
```

---

### Query Processing

#### Submit Query

Submit a natural language query and get an AI-powered response.

**Endpoint:** `POST /query`

**Request Body:**
```json
{
  "query": "string",
  "session_id": "uuid",
  "top_k": 5
}
```

**Parameters:**
- `query` (string, required): User's question
- `session_id` (string, required): Session UUID for context
- `top_k` (integer, optional): Number of context documents to retrieve (default: 5)

**Response:**
```json
{
  "response": "string",  // AI-generated answer
  "sources": [
    {
      "content": "string",
      "metadata": {
        "source": "IRS Publication 590-B",
        "url": "https://www.irs.gov/...",
        "chunk_id": "doc123_chunk5"
      },
      "score": 0.92
    }
  ],
  "session_context_used": true,
  "model": "gemini-2.5-flash-001"
}
```

**Example:**
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the tax implications of a Roth IRA?",
    "session_id": "SESSION_ID",
    "top_k": 5
  }'
```

**Response Flow:**
1. Query is embedded using Vertex AI
2. Similar documents retrieved from ChromaDB
3. Session context fetched from Agent API
4. Combined context sent to Gemini 2.5
5. Response generated with citations
6. Sources ranked by relevance score

**Notes:**
- Powered by Gemini 2.5 Flash
- Uses RAG (Retrieval-Augmented Generation)
- Includes session-specific context (uploaded documents)
- Returns source citations for transparency

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request parameters |
| 404 | Not Found | Resource not found (session, document, ticker) |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server-side error |
| 502 | Bad Gateway | Service unavailable (backend down) |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  "detail": "Detailed error message",
  "status": "error",
  "error_code": "RESOURCE_NOT_FOUND",
  "timestamp": "2024-11-25T15:30:00Z"
}
```

### Common Errors

#### Session Not Found
```json
{
  "detail": "Session not found",
  "status": "error"
}
```
**Status:** 404
**Cause:** Invalid or non-existent session_id

#### Invalid File Format
```json
{
  "detail": "Only PDF files are supported",
  "status": "error"
}
```
**Status:** 400
**Cause:** Uploaded file is not PDF

#### Ticker Not Found
```json
{
  "detail": "Ticker symbol 'INVALID' not found",
  "status": "error"
}
```
**Status:** 404
**Cause:** Invalid stock ticker

#### Service Unavailable
```json
{
  "detail": "LLM service unavailable",
  "status": "error"
}
```
**Status:** 503
**Cause:** Backend service down or overloaded

---

## Rate Limiting

**Current Status:** Not implemented

**Future Implementation:**
- 100 requests/minute per IP
- 1000 requests/hour per user
- 10 document uploads/hour per session

---

## Authentication

**Current Status:** Not implemented

All endpoints are currently open. Future versions will implement:
- JWT-based authentication
- API key authentication for programmatic access
- OAuth 2.0 for third-party integrations

---

## Pagination

**Current Status:** Not implemented for list endpoints

Future list endpoints will support:
```
GET /sessions?page=1&limit=20
```

---

## Webhooks

**Current Status:** Not implemented

Future webhook support for:
- Document processing complete
- Portfolio value alerts
- Market movement notifications

---

## Additional Notes

### CORS

Both APIs have CORS enabled for:
- **Origins:** `*` (all origins in development)
- **Methods:** All HTTP methods
- **Headers:** All headers

**Production:** Will be restricted to specific domains

### Content-Type

All POST/PUT requests must include:
```http
Content-Type: application/json
```

Except file uploads which use:
```http
Content-Type: multipart/form-data
```

### Timeouts

- **Standard Requests:** 30 seconds
- **Document Processing:** 120 seconds
- **LLM Queries:** 60 seconds

---

## SDK / Client Libraries

**Current Status:** Not available

**Future:**
- Python SDK
- JavaScript/TypeScript SDK
- REST client examples

---

## API Versioning

**Current Version:** v1 (implicit)

**Future:** Explicit versioning via URL:
```
http://localhost:8010/v1/sessions/
http://localhost:8010/v2/sessions/
```

---

## Support

For API issues or questions:

1. Check service health endpoints
2. Review service logs: `docker logs finwhiz_agent` or `docker logs finwhiz_llm`
3. Verify request format matches examples above
4. Check network connectivity between services
5. Review `.env` configuration

---

*For development setup, see [docs/DEVELOPMENT.md](DEVELOPMENT.md)*
*For architecture details, see [docs/ARCHITECTURE.md](ARCHITECTURE.md)*
