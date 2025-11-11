# FinWhiz Frontend - Development Guide

## Overview

The FinWhiz frontend is built with React + TypeScript + Vite and communicates with two backend services:
- **Agent Service** (port 8010): Handles session management, document uploads, and user data
- **LLM Service** (port 8001): Handles RAG queries and LLM responses

## Architecture

The frontend uses Vite's proxy configuration to forward API requests:
- `/api/agent/*` → Agent Service (http://localhost:8010 or http://agent:8010 in Docker)
- `/api/llm/*` → LLM Service (http://localhost:8001 or http://llm:8001 in Docker)

## Development Options

### Option 1: Local Development (Frontend Only)

**Prerequisites:**
- Backend services (agent and llm) must be running
- Node.js 20+ installed

**Steps:**

1. **Start backend services:**
   ```bash
   # From project root
   docker-compose up agent llm postgres
   ```

2. **Install dependencies:**
   ```bash
   cd src/frontend
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Access the app:**
   Open http://localhost:3000

**Benefits:**
- Fast hot-reload
- Direct access to source code
- Easy debugging

### Option 2: Full Docker Development

**Steps:**

1. **Start all services:**
   ```bash
   # From project root
   docker-compose up
   ```

2. **Access the app:**
   Open http://localhost:3000

**Benefits:**
- Production-like environment
- All services configured automatically
- Consistent across team members

### Option 3: Docker with Frontend Hot-Reload

**Steps:**

1. **Start backend services:**
   ```bash
   docker-compose up agent llm postgres
   ```

2. **Start frontend with Docker dev mode:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up frontend
   ```

**Benefits:**
- Hot-reload with Docker
- Consistent networking
- Volume-mounted source code

## Environment Configuration

### Development (.env.development)
```env
VITE_API_BASE_URL=http://localhost:3000
```

### Production (.env.production)
```env
VITE_API_BASE_URL=
```

The production build uses relative paths since the frontend is served from the same origin as the API gateway.

## API Service Structure

The `src/services/api.ts` file provides all API methods:

```typescript
import { api } from './services/api';

// Create a session
const session = await api.createSession(userId);

// Upload documents
const w2Doc = await api.uploadW2(sessionId, file);
const doc1099 = await api.upload1099(sessionId, file);

// Query the LLM
const response = await api.query(query, sessionId);

// Add messages to session
await api.addMessage(sessionId, 'user', content);
```

## Troubleshooting

### Issue: API calls fail with "Network Error"

**Solution 1: Check backend services are running**
```bash
# Check if services are healthy
curl http://localhost:8010/health  # Agent service
curl http://localhost:8001/health  # LLM service
```

**Solution 2: Check Vite proxy configuration**
- Open browser DevTools → Network tab
- Look for failed requests to `/api/*`
- Check Vite terminal for proxy errors

**Solution 3: Verify environment variables**
```bash
# In src/frontend directory
cat .env.development
```

### Issue: Document uploads don't work

**Checklist:**
1. File must be PDF format
2. Agent service must be running and healthy
3. Check browser console for specific error messages
4. Verify GCS credentials are configured in backend

### Issue: Chat messages don't appear

**Checklist:**
1. Session must be created successfully (check localStorage for `finwhiz_session`)
2. LLM service must be running
3. Check browser console for API errors
4. Verify Chroma database is initialized in LLM service

## Testing the API Integration

### Test Session Creation
```javascript
// Open browser console on http://localhost:3000
const userId = crypto.randomUUID();
const response = await fetch('/api/agent/sessions/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: userId })
});
const session = await response.json();
console.log(session);
```

### Test LLM Query
```javascript
// Open browser console (ensure you have a session_id)
const sessionId = 'your-session-id-here';
const response = await fetch('/api/llm/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'What is a W-2 form?',
    session_id: sessionId,
    top_k: 5
  })
});
const result = await response.json();
console.log(result);
```

## Build for Production

```bash
# Build the app
npm run build

# Preview production build locally
npm run preview
```

The production build outputs to `dist/` and is served by nginx in Docker.

## Key Files

- `vite.config.ts` - Vite configuration with proxy setup
- `src/services/api.ts` - API client with all backend methods
- `.env.development` - Development environment variables
- `src/vite-env.d.ts` - TypeScript environment variable types
- `Dockerfile` - Production build (nginx)
- `Dockerfile.dev` - Development build (with hot-reload)

## Additional Notes

### Proxy Configuration Logic

The Vite proxy automatically detects the environment:
- **Local development**: Proxies to `localhost:8010` and `localhost:8001`
- **Docker environment**: Proxies to `agent:8010` and `llm:8001` (container names)

This is controlled by the `DOCKER_ENV` environment variable set in docker-compose.yml.

### CORS

Both backend services have CORS configured to allow requests from any origin during development. In production, this should be restricted to your frontend domain.
