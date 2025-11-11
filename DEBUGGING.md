# FinWhiz Frontend - Debugging Guide

## What I Fixed

### 1. Portfolio Calculation - FIXED ✅
**Problem:** Negative values in portfolio allocation (Bonds showing -48%)

**Root Cause:** The calculation logic didn't account for edge cases where `(100 - stocks)` could result in negative bond values.

**Solution:** Added proper bounds checking with `Math.max` and `Math.min` to ensure:
- All values are between 0-100%
- Total always equals 100%
- No negative values possible

### 2. Added Comprehensive Logging ✅
**Problem:** Chat and document upload failed silently with generic errors

**Solution:** Added detailed console logging to both:
- `ChatInterface.tsx` - Logs every step of message sending and LLM queries
- `DocumentUpload.tsx` - Logs file selection, validation, and upload process

## How to Debug Issues

### Step 1: Refresh the Frontend

The changes have been made to the source files. You need to **refresh your browser** or restart the dev server:

```bash
# If dev server is running, just refresh browser (Ctrl+R or Cmd+R)
# OR restart the dev server:
cd src/frontend
npm run dev
```

### Step 2: Open Browser DevTools

1. Open your app: http://localhost:3000
2. Press **F12** (or right-click → Inspect)
3. Go to the **Console** tab

### Step 3: Test Each Feature

#### Test Portfolio (Should be fixed now)
1. Go through onboarding again
2. Check the portfolio allocation
3. **Expected:** All positive percentages that add up to 100%

#### Test Chat
1. Type a message like "What is a W-2?"
2. Check the Console tab - you should see:
   ```
   Sending message to session: <uuid>
   Message content: What is a W-2?
   Message logged to agent
   Querying LLM with session: <uuid>
   LLM Response: {...}
   Assistant response logged
   ```

**If you see an error:**
- Look for "Error querying LLM:" in console
- Check the Network tab → Filter by "Fetch/XHR"
- Find the failed request to `/api/llm/query`
- Click on it and check:
  - **Headers** tab: Request URL and headers
  - **Payload** tab: What data was sent
  - **Response** tab: Error message from backend

#### Test Document Upload
1. Click "Upload Tax Documents"
2. Select a PDF file
3. Check Console - you should see:
   ```
   File selected: File {...}
   File type: application/pdf
   File size: 12345
   Starting upload for session: <uuid>
   Document type: w2
   Uploading W-2...
   Upload successful: {...}
   ```

**If upload fails:**
- Check console for "Upload error:"
- Check Network tab for the failed POST request to `/api/agent/sessions/<id>/w2`
- Common issues:
  - File not a PDF
  - Backend not accessible
  - GCS credentials missing

### Step 4: Common Error Patterns

#### Error: "Network Error" or "ERR_CONNECTION_REFUSED"
**Meaning:** Frontend can't reach backend services

**Check:**
```bash
# Verify services are running
curl http://localhost:8010/health  # Agent
curl http://localhost:8001/health  # LLM

# If not running:
docker-compose up agent llm postgres
```

#### Error: 404 Not Found
**Meaning:** API endpoint doesn't exist

**Check Console logs for the URL being called:**
- Should be: `/api/agent/...` or `/api/llm/...`
- Vite proxy rewrites these to backend services

#### Error: 422 Unprocessable Entity
**Meaning:** Backend received request but data format is wrong

**Check:**
- Console → Network → Payload tab
- Verify the data structure matches what backend expects

#### Error: 500 Internal Server Error
**Meaning:** Backend crashed while processing request

**Check backend logs:**
```bash
docker logs finwhiz_agent --tail 50
docker logs finwhiz_llm --tail 50
```

## Detailed Logging Output

### Successful Chat Flow
```
Console:
  Sending message to session: 123e4567-e89b-12d3-a456-426614174000
  Message content: What is a W-2?
  BASE_URL: http://localhost:3000
  Sending Request to the Target: POST /api/agent/sessions/123e4567-e89b-12d3-a456-426614174000/messages
  Received Response from the Target: 200 /api/agent/sessions/123e4567-e89b-12d3-a456-426614174000/messages
  Message logged to agent
  Querying LLM with session: 123e4567-e89b-12d3-a456-426614174000
  Sending Request to the Target: POST /api/llm/query
  Received Response from the Target: 200 /api/llm/query
  LLM Response: {answer: "A W-2 form is...", sources: [...], context: "..."}
  Assistant response logged
```

### Successful Upload Flow
```
Console:
  File selected: File {name: "w2_2023.pdf", size: 45678, type: "application/pdf"}
  File type: application/pdf
  File size: 45678
  Starting upload for session: 123e4567-e89b-12d3-a456-426614174000
  Document type: w2
  Uploading W-2...
  Sending Request to the Target: POST /api/agent/sessions/123e4567-e89b-12d3-a456-426614174000/w2
  Received Response from the Target: 200 /api/agent/sessions/123e4567-e89b-12d3-a456-426614174000/w2
  Upload successful: {document_id: "...", document_type: "w2", gcs_uri: "...", created_at: "..."}
```

## Next Steps

1. **Refresh your browser** to load the new code with fixes
2. **Open DevTools Console** (F12)
3. **Test each feature** and observe the console logs
4. **If still having issues**, copy the console error messages and share them

The enhanced logging will tell us exactly where things are failing!
