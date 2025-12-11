FROM python:3.12-slim

# Environment setup
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/src
RUN set -ex && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git build-essential curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && \
    useradd -ms /bin/bash app -d /home/app -u 1000 && \
    mkdir -p /app /home/app/.venv /app/src /app/data && \
    chown -R app:app /app /home/app

USER app
WORKDIR /app/src/llm

# Install dependencies into a venv; use CPU-only PyTorch wheel index
RUN python -m venv /home/app/.venv && \
    source /home/app/.venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu .

COPY --chown=app:app . .

EXPOSE 8001

WORKDIR /app

CMD ["bash", "-c", "source /home/app/.venv/bin/activate && uvicorn src.llm.llm_service:app --host 0.0.0.0 --port 8001 --reload"]
