FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/home/app/.venv

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

USER app
WORKDIR /app

COPY --chown=app:app pyproject.toml uv.lock ./ 

RUN uv sync

EXPOSE 8001

CMD ["bash", "-c", "source /home/app/.venv/bin/activate && uvicorn src.llm.llm_api:app --host 0.0.0.0 --port 8001"]
