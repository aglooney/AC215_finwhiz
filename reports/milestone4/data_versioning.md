# Data Versioning Strategy

## Overview

FinWhiz uses a hybrid approach to data versioning that aligns with the course's data-versioning tutorial (Tutorial 7). We use **DVC for static datasets** (ML training data and webscraped knowledge base) and **Git for small artifacts** (synthetic test data, code, configs). This strategy ensures reproducibility for ML experiments and RAG system behavior while keeping operational complexity manageable.

## Strategy Justification

### Why Hybrid Versioning?

Our project has diverse data characteristics that require different versioning approaches:

| Data Type | Volume | Update Frequency | Versioning Method | Rationale |
|-----------|--------|------------------|-------------------|-----------|
| **ML Training Data** (FIQA) | ~17K QA pairs, 38MB | Static (one-time import) | **DVC + GCS remote** | Tutorial pattern: static dataset, Git-taggable versions, hash integrity |
| **Scraped Financial Content** | ~7MB chunked NDJSON (108 files) | Weekly/monthly refreshes | **DVC + GCS remote** | Tutorial pattern: static snapshots, reproducible RAG responses, cannot re-scrape historical docs |
| **ChromaDB Embeddings** | ~500MB vector DB | Updated with scraped content | **Derived (not versioned)** | Computed from DVC-tracked scraped data; rebuilding from source provides reproducibility |
| **User Session Data** | Growing with users | Real-time transactional | **Not versioned** | Contains PII (SSNs, income); operational database backups only |
| **Synthetic Test Data** | <2MB PDFs/JSON | Generated on-demand | **Git-committed** | Small enough for Git; generation code versioned alongside outputs |
| **Database Schema** | N/A (code) | Changed with code | **Git** | Schema defined in `models.py`; versioned as code |

---

## Implementation Details

### 1. DVC for ML Training Data (FIQA)

**What:** FIQA financial QA dataset (train/test splits in Gemini JSONL format)

**Tool:** [DVC](https://dvc.org/) with GCS remote storage

**Configuration:**
```yaml
# .dvc/config
[core]
    remote = finetuning_gcs
['remote "finetuning_gcs"']
    url = gs://finwhiz-storage/finetuning_dvc
```

**Tracked Files:**
- `src/llm/finetuning/data.dvc` → tracks 4 JSONL files totaling 38MB (17K QA pairs)

**Workflow:**
```bash
# Pull versioned data (for teammates or CI/CD)
export GOOGLE_APPLICATION_CREDENTIALS=secrets/service-account-key.json
dvc pull src/llm/finetuning/data.dvc

# Update dataset (when making changes)
dvc add src/llm/finetuning/data/
dvc push
git add src/llm/finetuning/data.dvc
git commit -m 'Update FIQA dataset'
git tag -a "fiqa_v2" -m "Updated FIQA with new splits"
git push --atomic origin main fiqa_v2
```

**Why DVC for this data?**
- **Reproducibility**: Hash-based tracking ensures exact dataset reconstruction
- **Size-appropriate**: 38MB fits DVC's model well
- **Static nature**: One-time import, infrequent updates
- **Git integration**: DVC metadata files tracked in Git alongside code

**Reproducibility:** Any teammate or CI/CD pipeline can:
1. Checkout the tagged commit: `git checkout fiqa_v2`
2. Run `dvc pull` to restore exact dataset used for that training run

---

### 2. DVC for Webscraped Financial Content

**What:** Chunked NDJSON files from IRS, FINRA, FRED, and consumer finance websites

**Tool:** [DVC](https://dvc.org/) with same GCS remote as FIQA

**Tracked Files:**
- `src/webscraping/data.dvc` → tracks 108 NDJSON files totaling 7.4MB across subdirectories:
  - `consumer-finance/` - 82 files
  - `finra/` - 1 file
  - `fred/` - 12 files
  - `irs/` - 9 files
  - `local-pdfs/` - 4 files

**Why DVC, not manual GCS?**
- **Cannot re-scrape historical content** (websites change/remove pages)
- **RAG responses depend on knowledge base version** (reproducibility matters)
- **Size is manageable** (~7MB now, max ~50MB expected)
- **Tutorial pattern match** (static snapshots, infrequent updates)

**Workflow:**
```bash
# After each scraping run:
# 1. Run scraping (Docker container or local script)
docker-compose run webscrape python -m webscraping.ingest_shared.finra.src.crawl.run_crawl

# 2. Track with DVC
dvc add src/webscraping/data
dvc push

# 3. Version in Git
git add src/webscraping/data.dvc .gitignore
git commit -m "Scraped data update: 2024 Q4"
git tag -a "scraped_2024_q4" -m "Q4 2024 scraping run"
git push --atomic origin main scraped_2024_q4
```

**Reproducibility:** To test RAG behavior with past data:
```bash
git checkout scraped_2024_q3        # Travel to past snapshot
dvc pull src/webscraping/data.dvc  # Restore scraped content
python src/embedder/embedding.py    # Rebuild ChromaDB from that version
docker-compose up llm               # Test RAG with old knowledge base
```

**Why this matters:**
- Financial regulations change over time (e.g., IRS tax brackets)
- To validate RAG answers from 6 months ago, need that exact knowledge base
- Websites remove/update content (FINRA rule changes, FRED data revisions)

---

### 3. ChromaDB Embeddings (Derived Data)

**What:** Vector embeddings of scraped content stored in ChromaDB

**Storage:** `gs://fw_ws/chroma_storage_backup/` (GCS bucket)

**Versioning Strategy:** **Not independently versioned** (derived from DVC-tracked sources)

**Rationale:**
- Embeddings are **deterministically computed** from `src/webscraping/data/`
- To reproduce: checkout Git tag → `dvc pull` → run `src/embedder/embedding.py`
- Storing embeddings in GCS = **caching**, not versioning
- True reproducibility comes from versioning the source data (DVC)

**Upload/Download:**
```bash
# Upload (after embedding scraped data)
python src/embedder/embedding.py
# → Automatically uploads to gs://fw_ws/chroma_storage_backup/

# Download (on app startup)
docker-compose up llm  # Auto-downloads via chroma_utils.py if local dir empty
```

**Bucket Structure:**
```
gs://fw_ws/chroma_storage_backup/
├── chroma.sqlite3
└── 1a90eda1-e932-4e73-89dd-edb1adf9d126/  # Collection directory
```

**Why not DVC for ChromaDB?**
- **Derived data** - Can always rebuild from `src/webscraping/data.dvc`
- **Large size** - 500MB embeddings would slow DVC operations
- **Redundant** - Versioning both source and derived data doubles storage costs

---

### 4. Synthetic Test Data (Git-Committed)

**What:** Test documents (W-2s, 1099s, portfolio statements) generated **algorithmically** for agent workflow testing

**Tool:** Git (committed directly to repo)

**Structure:**
```
src/synthetic_data/
├── w2/
│   ├── synthetic_w2/generator.py           # Algorithmic generation logic (Faker + numpy)
│   ├── outputs/w2_000.pdf                  # Generated PDF (1.5MB total)
│   ├── outputs/w2_000.json                 # Ground-truth fields
│   └── README.md                           # Generation methodology
├── int_1099/outputs/                       # 56KB
└── portfolio/outputs/                      # 16KB
```

**Generation Method:**
- **No LLM involvement** - Uses deterministic algorithms (Faker library for realistic names/addresses, numpy for financial figures)
- **Seeded randomness** - `--seed 42` ensures reproducible test fixtures
- **Template-based PDF filling** - Uses IRS fillable PDF templates

**Workflow:**
```bash
# Generate synthetic docs (example for W-2)
docker run --rm -v "$(pwd)":/app finwhiz_synthetic \
  python -m synthetic_w2 --count 3 --seed 42 --output-dir outputs/

# Outputs committed to Git
git add src/synthetic_data/w2/outputs/w2_001.*
git commit -m "Add synthetic W-2 test case 001"
```

**Why Git for synthetic data?**
- **Small size** (<2MB total) → no need for DVC
- **High transparency requirement** → keeping generation code + outputs together ensures reproducibility
- **Test stability** → committed outputs ensure integration tests run against known-good fixtures
- **Deterministic generation** → seeded random state makes outputs reproducible from code alone

---

### 5. User Session Data (NOT Versioned)

**What:** User sessions, chat messages, uploaded document metadata, extracted W-2/1099/portfolio fields

**Tool:** PostgreSQL (local) / Cloud SQL (production) with SQLAlchemy ORM

**Schema:** See `src/agentic_user_data_processing/models.py`  
(tables: `users`, `sessions`, `messages`, `documents`, `w2_fields`, `form1099_fields`, `portfolio_fields`)

**Versioning Strategy:**
- ⚠️ **NOT tracked in version control** - Session data contains PII (names, SSNs, income)
- **Schema versioning** - Schema defined in `models.py` and tracked in Git as code

**Why not versioned:**
- **PII compliance** - Contains sensitive personal information
- **Transactional data** - Not reproducible research artifacts
- **Out of tutorial scope** - Tutorial T7 covers static datasets, not production databases

**What IS versioned:**
- ✅ Database schema code (`models.py`) in Git
- ✅ API code that writes/reads from database in Git

---

## Version History & Reproducibility

### DVC-Tracked Data Versions

| Dataset | Version Tag | Date | Size | Description |
|---------|-------------|------|------|-------------|
| FIQA | `fiqa_initial` | Nov 2024 | 38MB | Initial FIQA import (17K QA pairs) |
| Scraped Data | `scraped_2024_nov` | Nov 23, 2024 | 7.4MB | Initial scraping run (IRS, FINRA, FRED, consumer finance) |

### How to Retrieve Specific Versions

```bash
# 1. Checkout the Git tag
git checkout scraped_2024_nov

# 2. Pull the data from DVC
export GOOGLE_APPLICATION_CREDENTIALS=secrets/service-account-key.json
dvc pull  # Pulls all .dvc files in current commit

# 3. Verify data integrity
dvc status  # Should show "Data and pipelines are up to date"

# 4. Use the versioned data
python src/embedder/embedding.py        # Build ChromaDB from this version
docker-compose up llm                   # Run RAG with this knowledge base
```

---

## Command Reference

### Pull Data (Teammates/CI)

| Data Type | Pull Command |
|-----------|--------------|
| **FIQA (DVC)** | `dvc pull src/llm/finetuning/data.dvc` |
| **Scraped Content (DVC)** | `dvc pull src/webscraping/data.dvc` |
| **ChromaDB (GCS)** | `docker-compose up llm` (auto-downloads on start) |
| **Synthetic Data (Git)** | `git pull` |

### Push Data (After Updates)

| Data Type | Push Command |
|-----------|--------------|
| **FIQA (DVC)** | `dvc add src/llm/finetuning/data && dvc push` |
| **Scraped Content (DVC)** | `dvc add src/webscraping/data && dvc push` |
| **ChromaDB (GCS)** | `python src/embedder/embedding.py` (auto-uploads) |
| **Synthetic Data (Git)** | `git add src/synthetic_data/*/outputs/ && git commit` |

---

## Reproducibility Checklist

To reproduce any past experiment or RAG behavior:

- [ ] **Environment**: Checkout Git commit/tag (`git checkout <tag>`)
- [ ] **ML Training Data**: `dvc pull src/llm/finetuning/data.dvc`
- [ ] **Scraped Content**: `dvc pull src/webscraping/data.dvc`
- [ ] **Embeddings**: Rebuild via `python src/embedder/embedding.py` (or pull GCS cache)
- [ ] **Synthetic Test Data**: Automatically available (Git-tracked)
- [ ] **Code & Configs**: Automatically available (Git-tracked)
- [ ] **Credentials**: Set `GOOGLE_APPLICATION_CREDENTIALS` env var

**Example: Reproduce fine-tuning run from Nov 23, 2024**
```bash
git checkout fiqa_initial
dvc pull src/llm/finetuning/data.dvc
python src/llm/finetuning/train_gemini_full.py  # Uses exact dataset from that date
```

**Example: Reproduce RAG answers from Nov 23, 2024**
```bash
git checkout scraped_2024_nov
dvc pull src/webscraping/data.dvc
python src/embedder/embedding.py  # Rebuild ChromaDB from Nov 23 scraped data
docker-compose up llm              # RAG will use Nov 23 knowledge base
```

---

## Alignment with Tutorial 7 (Data Versioning)

Our implementation follows the tutorial's core patterns:

| Tutorial Pattern | Our Implementation |
|------------------|---------------------|
| **DVC + Git for static datasets** | ✅ FIQA (38MB) + Scraped data (7.4MB) |
| **GCS as DVC remote** | ✅ `gs://finwhiz-storage/finetuning_dvc` |
| **Git tags for dataset versions** | ✅ `fiqa_initial`, `scraped_2024_nov` |
| **`.dvc` files in Git** | ✅ `src/llm/finetuning/data.dvc`, `src/webscraping/data.dvc` |
| **Reproducible pull workflow** | ✅ `git checkout <tag> && dvc pull` |
| **Small artifacts in Git** | ✅ Synthetic data (<2MB) committed directly |
