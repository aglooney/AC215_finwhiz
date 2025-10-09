# Investor.gov RAG Pipeline

Fetch, transform, and export investor.gov educational content (alerts, calculators, info sheets) into a GCS bucket for use in a Retrieval-Augmented Generation setup.

## Setup

1. Create `.env` with your bucket, project, optionally credentials.  
2. Install dependencies:
   ```bash
   make venv
3. Activate environment
    ```bash
    source venv/bin/activate
3. Run the pipeline:
    ```bash
    make investor
4. Verify
    ```bash
    export $(grep -v '^#' .env | xargs)
    echo $GCS_BUCKET
    gcloud storage ls gs://$GCS_BUCKET/investor/exports/jsonl/

5. Scheduling
Use cron or launchd to run make investor periodically (daily, etc.)
Directory Structure
See config/, src/, data/, etc.

---

Once you drop in all of these files, run:

```bash
make venv
make investor
And you should see crawler output, chunk files in data/investor/chunks/, and uploads into your GCS bucket under investor/exports/jsonl/.
Let me know if you run into any errors or want enhancements (PDF parsing, alert updates only, skip duplicates, etc.).