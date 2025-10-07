# Use the same base image pattern as other FinWhiz services
FROM python:3.12-slim-bookworm

# Keep apt quiet and Python logs flushed
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/home/app/.venv \
    PYTHONPATH=/app/synthetic_data/w2/src

# Install system deps, uv, and create runtime user
RUN set -ex; \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends pdftk-java && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install uv && \
    useradd -ms /bin/bash app -d /home/app -u 1000 && \
    mkdir -p /app && \
    chown app:app /app

USER app

# Copy repo contents (uv will scope to project path)
COPY src/synthetic_data /app

#Install Python dependencies for synthetic data generation
WORKDIR /app/src/synthetic_data
RUN uv sync



# Default entry: expose Typer CLI; command can be overridden at runtime
#ENTRYPOINT ["python", "-m", "w2.synthetic_w2.cli"]
#CMD ["generate", "--output-dir", "app/outputs", "--count", "1"]
ENTRYPOINT ["/bin/bash"]
CMD ["-c", "source /home/app/.venv/bin/activate && exec python -m w2.synthetic_w2.cli"]
