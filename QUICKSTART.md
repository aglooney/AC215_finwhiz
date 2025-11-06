# FinWhiz - Quick Start Guide

## Prerequisites

- Docker & Docker Compose installed
- Node.js 20+ installed (for local frontend development)
- Google Cloud credentials configured (`.env` file in project root)

## Option 1: Local Frontend Development (Recommended)

This setup runs backend services in Docker while running the frontend locally for fast hot-reload.

### Step 1: Start Backend Services

```bash
# From project root
./start-dev.sh
```

This script will:
- Clean up any existing containers
- Start PostgreSQL, Agent, and LLM services in Docker
- Wait for all services to be healthy
- Show you the service URLs

**Expected output:**
```
🎉 All backend services are running!

Service Status:
  ✅ PostgreSQL: http://localhost:5432
  ✅ Agent API:  http://localhost:8010
  ✅ LLM API:    http://localhost:8001
```

### Step 2: Start Frontend

**In a NEW terminal:**

```bash
cd src/frontend
./dev-setup.sh
```

This will:
- Check Node.js and npm are installed
- Install dependencies if needed
- Verify backend services are running
- Start the Vite dev server

### Step 3: Open the App

Open your browser to: **http://localhost:3000**

---

## Option 2: Full Docker Development

Run everything in Docker (slower hot-reload):

```bash
# From project root
docker-compose up
```

Wait for all services to start, then open: **http://localhost:3000**

---

## Troubleshooting

### Issue: "Backend services are not running"

**Solution:**
```bash
# Check if containers are running
docker ps | grep finwhiz

# If not running, start them:
./start-dev.sh
```

### Issue: "docker-compose up" fails

**Check logs:**
```bash
# View all logs
docker-compose logs

# View specific service
docker logs finwhiz_agent
docker logs finwhiz_llm
docker logs finwhiz_postgres
```

**Common fixes:**
```bash
# Clean up and rebuild
docker-compose down
docker-compose build --no-cache
./start-dev.sh
```

### Issue: Frontend can't connect to backend

**Check proxy configuration:**
1. Open browser DevTools → Console
2. Look for: `BASE_URL: http://localhost:3000`
3. Check Network tab for failed `/api/*` requests

**Verify backend services are healthy:**
```bash
curl http://localhost:8010/health  # Should return {"status":"ok"}
curl http://localhost:8001/health  # Should return {"status":"ok"}
```

### Issue: Document uploads fail

**Check:**
1. File is PDF format
2. GCS credentials are configured in `.env`
3. Agent service logs: `docker logs finwhiz_agent`

### Issue: Chat doesn't work

**Check:**
1. Browser console for errors
2. LLM service is running: `curl http://localhost:8001/health`
3. Chroma database initialized: `docker logs finwhiz_llm | grep Chroma`

---

## Viewing Logs

### All services:
```bash
docker-compose logs -f
```

### Specific service:
```bash
docker-compose logs -f agent
docker-compose logs -f llm
docker-compose logs -f postgres
```

### Frontend (when running locally):
Check the terminal where you ran `./dev-setup.sh`

---

## Stopping Services

### Stop backend Docker services:
```bash
docker-compose down
```

### Stop frontend:
Press `Ctrl+C` in the terminal running the frontend

---

## Testing the Integration

### Test 1: Create a Session
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

### Test 2: Query the LLM
```javascript
// Open browser console (replace SESSION_ID with actual value)
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

1. **Start backend once per session:**
   ```bash
   ./start-dev.sh
   ```
   Leave this running in the background.

2. **Work on frontend:**
   ```bash
   cd src/frontend
   npm run dev
   ```

3. **Make changes** to React components - they'll hot-reload automatically

4. **View logs** when debugging:
   ```bash
   # In another terminal
   docker-compose logs -f agent llm
   ```

5. **Stop everything when done:**
   ```bash
   docker-compose down
   ```

---

## Common Commands

| Task | Command |
|------|---------|
| Start backends | `./start-dev.sh` |
| Start frontend | `cd src/frontend && npm run dev` |
| View logs | `docker-compose logs -f` |
| Stop all | `docker-compose down` |
| Rebuild | `docker-compose build --no-cache` |
| Check health | `curl http://localhost:8010/health` |
| Clean restart | `docker-compose down && ./start-dev.sh` |

---

## Next Steps

- See `src/frontend/DEVELOPMENT.md` for detailed frontend documentation
- See `docker-compose.yml` for service configuration
- See `.env` for environment variables

---

## Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Verify `.env` file is configured
3. Ensure ports 3000, 5432, 8001, 8010 are not in use
4. Try a clean restart: `docker-compose down && ./start-dev.sh`
