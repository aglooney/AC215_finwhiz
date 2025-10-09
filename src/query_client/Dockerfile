FROM python:3.12-slim

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1

# UV environment variables
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/home/app/.venv

# Install system dependencies
RUN set -ex && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv and create a non-root user
RUN pip install --no-cache-dir --upgrade pip uv && \
    useradd -ms /bin/bash app -d /home/app -u 1000 && \
    mkdir -p /app /home/app/.venv && \
    chown -R app:app /app /home/app/.venv

# Switch to non-root user
USER app
WORKDIR /app

# Copy pyproject.toml and uv.lock first for dependency caching
COPY --chown=app:app pyproject.toml uv.lock ./

# Sync dependencies into uv virtual environment
RUN uv sync

# Copy the interactive script
COPY --chown=app:app interactive_query.py ./

# Expose nothing since this is just interactive
CMD ["bash", "-c", "source /home/app/.venv/bin/activate && python /app/src/query_client/interactive_query.py"]


