# Load variables from .env if present
export $(shell sed 's/=.*//' .env 2>/dev/null)

# Variables
SEEDS=config/crawl_allowlist.yml
PYTHON=rag_venv/bin/python
BUCKET?=$(GCS_BUCKET)
PROJECT?=$(PROJECT_ID)
REGION?=$(LOCATION)
CRAWL_MAX?=5   # default: only crawl 5 pages for safety

.PHONY: venv install bucket crawl transform export all dry-run clean

# --------------------------
# Environment / dependencies
# --------------------------

venv:
	python3 -m venv rag_venv
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PYTHON) -m pip install -r requirements.txt

install:
	$(PYTHON) -m pip install -r requirements.txt

# --------------------------
# GCP setup
# --------------------------

bucket:
ifndef BUCKET
	$(error GCS_BUCKET is not set in .env or environment)
endif
ifndef PROJECT
	$(error PROJECT_ID is not set in .env or environment)
endif
ifndef REGION
	$(error LOCATION is not set in .env or environment)
endif
	gcloud storage buckets create $(BUCKET) \
		--project=$(PROJECT) \
		--location=$(REGION) \
		--uniform-bucket-level-access || true
	gcloud storage buckets list --project=$(PROJECT) | grep $(BUCKET)

# --------------------------
# Pipeline steps
# --------------------------

crawl:
	$(PYTHON) -m src.crawl.run_crawl --seeds $(SEEDS) --out data/raw_html --max-pages $(CRAWL_MAX)

transform:
	$(PYTHON) -m src.transform.run_transform --in data/raw_html --out data \
		--selectors config/selectors.yml --routing config/routing.yml

export:
	$(PYTHON) -m src.export.build_jsonl --in data/chunks --out data \
		--schema config/schema.json
	$(PYTHON) -m src.export.to_gcs --local data/exports/jsonl \
		--bucket $(BUCKET) --prefix finra/exports/jsonl

dry-run:
	$(PYTHON) -m scripts.dry_run_sample

all: bucket crawl transform export

clean:
	rm -rf data/raw_html data/parsed_json data/chunks data/exports