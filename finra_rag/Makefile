# Uses variables from .env (if present)
export $(shell sed 's/=.*//' .env 2>/dev/null)

SEEDS=config/crawl_allowlist.yml

.PHONY: venv install crawl transform export all dry-run

venv:
	python3 -m venv rag_venv && . rag_venv/bin/activate && \
	python -m pip install --upgrade pip setuptools wheel && \
	pip install -r requirements.txt

install:
	. rag_venv/bin/activate && pip install -r requirements.txt

crawl:
	. rag_venv/bin/activate && python -m src.crawl.run_crawl --seeds $(SEEDS) --out data/raw_html

transform:
	. rag_venv/bin/activate && python -m src.transform.run_transform --in data/raw_html --out data \
		--selectors config/selectors.yml --routing config/routing.yml

export:
	. rag_venv/bin/activate && python -m src.export.build_jsonl --in data/chunks --out data \
		--schema config/schema.json
	. rag_venv/bin/activate && python -m src.export.to_gcs --local data/exports/jsonl --bucket $$GCS_BUCKET \
		--prefix finra/exports/jsonl

dry-run:
	. rag_venv/bin/activate && python -m scripts.dry_run_sample

all: crawl transform export