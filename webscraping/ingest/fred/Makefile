# Load environment variables from .env if present
ifneq (,$(wildcard .env))
  include .env
  export
endif

# Detect Python executable depending on environment
# 1. If running inside Conda, use "python"
# 2. If rag_venv exists and we are not in Conda, use that
# 3. Otherwise fall back to system python
PYTHON := $(shell \
	if [ -n "$$CONDA_DEFAULT_ENV" ]; then \
		echo "python"; \
	elif [ -x "rag_venv/bin/python" ]; then \
		echo "rag_venv/bin/python"; \
	else \
		echo "python3"; \
	fi)

.PHONY: venv install fred all

venv:
	python3 -m venv rag_venv && . rag_venv/bin/activate && \
	python -m pip install --upgrade pip setuptools wheel && \
	pip install -r requirements.txt

install:
	$(PYTHON) -m pip install -r requirements.txt

fred:
	$(PYTHON) -m src.fred.fetch_data --out data/fred/raw
	$(PYTHON) -m src.fred.transform --in data/fred/raw --out data/fred/chunks
	$(PYTHON) -m src.export.to_gcs --local data/fred/chunks --bucket $(GCS_BUCKET) --prefix fred/exports/jsonl

all: fred
