# Data Versioning Strategy

## Overview

FinWhiz uses a hybrid approach to data versioning. We combine DVC for static training datasets with GCS snapshot-based versioning for dynamic application data. This approach accommodates our project's diverse data characteristics: static ML training sets, regularly updated scraped content, and ephemeral user session data.

## Strategy Justification

### Why Hybrid Versioning?

Our project has diverse data characteristics that require different versioning approaches:

| Data Type | Volume | Update Frequency | Versioning Method | Rationale |
|-----------|--------|------------------|-------------------|-----------|
| **ML Training Data** (FIQA) | ~17K QA pairs, 50MB | Static (one-time import) | **DVC + GCS remote** | Git-like workflow for dataset iterations; hash-based integrity; reproducible across environments |
| **Scraped Financial Content** | ~2GB chunked NDJSON | Weekly/monthly refreshes | **GCS manual upload** | Too large for DVC tracking; infrequent updates make manual snapshots practical; GCS bucket organization via prefixes |
| **ChromaDB Embeddings** | ~500MB vector DB | Updated with scraped content | **GCS auto-upload** | Derived data (computed from scraped content); embedder script automatically uploads after each build |
| **User Session Data** | Growing with users | Real-time transactional | **Not versioned** | Contains PII (SSNs, income); operational backups only, never tracked in version control |
| **Synthetic Test Data** | <10MB PDFs/JSON | Generated on-demand | **Git-committed** | Small enough for direct Git tracking; generation code versioned alongside outputs |
| **Database Schema** | N/A (code) | Changed with code | **Git** | Schema defined in `models.py`, versioned as code |

---

## Implementation Details

### 1. DVC for ML Training Data

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
- `src/llm/finetuning/data.dvc` → tracks 4 JSONL files totaling 38MB

**Workflow:**
```bash
# Pull versioned data (for teammates or CI/CD)
export GOOGLE_APPLICATION_CREDENTIALS=secrets/service-account-key.json
dvc pull src/llm/finetuning/data.dvc

# After dataset changes (future updates)
dvc add src/llm/finetuning/data/
dvc push
git add src/llm/finetuning/data.dvc
git commit -m 'Update FIQA dataset'
```

**Why DVC for this data?**
- **Reproducibility**: Hash-based tracking ensures exact dataset reconstruction
- **Size-appropriate**: 50MB fits DVC's model well
- **Static nature**: One-time import, infrequent updates
- **Git integration**: DVC metadata files tracked in Git alongside code

---

### 2. GCS Manual Upload for Scraped Content & ChromaDB

**What:** Web-scraped financial resources + ChromaDB embeddings

**Why NOT DVC?**
- **Size**: 2GB+ scraped data makes DVC tracking impractical (slow pulls, large Git metadata)
- **Update frequency**: Weekly/monthly refreshes would create excessive DVC churn
- **Derived data**: ChromaDB is computed from scraped content (embeddings), not original source material
- **Access pattern**: Application only needs "latest" version, not historical comparisons

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
- **Backup Strategy (Operational, Not Version Control):**
- **Local development:** Docker volume (`postgres_data`) persists across container restarts
- **Production:** Cloud SQL automated backups (7-day retention, disaster recovery only)
- **Never tracked in Git/DVC:** User data remains in database only

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
| **Scraped Content** | `gsutil cp -r gs://finwhiz-storage/base-knowledge/scraped-data/ data/` | `python src/gcp_storage/upload_all_scraped_data.py` (overwrites existing) |
| **ChromaDB** | `docker-compose up llm` (auto-downloads on container start) | `python src/embedder/embedding.py` (auto-uploads, overwrites existing) |
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
6. ✅ Initialize DB schema: `docker-compose up postgres agent`
7. ✅ Use committed synthetic data for tests: files in `src/synthetic_data/*/outputs/`

**Note:** User session data is NOT versioned (contains PII).

**All required config/credentials documented in:** `README.md`, `QUICKSTART.md`, and service-specific READMEs.

---

## References

- DVC configuration: `.dvc/config`
- Fine-tuning config: `src/llm/finetuning/configs/fiqa_gemini.yaml`
- Scraping pipelines: `src/webscraping/README.md`
- GCS utilities: `src/gcp_storage/README.md`
- Synthetic data generation: `src/synthetic_data/README.md`
- Database models: `src/agentic_user_data_processing/models.py`
