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

# This is done for the tutorial only
ENV GOOGLE_APPLICATION_CREDENTIALS=secrets/reliable-sight-471200-v5-96e7a2bfec46.json
ENV GCS_BUCKET=fw_ws

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
    mkdir -p /app /app/data && \
    chown -R app:app /app

# Switch to the new user
USER app
WORKDIR /app

# Copy the source code
COPY --chown=app:app . ./

# Install dependencies
RUN uv sync 

# Set PYTHONPATH so imports work correctly
ENV PYTHONPATH=/app

# Entry point - activate venv and run bash
ENTRYPOINT ["/bin/bash"]
CMD ["-c", "source /home/app/.venv/bin/activate && exec bash"]

#How to run the file:
# python -m src.webscraping.ingest.irs.normalize.py
