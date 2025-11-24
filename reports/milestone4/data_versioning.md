# Data Versioning Strategy

## Overview

FinWhiz uses a hybrid approach to data versioning. We combine DVC for static training datasets with GCS snapshot-based versioning for dynamic application data. This approach accommodates our project's diverse data characteristics: static ML training sets, regularly updated scraped content, and ephemeral user session data.

## Strategy Justification

### Why Hybrid Versioning?

Our project has diverse data characteristics that require different versioning approaches:

| Data Type | Volume | Update Frequency | Versioning Method | Tutorial Alignment |
|-----------|--------|------------------|-------------------|-------------------|
| **ML Training Data** (FIQA) | ~17K QA pairs, 50MB | Static (one-time import) | **DVC** ✅ | Matches tutorial exactly: DVC + GCS remote + Git tags |
| **Scraped Financial Content** | ~2GB chunked NDJSON | Weekly/monthly refreshes | **Manual GCS backup** ⚠️ | NOT tracked by DVC; documented as limitation (too large/dynamic) |
| **ChromaDB Embeddings** | ~500MB vector DB | Updated with scraped content | **GCS manual upload** ⚠️ | Derived data (not source); auto-uploaded by embedder script |
| **User Session Data** | <100MB (local), grows with users | Real-time transactional | **Not versioned (PII)** ✅ | Out of scope: contains PII, ephemeral |
| **Synthetic Test Data** | <10MB PDFs/JSON | Generated on-demand | **Git-tracked** ✅ | Small enough for Git; generation code + outputs committed |
| **Database Schema** | N/A (code) | Changed with code | **Git** ✅ | Schema is code (`models.py`), versioned via Git |

**Tutorial Pattern (Tutorial T7):**
- Static datasets → DVC tracking → GCS remote → Git tags
- Our FIQA dataset follows this exactly (see `src/llm/finetuning/data.dvc`)

**Known Limitations:**
- Scraped content NOT DVC-tracked due to size/update frequency (acknowledged tradeoff)
- ChromaDB is derived data (embeddings of scraped content), not versioned independently

---

## Implementation Details

### 1. DVC for ML Training Data (Follows Tutorial T7)

**What:** FIQA financial QA dataset (train/test splits in Gemini JSONL format)

**Tool:** [DVC](https://dvc.org/) with GCS remote storage - **matches tutorial pattern exactly**

**Configuration:**
```yaml
# .dvc/config (same structure as tutorial)
[core]
    remote = finetuning_gcs
['remote "finetuning_gcs"']
    url = gs://finwhiz-storage/finetuning_dvc
```

**Tracked Files:**
- `src/llm/finetuning/data.dvc` → tracks `fiqa_train.jsonl`, `fiqa_test.jsonl`, `gemini_train_full.jsonl`, `gemini_test_full.jsonl`

**Workflow (mirrors tutorial):**
```bash
# Initial setup (already done)
dvc init
dvc remote add -d finetuning_gcs gs://finwhiz-storage/finetuning_dvc
dvc add src/llm/finetuning/data/
dvc push

# Version in Git (tutorial pattern)
git add src/llm/finetuning/data.dvc
git commit -m 'FIQA dataset v1'
git tag -a 'fiqa_v1' -m 'Initial FIQA import'
git push --atomic origin main fiqa_v1

# Retrieve versioned data (for teammates or CI/CD)
export GOOGLE_APPLICATION_CREDENTIALS=secrets/service-account-key.json
git checkout fiqa_v1            # Get specific version
dvc pull src/llm/finetuning/data.dvc
```

**Version History:**
- Current version: Initial FIQA import (commit `5910ccd`, DVC hash `78f36b1c`)
- Dataset hash in `.dvc` file ensures reproducibility across environments
- Future iterations: `dvc add` → `git commit` → `git tag` (same as tutorial)

**Why DVC for this data?**
- Dataset is **static** (one-time HuggingFace import)
- **Small size** (~50MB) fits DVC's diff-based model well
- **Training reproducibility** is critical; DVC + Git ensures exact dataset reconstruction
- **Follows Tutorial T7 exactly** (cheese_dataset → fiqa_dataset)

---

### 2. GCS Manual Upload for Scraped Content & ChromaDB (Known Limitation)

**What:** Web-scraped financial resources + ChromaDB embeddings

**Tool:** Manual `gsutil` commands or Python upload scripts

**Why NOT DVC?** 
- ⚠️ **Size**: 2GB+ scraped data makes DVC tracking impractical
- ⚠️ **Update frequency**: Weekly refreshes create version churn
- ⚠️ **Derived data**: ChromaDB is computed from scraped data (embeddings), not source material

**Acknowledged Tradeoff:**
This deviates from Tutorial T7 pattern. For full tutorial alignment, scraped data SHOULD be DVC-tracked with Git tags. We accept this limitation for pragmatic reasons (size/frequency), but document it transparently.

**Current Implementation:**
- **Embedder script** (`src/embedder/embedding.py`) has `upload_chroma_to_gcs()` function
- **Manual process**: Run embedder → uploads to `gs://fw_ws/chroma_storage_backup/`
- **Retrieval**: `src/llm/chroma_utils.py` downloads from GCS on container start

**Bucket Structure (Current):**
```
gs://fw_ws/
├── raw_scrapes/               # Manually uploaded via webscraping pipelines
├── chunked_documents/          # Manually uploaded via embedder
└── chroma_storage_backup/     # Uploaded by embedder script
    ├── chroma.sqlite3
    └── 1a90eda1-e932-4e73-89dd-edb1adf9d126/  # Collection directory
```

**Version Strategy (Manual):**
To create "versions", you would manually change the upload prefix:
```python
# Example: Add timestamps to create versions
upload_chroma_to_gcs(local_dir="src/chroma_storage/", 
                     bucket_name="fw_ws", 
                     dest_prefix="chroma_storage_backup_2025-01-10")  # Manual version name
```

**Retrieval:**
```bash
# Download latest snapshot (what the LLM service does on startup)
# Via chroma_utils.py - automatically pulls from GCS
docker-compose up llm  # Auto-downloads if local dir is empty

# Manual download
gsutil -m cp -r gs://fw_ws/chroma_storage_backup/ src/chroma_storage/
```

**Why manual upload (not DVC)?**
- **Large size** (500MB+) - ChromaDB is too big for efficient Git/DVC tracking
- **Generated data** - ChromaDB is derived from scraped content, not source material
- **Infrequent updates** - Only regenerated when scraping runs (weekly/monthly)
- **Simple access pattern** - LLM service just needs "latest" version, not historical comparisons

**Future Enhancement:** Could add timestamped prefixes + GCS lifecycle policies to retain N versions automatically.

---

### 3. Synthetic Test Data (Algorithmic Generation)

**What:** Test documents (W-2s, 1099s, portfolio statements) generated **algorithmically** (via Faker + numpy) for agent workflow testing

**Tool:** Git (committed directly to repo)

**Structure:**
```
src/synthetic_data/
├── w2/
│   ├── synthetic_w2/generator.py           # Algorithmic generation logic (Faker + numpy)
│   ├── outputs/w2_000.pdf                  # Generated PDF
│   ├── outputs/w2_000.json                 # Ground-truth fields (for validation)
│   └── README.md                           # Generation methodology
├── int_1099/...
└── portfolio/...
```

**Generation Method:**
- **No LLM involvement** - Uses deterministic algorithms (Faker library for realistic names/addresses, numpy for financial figures)
- **Seeded randomness** - `--seed 42` ensures reproducible test fixtures across runs
- **Template-based PDF filling** - Uses IRS fillable PDF templates (`assets/irs_w-2_fillable.pdf`)

**Workflow:**
```bash
# Generate synthetic docs (example for W-2)
docker run --rm -v "$(pwd)":/app finwhiz_synthetic \
  python -m synthetic_w2 --count 3 --seed 42 --output-dir outputs/

# Outputs committed to Git (see src/synthetic_data/*/outputs/)
git add src/synthetic_data/w2/outputs/w2_001.*
git commit -m "Add synthetic W-2 test case 001"
```

**Transparency & Reproducibility (MS4):**
- ✅ **Generation code** versioned in `src/synthetic_data/<type>/synthetic_<type>/generator.py` (deterministic logic)
- ✅ **Outputs** committed alongside code (PDF + JSON)
- ✅ **Generation parameters** documented in each subdir's README (seed values, field ranges, template sources)
- ✅ **No LLM prompts required** - generation is purely algorithmic (Faker + numpy), not LLM-based

**Why Git for synthetic data?**
- **Small size** (<10MB total) → no need for DVC
- **High transparency requirement** → keeping generation code + outputs together in version control ensures reproducibility
- **Test stability** → committed outputs ensure integration tests run against known-good fixtures
- **Deterministic generation** → seeded random state makes outputs reproducible from code alone

---

### 4. User Session Data (NOT Versioned - Out of Scope)

**What:** User sessions, chat messages, uploaded documents, extracted financial fields

**Why not versioned:**
- ⚠️ **PII compliance** - Contains SSNs, income, personal info
- ⚠️ **Out of tutorial scope** - Tutorial T7 covers static datasets for ML, not production databases
- ⚠️ **Ephemeral data** - Transactional records, not reproducible research artifacts

**Database Schema IS Versioned:**
- Schema definitions (`models.py`) are tracked in Git ✅
- Schema is code, follows standard Git version control
- Future migrations (via Alembic) would also be Git-tracked

**What:** User sessions, chat messages, uploaded document metadata, extracted W-2/1099/portfolio fields

**Tool:** PostgreSQL (local) / Cloud SQL (production) with SQLAlchemy ORM

**Schema:** See `src/agentic_user_data_processing/models.py` (tables: `users`, `sessions`, `messages`, `documents`, `w2_fields`, `form1099_fields`, `portfolio_fields`)

**Versioning Strategy:**
- ⚠️ **NOT tracked in version control** - Session data contains PII (names, SSNs, income) and is ephemeral/user-specific
- **Schema versioning** - NOT YET IMPLEMENTED (planned via Alembic in MS5); currently schema defined in `models.py` only
- **Backup strategy** (operational, not version control):
  - **Local development:** Docker volume (`postgres_data`) persists across container restarts; dropped between major refactors
  - **Cloud SQL (production):** Automated daily backups (7-day retention) + point-in-time recovery for disaster recovery
  - **No DVC/Git tracking:** User data never leaves the database; only schema migrations are version-controlled

**Reproducibility Note:**
- Database **schema** migrations versioned via **Alembic** (planned for MS5) - tracks schema evolution (e.g., `ALTER TABLE` statements), not individual rows
- Test fixtures use **SQLAlchemy factories** with deterministic seeds (see `tests/integration/conftest.py`) - ephemeral test data only
- CloudSQL compatibility maintained via **standard SQLAlchemy patterns** (no database-specific SQL)

**Why no versioning for user data?**
- **PII compliance** - Names, SSNs, financial details must not be tracked in Git/DVC
- **Transactional data** - User sessions are ephemeral; versioning individual records makes no sense for a live application
- **Separation of concerns** - Version control is for code/config/static datasets, not production user data
- **Schema is versioned** - We track schema structure (via Alembic migrations), not the data itself

---

## Version Control Commands (Quick Reference)

| Data Type | Pull Command | Push Command |
|-----------|--------------|--------------|
| **FIQA (DVC)** | `dvc pull src/llm/finetuning/data.dvc` | `dvc push` |
| **Scraped Content** | `gsutil cp -r gs://fw_ws/chunked_documents_<DATE>/ data/` (manual) | `gsutil cp -r data/ gs://fw_ws/chunked_documents_<DATE>/` (manual) |
| **ChromaDB** | `docker-compose up llm` (auto-downloads on container start) | `python src/embedder/embedding.py` (auto-uploads to `chroma_storage_backup`) |
| **Synthetic Data** | `git pull` | `git add src/synthetic_data/*/outputs/ && git commit` |
| **Session DB** | `pg_dump finwhiz > backup.sql` (local dev only) | Cloud SQL automated backups (production); **never version-controlled due to PII** |

---

## Reproducibility Checklist

For a teammate to reproduce the **entire FinWhiz system from scratch**:

1. ✅ Clone repo + checkout specific commit (e.g., `git checkout f03c941`)
2. ✅ Install DVC + pull training data: `dvc pull src/llm/finetuning/data.dvc`
3. ✅ Set GCS credentials: `export GOOGLE_APPLICATION_CREDENTIALS=secrets/service-account-key.json`
4. ✅ Download latest ChromaDB snapshot: `docker-compose up embedder` (auto-pulls from GCS on start)
5. ✅ Scrape fresh content (optional): `docker run finwhiz_webscrape python -m webscraping.ingest_shared.finra.src.crawl.run_crawl`
6. ✅ Initialize DB schema: `docker-compose up postgres agent` (Alembic auto-migration in MS5)
7. ✅ Use committed synthetic data for tests: files already in `src/synthetic_data/*/outputs/`

**Note:** User session data is NOT versioned (contains PII); only schema migrations will be tracked via Alembic.

**All required config/credentials documented in:** `README.md`, `QUICKSTART.md`, and service-specific READMEs.

---

## Future Enhancements (Post-MS4)

- **Alembic migrations** for DB schema versioning (NOT YET IMPLEMENTED - planned for MS5; currently schema changes require manual table recreation)
- **DVC pipelines** to automate: scrape → embed → upload (replaces manual `gsutil` commands)
- **MLflow integration** for experiment tracking (links model versions to specific data.dvc hashes)
- **Artifact Registry** for Docker images (ensures container versions match data/code versions)

---

## References

- DVC setup: [Tutorial T7](../../local_notes/tutorials/data-versioning/)
- Fine-tuning config: `src/llm/finetuning/configs/fiqa_gemini.yaml`
- Scraping pipelines: `src/webscraping/README.md`
- GCS utilities: `src/gcp_storage/README.md`
- Synthetic data generation: `src/synthetic_data/README.md`
