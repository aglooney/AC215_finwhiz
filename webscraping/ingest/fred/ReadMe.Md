# 📊 FRED RAG Pipeline

This repository provides a simple **data pipeline** that fetches macroeconomic data from the [FRED API](https://fred.stlouisfed.org/), transforms it into JSONL chunks, and uploads it into a **Google Cloud Storage (GCS) bucket** for use in Retrieval-Augmented Generation (RAG) systems.

---

## 🚀 Features
- Fetches selected FRED series (Treasury yields, CPI, PCE, industrial production, etc.).
- Transforms raw API responses into **JSONL chunks** with human-readable summaries.
- Uploads results to your configured **GCS bucket**.
- Supports both **Conda** and **venv** environments (auto-detected in Makefile).
- Can be scheduled with **cron** or **Cloud Scheduler** for automatic updates.

---

## 📂 Repository Structure
fred_rag/
├── config/
│ └── series.yml # FRED series to fetch
├── data/ # Local staging (raw + chunks)
├── src/
│ └── fred/
│ ├── fetch_data.py
│ └── transform.py
├── .env # API keys + bucket config (ignored in git)
├── .gitignore
├── Makefile
├── requirements.txt
└── README.md

---

## 🔑 Setup

### 1. Get a FRED API Key
1. Register a free account at [FRED](https://fred.stlouisfed.org/).  
2. Request an API key: [API Key page](https://fred.stlouisfed.org/docs/api/api_key.html).  
3. Copy your key.

### 2. Configure Environment
Create a `.env` file in the repo root:

```bash
FRED_API_KEY=your_fred_api_key_here
PROJECT_ID=your_gcp_project
GCS_BUCKET=fw_irs
LOCATION=us-central1
3. Install dependencies
Option A: Conda
conda create -n fred_rag python=3.11 -y
conda activate fred_rag
pip install -r requirements.txt
Option B: venv
make venv
⚙️ Usage
Fetch + Upload Data
make fred
This runs the pipeline:
Fetch raw JSON from FRED into data/fred/raw/.
Transform into JSONL chunks in data/fred/chunks/.
Uploads to gs://fw_irs/fred/exports/jsonl/.
Verify upload
gcloud storage ls gs://fw_irs/fred/exports/jsonl/
⏱️ Scheduling
Cron (local)
Edit crontab:
crontab -e
Add:
0 6 * * * cd /path/to/fred_rag && make fred >> /tmp/fred_rag.log 2>&1
Runs daily at 6 AM.
Cloud Scheduler (GCP)
For production, wrap in Docker + deploy to Cloud Run, then trigger with Cloud Scheduler.
📊 Example Output
Sample JSONL chunk (CPIAUCSL):
{
  "id": "fred-CPIAUCSL-2025-01",
  "source": "https://fred.stlouisfed.org/series/CPIAUCSL",
  "title": "Consumer Price Index for All Urban Consumers",
  "content": "As of Jan 2025, CPI was 307.1 (1982-84=100), up 3.1% YoY and 0.2% MoM."
}
⚠️ Notes
FRED API calls require your API key (.env keeps it out of git).
Costs on GCP are minimal: a few cents/month for storage + requests.
Best practice: keep .env and any credentials in .gitignore.
✅ With this, your RAG system can answer queries like:
“What’s the current shape of the Treasury yield curve?”
“How fast is CPI inflation changing?”
“What sectors are showing growth or contraction?”

---
