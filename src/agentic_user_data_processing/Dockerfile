FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1

ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/home/app/.venv

RUN set -ex && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        curl \
        pdftk-java \
        ghostscript && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip uv && \
    useradd -ms /bin/bash app -d /home/app -u 1000 && \
    mkdir -p /app /home/app/.venv && \
    chown -R app:app /app /home/app/.venv

USER app
WORKDIR /app

COPY --chown=app:app pyproject.toml uv.lock ./
RUN uv sync

COPY --chown=app:app . .

EXPOSE 8010

CMD ["bash", "-c", "source /home/app/.venv/bin/activate && uvicorn agentic_user_data_processing.app:app --host 0.0.0.0 --port 8010"]
