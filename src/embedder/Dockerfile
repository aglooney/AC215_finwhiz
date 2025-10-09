# Use official slim Python image
FROM python:3.12-slim-bookworm

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1

# Optional: uv environment settings
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/home/app/.venv

# Create a non-root user and working directories
RUN set -ex && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install uv && \
    useradd -ms /bin/bash app -d /home/app -u 1000 && \
    mkdir -p /app /home/app/.venv && \
    chown -R app:app /app /home/app/.venv

# Switch to non-root user
USER app
WORKDIR /app

# Copy source code
COPY --chown=app:app . ./

# Install Python dependencies via uv (or requirements.txt)
RUN uv sync 

# Default command: interactive bash
CMD ["bash", "-c", "source /home/app/.venv/bin/activate && exec bash"]

