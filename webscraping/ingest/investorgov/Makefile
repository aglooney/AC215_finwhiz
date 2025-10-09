ifneq (,$(wildcard .env))
  include .env
  export
endif

PYTHON := $(shell \
	if [ -n "$$CONDA_DEFAULT_ENV" ]; then \
		echo "python"; \
	elif [ -x "venv/bin/python" ]; then \
		echo "venv/bin/python"; \
	else \
		echo "python3"; \
	fi)

.PHONY: venv install investor all

venv:
	python3 -m venv venv
	venv/bin/pip install --upgrade pip setuptools wheel
	venv/bin/pip install -r requirements.txt

install:
	$(PYTHON) -m pip install -r requirements.txt

investor:
	$(PYTHON) -m src.crawl.run_crawl --seeds config/investor_allowlist.yml --out data/investor/raw_html
	$(PYTHON) -m src.transform.run_transform --in data/investor/raw_html --out data/investor --selectors config/investor_selectors.yml --routing config/investor_routing.yml
	$(PYTHON) -m src.export.build_jsonl --in data/investor --out data/investor --schema config/schema.json
	$(PYTHON) -m src.export.to_gcs --local data/investor/exports/jsonl --bucket $(GCS_BUCKET) --prefix investor/exports/jsonl

all: investor