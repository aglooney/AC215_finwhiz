# Use the official Debian-hosted Python image
FROM python:3.12-slim-bookworm

# Prevent apt from showing prompts
ENV DEBIAN_FRONTEND=noninteractive

# Python wants UTF-8 locale
ENV LANG=C.UTF-8

# Tell Python to disable buffering so we don't lose any logs.
ENV PYTHONUNBUFFERED=1

# Tell uv to copy packages from the wheel into the site-packages
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/home/app/.venv

# FinWhiz GCP Configuration
ENV GCP_PROJECT_ID=finwhiz-ac215
ENV GCS_BUCKET_NAME=finwhiz-storage

# Ensure we have an up to date baseline, install dependencies and
# create a user so we don't run the app as root
RUN set -ex;\
    apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install uv && \
    useradd -ms /bin/bash app -d /home/app -u 1000 && \
    mkdir -p /app && \
    chown app:app /app

# Switch to the new user
USER app
WORKDIR /app

# Copy the source code
COPY --chown=app:app . ./

# Install dependencies using uv
RUN uv sync

# Set working directory to ingest folder where scrapers are
WORKDIR /app/ingest 

# Entry point - start with bash and activate venv
ENTRYPOINT ["/bin/bash"]
CMD ["-c", "source /home/app/.venv/bin/activate && exec bash"]

# ==============================================================================
# How to build and run (FROM PROJECT ROOT - AC215_FINWHIZ):
# ==============================================================================
# 
# 1. Build the image:
#    docker build -f src/webscraping/Dockerfile -t finwhiz-scraper src/webscraping
#
# 2. Run with Service Account Key:
#    docker run -it --rm \
#      -v $(pwd)/secrets/service-account-key.json:/gcp/key.json:ro \
#      -e GOOGLE_APPLICATION_CREDENTIALS=/gcp/key.json \
#      -v $(pwd)/data:/app/data \
#      finwhiz-scraper
#
#    Note: --rm automatically removes the container after exit (keeps image intact)
#
# 3. Inside container, run a scraper (you start in /app/ingest):
#    cd consumer_finance
#    python normalize_cf.py \
#      --config consumer_finance_config.yaml \
#      --bucket finwhiz-storage \
#      --gcs-prefix base-knowledge/scraped-data/consumer-finance \
#      --max-pages 20
#
# 3b. Or run other scrapers:
#    cd investorgov
#    python normalize_investorgov.py ...
#
#    cd irs
#    python normalize_irs.py ...
#
# 4. Verify GCS access (optional):
#    docker run --rm \
#      -v $(pwd)/secrets/service-account-key.json:/gcp/key.json:ro \
#      -e GOOGLE_APPLICATION_CREDENTIALS=/gcp/key.json \
#      finwhiz-scraper \
#      -c "source /home/app/.venv/bin/activate && python -c 'from google.cloud import storage; print(\"✓ GCS Access:\", storage.Client(project=\"finwhiz-ac215\").bucket(\"finwhiz-storage\").exists())'"
#
# 5. To run without auto-activating venv:
#    docker run -it --rm --entrypoint /bin/bash finwhiz-scraper
#
# 6. To deactivate venv inside container:
#    deactivate
#
# ==============================================================================
# ALTERNATIVE: Run from src/webscraping/ folder:
# ==============================================================================
#
# cd src/webscraping
# docker build -t finwhiz-scraper .
# docker run -it --rm \
#   -v ../../secrets/service-account-key.json:/gcp/key.json:ro \
#   -e GOOGLE_APPLICATION_CREDENTIALS=/gcp/key.json \
#   -v $(pwd)/data:/app/data \
#   finwhiz-scraper
#
# ==============================================================================
# Security Notes:
# ==============================================================================
# - Service account key should be in secrets/service-account-key.json
# - Ensure secrets/ is in .gitignore (never commit keys to git!)
# - Service account should have minimal permissions (roles/storage.objectAdmin)
# - Rotate service account keys regularly
# - For production on GCP, consider using Workload Identity instead of key files
#
# Setup .gitignore:
#   echo "secrets/" >> .gitignore
#   echo "secrets/*.json" >> .gitignore
# ==============================================================================