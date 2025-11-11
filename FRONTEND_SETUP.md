# FinWhiz UI Setup Guide

This guide will help you spin up the complete FinWhiz UI with all backend services.

## Quick Start

### 1. Build and Start All Services

From the project root directory:

```bash
docker-compose up --build
```

This will start:
- **postgres** (port 5432) - Database
- **llm** (port 8001) - RAG/LLM service with Gemini 2.5
- **agent** (port 8010) - Session and document processing
- **frontend** (port 3000) - Web UI
- **query_client** - CLI tool (optional)

### 2. Access the Application

Once all services are healthy, open your browser:

```
http://localhost:3000
```

## First Time Setup

### Prerequisites

Ensure you have:
- Docker Desktop (or Docker Engine) installed
- GCP service account credentials in `secrets/` directory
- `.env` file configured (see below)

### Environment Configuration

Your `.env` file should contain:

```bash
# GCS Configuration
GOOGLE_APPLICATION_CREDENTIALS=secrets/service-account-key.json
BUCKET_CREDENTIALS=secrets/service-account-key.json
VERTEXAI_CREDENTIALS=secrets/vertexai-service-account.json
GCS_BUCKET=fw_ws
GCS_PREFIX=chroma_storage
USER_UPLOAD_BUCKET=fw_user_uploads

# Database
DATABASE_URL=postgresql+psycopg://finwhiz:finwhiz@postgres:5432/finwhiz

# Service URLs (for internal container communication)
AGENT_URL=http://agent:8010
LLM_URL=http://llm:8001

# Chroma Configuration
CHROMA_PATH=/app/src/chroma_storage
COLLECTION_NAME=finwhiz_docs
```

## Using the Application

### Onboarding

1. Enter your age (e.g., 30)
2. Enter your target retirement age (e.g., 65)
3. Describe your investment goal
4. Select your risk tolerance (Conservative, Moderate, or Aggressive)

### Portfolio Recommendations

After onboarding, you'll see personalized portfolio allocations:
- **Stocks** - Equity allocation
- **Bonds** - Fixed income allocation
- **Cash** - Liquid reserves

The allocations are calculated based on:
- Your age
- Years to retirement
- Risk tolerance level

### Chat Interface

Ask questions about:
- Financial concepts and strategies
- Retirement planning
- Tax-related questions
- Investment advice
- Document-specific questions (after uploading)

Example questions:
- "What is a Roth IRA and should I contribute to one?"
- "How much should I save for retirement?"
- "Explain the tax implications of my W-2"

### Document Upload

1. Click the "Upload Documents" tab
2. Select document type (W-2 or 1099)
3. Upload a PDF file
4. The system will:
   - Extract key fields using AI
   - Store the document securely in GCS
   - Make the data available for personalized responses

After uploading, ask questions like:
- "What is my total income from the form I uploaded?"
- "Based on my W-2, what tax deductions might I be eligible for?"

## Architecture Overview

```
┌─────────────┐
│   Browser   │
│ localhost:  │
│    3000     │
└──────┬──────┘
       │
       │ HTTP
       ▼
┌─────────────────┐
│    Frontend     │
│  (Nginx/React)  │
│                 │
│  /api/agent/*   │────┐
│  /api/llm/*     │────┤
└─────────────────┘    │
                       │
       ┌───────────────┴───────────────┐
       │                               │
       ▼                               ▼
┌─────────────┐                ┌─────────────┐
│   Agent API │                │   LLM API   │
│   :8010     │                │   :8001     │
│             │                │             │
│ - Sessions  │                │ - RAG       │
│ - Messages  │                │ - Chroma DB │
│ - Documents │                │ - Gemini    │
└──────┬──────┘                └─────────────┘
       │
       ▼
┌─────────────┐
│  Postgres   │
│   :5432     │
│             │
│ - Sessions  │
│ - Messages  │
│ - Documents │
└─────────────┘
```

## Troubleshooting

### Frontend Not Loading

```bash
# Check if frontend container is running
docker ps | grep finwhiz_frontend

# View frontend logs
docker logs finwhiz_frontend

# Rebuild frontend only
docker-compose up --build frontend
```

### API Connection Issues

```bash
# Check if backend services are healthy
docker ps

# View agent logs
docker logs finwhiz_agent

# View LLM logs
docker logs finwhiz_llm
```

### CORS or Proxy Issues

The Nginx configuration in `src/frontend/nginx.conf` handles API proxying:
- `/api/agent/*` → `http://agent:8010/`
- `/api/llm/*` → `http://llm:8001/`

If you see CORS errors, ensure all services are on the same Docker network (`finwhiz_network`).

### Service Health Checks

```bash
# Agent health
curl http://localhost:8010/health

# LLM health
curl http://localhost:8001/health

# Frontend health
curl http://localhost:3000
```

## Development Workflow

### Frontend Development Only

If you want to work on the frontend without rebuilding everything:

```bash
# Start backend services
docker-compose up postgres llm agent

# In another terminal, run frontend in dev mode
cd src/frontend
npm install
npm run dev
```

The dev server will run on `http://localhost:5173` with hot reload.

### Making Changes

1. **UI Changes**: Edit files in `src/frontend/src/`
   - Components: `src/components/`
   - Pages: `src/pages/`
   - Styles: `src/index.css`

2. **API Integration**: Edit `src/frontend/src/services/api.ts`

3. **Types**: Edit `src/frontend/src/types/index.ts`

4. **Backend Changes**: Edit respective service files and rebuild:
   ```bash
   docker-compose up --build agent  # or llm
   ```

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## Production Deployment

The current setup is suitable for local development. For production:

1. Set proper environment variables
2. Use production-grade secrets management
3. Enable HTTPS with SSL certificates
4. Configure proper CORS policies
5. Set up monitoring and logging
6. Use managed database (Cloud SQL)
7. Deploy to GCP (Cloud Run or GKE)

## Support

For issues or questions:
- Check service logs: `docker logs <container_name>`
- Review the README files in each service directory
- Ensure all prerequisites are met (GCP credentials, .env file)
