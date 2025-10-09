FROM python:3.12-slim

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1

# Tell uv where to put the environment
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/home/app/.venv

# Install system dependencies
RUN set -ex && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv and create user
RUN pip install --no-cache-dir --upgrade pip uv && \
    useradd -ms /bin/bash app -d /home/app -u 1000 && \
    mkdir -p /app /home/app/.venv && \
    chown -R app:app /app /home/app/.venv

# Switch to non-root user
USER app
WORKDIR /app

# Copy pyproject.toml and uv.lock first for caching
COPY --chown=app:app pyproject.toml uv.lock ./

# Sync dependencies into uv virtual environment
RUN uv sync

# Copy all source code
COPY --chown=app:app . .

# Expose API port
EXPOSE 8000

# Activate uv environment and start FastAPI app
CMD ["bash", "-c", "source /home/app/.venv/bin/activate && uvicorn src.retriever.retriever:app --host 0.0.0.0 --port 8000 --reload"]
