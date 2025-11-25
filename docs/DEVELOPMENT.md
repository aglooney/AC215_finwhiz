# FinWhiz - Development Guide

*Last Updated: November 25, 2024*

This guide provides comprehensive instructions for setting up and developing FinWhiz locally.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Development Options](#development-options)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Code Quality](#code-quality)

---

## Prerequisites

### Required Software

- **Docker Desktop** (or Docker Engine) + docker-compose plugin
- **Node.js 20+** (for local frontend development)
- **Python 3.11+** (for backend development)
- **Git** for version control

### Cloud Setup

- **GCP Service Account** with access to:
  - Vertex AI
  - Cloud Storage (GCS buckets)
  - Cloud SQL
- **Credentials**: JSON key files stored in `secrets/` directory

---

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/finwhiz.git
cd finwhiz
```

### 2. Configure Environment Variables

Create a `.env` file at the repository root (use `.env.example` as template):

```bash
# GCP Credentials
GOOGLE_APPLICATION_CREDENTIALS=secrets/service-account-key.json
BUCKET_CREDENTIALS=secrets/service-account-key.json
VERTEXAI_CREDENTIALS=secrets/vertexai-service-account.json

# GCS Configuration
GCS_BUCKET=fw_ws
GCS_PREFIX=chroma_storage
USER_UPLOAD_BUCKET=fw_user_uploads

# Database (Cloud SQL via Proxy)
DATABASE_URL=postgresql+psycopg://finwhiz:password@cloudsql-proxy:5432/finwhiz
DB_USER=finwhiz
DB_PASS=your_password
DB_NAME=finwhiz
DB_HOST=cloudsql-proxy

# Service URLs (Docker internal communication)
AGENT_URL=http://agent:8010
LLM_URL=http://llm:8001

# Chroma Configuration
CHROMA_PATH=/app/src/chroma_storage
COLLECTION_NAME=finwhiz_docs

# Feature Flags
ENABLE_LIVE_PORTFOLIO=true
MARKET_DATA_PROVIDER=yfinance
```

### 3. Set Up Secrets Directory

```bash
mkdir -p secrets
# Copy your GCP service account keys to secrets/
cp ~/Downloads/service-account-key.json secrets/
cp ~/Downloads/vertexai-service-account.json secrets/
cp ~/Downloads/proxy-key.json secrets/
```

**Important**: Never commit files in `secrets/` to version control!

---

## Development Options

You have two main development approaches:

### Option 1: Local Frontend + Docker Backend (Recommended)

**Advantages:**
- Fast frontend hot-reload
- Full backend functionality
- Best for UI/UX development

**Use when:**
- Developing React components
- Iterating on UI/styling
- Testing frontend-backend integration

### Option 2: Full Docker Development

**Advantages:**
- Exact production environment
- No local dependencies needed
- Best for backend development

**Use when:**
- Developing backend services
- Testing full system integration
- Debugging container issues

---

## Running the Application

### Option 1: Local Frontend Development

#### Step 1: Start Backend Services

```bash
# From project root
./start-dev.sh
```

This script will:
- Clean up any existing containers
- Start Cloud SQL proxy, Agent, and LLM services in Docker
- Wait for all services to be healthy
- Display service URLs

**Expected output:**
```
🎉 All backend services are running!

Service Status:
  ✅ Cloud SQL Proxy: localhost:5432
  ✅ Agent API:       http://localhost:8010
  ✅ LLM API:         http://localhost:8001
```

#### Step 2: Start Frontend

**In a NEW terminal:**

```bash
cd src/frontend
./dev-setup.sh
```

This will:
- Check Node.js and npm installation
- Install dependencies if needed
- Verify backend services are running
- Start Vite dev server on port 3000

#### Step 3: Access the Application

Open your browser to: **http://localhost:3000**

---

### Option 2: Full Docker Development

Run all services in Docker (including frontend):

```bash
# From project root
docker-compose up --build
```

**Service Endpoints:**
- Frontend: http://localhost:3000
- Agent API: http://localhost:8010
- LLM API: http://localhost:8001
- Database: localhost:5432 (via Cloud SQL proxy)

**To run in detached mode:**
```bash
docker-compose up -d
```

**To view logs:**
```bash
docker-compose logs -f
```

---

## Testing

### Running Unit Tests

```bash
# From repository root
pytest                # Run all unit tests with coverage
pytest -m system      # Run system tests (requires running services)
```

### Running Full Test Suite

To mirror the CI pipeline locally (unit + integration tests with combined coverage):

```bash
./scripts/run_tests_with_coverage.sh
```

This script:
- Cleans prior `.coverage*` files
- Runs unit and integration test suites
- Generates merged HTML and XML reports in `coverage/`

### Test Scripts

```bash
# Test full pipeline (session creation, document upload, query)
bash test_full_pipeline.sh

# Test portfolio upload feature
bash test_portfolio_upload.sh

# Test GCS connectivity
cd src/gcp_storage
python test_gcs.py
```

### Integration Testing

#### Test 1: Create a Session
```javascript
// Open browser console at http://localhost:3000
const userId = crypto.randomUUID();
const response = await fetch('/api/agent/sessions/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: userId })
});
const session = await response.json();
console.log('Session created:', session);
```

#### Test 2: Query the LLM
```javascript
// Replace SESSION_ID with actual value
const response = await fetch('/api/llm/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'What is a W-2 form?',
    session_id: 'SESSION_ID',
    top_k: 5
  })
});
const result = await response.json();
console.log('LLM Response:', result);
```

---

## Development Workflow

### Daily Development Routine

1. **Start backend services once per session:**
   ```bash
   ./start-dev.sh
   ```
   Leave this running in the background.

2. **Work on frontend:**
   ```bash
   cd src/frontend
   npm run dev
   ```

3. **Make changes** to React components
   - Changes hot-reload automatically
   - Check browser console for errors

4. **View backend logs when debugging:**
   ```bash
   # In another terminal
   docker-compose logs -f agent llm
   ```

5. **Stop everything when done:**
   ```bash
   docker-compose down
   ```

### Backend Development

When working on backend services (Agent or LLM):

1. **Make code changes** in `src/agentic_user_data_processing/` or `src/llm/`

2. **Rebuild specific service:**
   ```bash
   docker-compose up --build agent  # or llm
   ```

3. **View logs:**
   ```bash
   docker logs finwhiz_agent -f
   ```

4. **Test API endpoints:**
   ```bash
   # Health checks
   curl http://localhost:8010/health
   curl http://localhost:8001/health

   # Create session
   curl -X POST http://localhost:8010/sessions/ \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test-user"}'
   ```

### Frontend Development

When working on frontend:

1. **Components**: Edit files in `src/frontend/src/components/`
2. **Pages**: Edit files in `src/frontend/src/pages/`
3. **Styling**: Edit `src/frontend/src/index.css`
4. **API Integration**: Edit `src/frontend/src/services/api.ts`
5. **Types**: Edit `src/frontend/src/types/index.ts`

**Hot Reload:**
- Changes are reflected instantly
- Check terminal for build errors
- Check browser console for runtime errors

### Database Development

When working with database models or migrations:

1. **Access database via proxy:**
   ```bash
   psql postgresql://finwhiz:password@localhost:5432/finwhiz
   ```

2. **View database logs:**
   ```bash
   docker logs finwhiz_cloudsql_proxy
   ```

3. **Reset database** (development only):
   - Update models in `src/agentic_user_data_processing/models.py`
   - Rebuild agent service
   - Database tables recreate on startup

---

## Troubleshooting

### Issue: Backend Services Not Running

**Symptoms:**
- Frontend can't connect to APIs
- 502 Bad Gateway errors

**Solution:**
```bash
# Check if containers are running
docker ps | grep finwhiz

# If not running, start them
./start-dev.sh

# Check service health
curl http://localhost:8010/health  # Should return {"status":"ok"}
curl http://localhost:8001/health  # Should return {"status":"ok"}
```

### Issue: docker-compose up Fails

**Check logs:**
```bash
# View all logs
docker-compose logs

# View specific service
docker logs finwhiz_agent
docker logs finwhiz_llm
docker logs finwhiz_cloudsql_proxy
```

**Common fixes:**
```bash
# Clean up and rebuild
docker-compose down
docker-compose build --no-cache
./start-dev.sh
```

### Issue: Frontend Can't Connect to Backend

**Check:**

1. **Verify proxy configuration:**
   - Open browser DevTools → Console
   - Look for: `BASE_URL: http://localhost:3000`
   - Check Network tab for failed `/api/*` requests

2. **Verify backend health:**
   ```bash
   curl http://localhost:8010/health
   curl http://localhost:8001/health
   ```

3. **Check Nginx configuration** (if running full Docker):
   - Review `src/frontend/nginx.conf`
   - Ensure `/api/agent/*` proxies to `http://agent:8010`
   - Ensure `/api/llm/*` proxies to `http://llm:8001`

### Issue: Document Uploads Fail

**Check:**

1. **File format**: Must be PDF
2. **GCS credentials**: Verify `.env` has correct credentials
3. **Agent service logs**:
   ```bash
   docker logs finwhiz_agent
   ```
4. **GCS bucket permissions**: Ensure service account has write access

### Issue: Chat Doesn't Work

**Check:**

1. **Browser console** for JavaScript errors
2. **LLM service is running**:
   ```bash
   curl http://localhost:8001/health
   ```
3. **Chroma database initialized**:
   ```bash
   docker logs finwhiz_llm | grep Chroma
   ```
4. **Vertex AI credentials** are valid

### Issue: Cloud SQL Proxy Connection Fails

**Symptoms:**
- Agent service can't connect to database
- "connection refused" errors

**Solution:**
```bash
# Check proxy logs
docker logs finwhiz_cloudsql_proxy

# Verify proxy-key.json exists and is valid
ls -la secrets/proxy-key.json

# Restart proxy
docker-compose restart cloudsql-proxy
```

### Issue: Port Already in Use

**Symptoms:**
- "port is already allocated" error

**Solution:**
```bash
# Find process using port (e.g., 3000)
lsof -i :3000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml:
# ports:
#   - "3001:80"  # Change 3000 to 3001
```

### Issue: Hot Reload Not Working

**Frontend:**
```bash
# Stop and restart dev server
cd src/frontend
npm run dev
```

**Backend:**
```bash
# Rebuild and restart service
docker-compose up --build agent
```

---

## Code Quality

### Linting and Formatting

We use [pre-commit](https://pre-commit.com) for consistent code quality:

#### One-Time Setup

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install
pre-commit install --hook-type pre-push
```

#### Running Manually

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

#### Git Workflow with Pre-commit

```bash
git add <files>
git commit -m "Your message"
# Pre-commit runs automatically (Black, Flake8)

git push
# Pre-push hook runs (checks whole repo)
```

If pre-commit finds issues:
1. Fix reported issues
2. Re-stage files: `git add <files>`
3. Commit/push again

#### Tools Used

- **Black**: Python code formatter
- **Flake8**: Python linter
- **isort**: Import statement organizer

Configuration files:
- `.pre-commit-config.yaml`
- `.flake8`
- `pyproject.toml`

### Frontend Linting

```bash
cd src/frontend

# Run ESLint
npm run lint

# Fix auto-fixable issues
npm run lint:fix

# Type checking
npm run type-check
```

---

## Viewing Logs

### All Services
```bash
docker-compose logs -f
```

### Specific Service
```bash
docker-compose logs -f agent
docker-compose logs -f llm
docker-compose logs -f cloudsql-proxy
docker-compose logs -f frontend
```

### Frontend (when running locally)
Check the terminal where you ran `npm run dev`

---

## Stopping Services

### Stop Backend Docker Services
```bash
docker-compose down
```

### Stop Frontend (local dev)
Press `Ctrl+C` in the terminal running the dev server

### Clean Restart (removes volumes)
```bash
docker-compose down -v
```

---

## Common Commands Reference

| Task | Command |
|------|---------|
| Start backends | `./start-dev.sh` |
| Start frontend (local) | `cd src/frontend && npm run dev` |
| Start all services (Docker) | `docker-compose up` |
| View logs | `docker-compose logs -f` |
| Stop all | `docker-compose down` |
| Rebuild service | `docker-compose build --no-cache <service>` |
| Check health | `curl http://localhost:8010/health` |
| Clean restart | `docker-compose down && ./start-dev.sh` |
| Run tests | `pytest` |
| Run with coverage | `./scripts/run_tests_with_coverage.sh` |
| Format code | `pre-commit run --all-files` |

---

## Additional Resources

- **Frontend Details**: [src/frontend/DEVELOPMENT.md](../src/frontend/DEVELOPMENT.md)
- **API Reference**: [docs/API_REFERENCE.md](API_REFERENCE.md)
- **Architecture**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- **Docker Compose**: [docker-compose.yml](../docker-compose.yml)
- **Environment**: [.env.example](../.env.example)

---

## Getting Help

If you encounter issues not covered here:

1. **Check service logs**: `docker-compose logs <service>`
2. **Verify `.env` configuration**
3. **Ensure all ports are available** (3000, 5432, 8001, 8010)
4. **Try clean restart**: `docker-compose down -v && docker-compose up --build`
5. **Check service READMEs** in respective `src/` directories
6. **Review GitHub issues** for known problems

---

*For deployment instructions, see [docs/DEPLOYMENT.md](DEPLOYMENT.md)*
*For API documentation, see [docs/API_REFERENCE.md](API_REFERENCE.md)*
