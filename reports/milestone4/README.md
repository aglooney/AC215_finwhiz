# Milestone 4: Development & Deployment

## Overview

This milestone integrates fine-tuning evaluation, data versioning, and testing infrastructure to demonstrate a deployment-ready FinWhiz system.

## Documentation

- **[Fine-Tuning & Evaluation](model_finetuning.md)** - Training process, results, and deployment strategy
- **[Data Versioning Strategy](data_versioning.md)** - DVC for ML data and scraped content, with reproducibility instructions

---

## Data Versioning Summary

### DVC-Tracked Datasets

We use DVC (Data Version Control) with GCS remote storage for static datasets:

1. **FIQA (ML Training Data)**
   - **Location**: `src/llm/finetuning/data.dvc`
   - **Size**: 38MB (17K QA pairs)
   - **Pull command**:
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS=secrets/service-account-key.json
     dvc pull src/llm/finetuning/data.dvc
     ```

2. **Webscraped Financial Content**
   - **Location**: `src/webscraping/data.dvc`
   - **Size**: 7.4MB (108 NDJSON files from IRS, FINRA, FRED, consumer finance)
   - **Pull command**:
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS=secrets/service-account-key.json
     dvc pull src/webscraping/data.dvc
     ```
   - **Why DVC?** Cannot re-scrape historical content; RAG responses depend on knowledge base version

### DVC Configuration

```yaml
# .dvc/config
[core]
    remote = finetuning_gcs
['remote "finetuning_gcs"']
    url = gs://finwhiz-storage/finetuning_dvc
```

### Reproducibility Workflow

To reproduce any past experiment:
```bash
# 1. Checkout Git tag
git checkout scraped_2024_nov

# 2. Pull DVC-tracked data
dvc pull

# 3. Rebuild derived data (ChromaDB)
python src/embedder/embedding.py

# 4. Run experiments
docker-compose up llm  # RAG with historical knowledge base
```

See **[data_versioning.md](data_versioning.md)** for complete strategy and command reference.

---

## Fine-Tuning & Evaluation Summary

### Dataset & Versioning
- **Dataset**: FIQA (financial QA) from HuggingFace (`LLukas22/fiqa`). Exported splits and Gemini-formatted JSONL live under `src/llm/finetuning/data/`.
- **Versioning**: DVC-managed (`src/llm/finetuning/data.dvc`, remote `gs://finwhiz-storage/finetuning_dvc`). Pull with:
  ```bash
  GOOGLE_APPLICATION_CREDENTIALS=secrets/service-account-key.json dvc pull src/llm/finetuning/data.dvc
  ```
- **Config**: `src/llm/finetuning/configs/fiqa_gemini.yaml` documents dataset paths, Vertex project/region, adapter size, and evaluation plan.

### Training Pipeline
- Script: `src/llm/finetuning/train_gemini_full.py` (downloads FIQA, formats JSONL, uploads to GCS, launches Vertex tuning job).
- Base model: `gemini-2.5-flash-lite-preview-02`
- Adapter size / epochs: `ADAPTER_SIZE_FOUR`, 3 epochs
- Output artifacts: `data/tuning_job_info.json` captures Vertex tuned endpoint; tuned weights remain in Vertex AI registry.
- Execution command (example):
  ```bash
  python src/llm/finetuning/train_gemini_full.py \
      --config src/llm/finetuning/configs/fiqa_gemini.yaml
  ```

### Evaluation Methodology
- Comparison script: `src/llm/finetuning/evaluate_tuned_model.py`
  - Runs tuned endpoint vs. base Gemini on the DVC-versioned FIQA test set.
  - Outputs raw predictions + metrics to `data/evaluation_compare.json`.
  - Sample command:
    ```bash
    python src/llm/finetuning/evaluate_tuned_model.py \
        --project-id finwhiz-ac215 \
        --tuned-endpoint projects/492818598297/locations/us-central1/endpoints/2818346269641015296 \
        --base-model gemini-2.5-pro \
        --num-samples 50 \
        --sample-seed 42
    ```
- Metrics captured: Rouge-L average, case-insensitive exact match (per-model averages and per-example detail). See `reports/milestone4/model_finetuning.md` for results summary.

### LLM-as-Judge
- Script: `reports/milestone4/llm_judge.py`
  - Consumes `data/evaluation_compare.json`, calls a judge model (default `gemini-2.5-pro`), and records win/tie/loss counts plus rationale.
  - Output stored in `reports/milestone4/llm_judge_results.json`.
  - Command:
    ```bash
    python reports/milestone4/llm_judge.py \
        --input data/evaluation_compare.json \
        --project-id finwhiz-ac215 \
        --judge-model gemini-2.5-pro \
        --limit 50
    ```
- Summary: Base model won 48/50 comparisons despite lower Rouge-L. Judge rationales indicate base model provides more comprehensive, better-structured responses. Full results in `reports/milestone4/model_finetuning.md`.

### Deployment Implications
- Tuned model improves financial QA accuracy and should be used when the Vertex endpoint is available (requires `GCP_PROJECT_ID`, Vertex permissions, and `tuning_job_info.json`).
- Base Gemini remains the fallback when the tuned endpoint is unavailable; keep both endpoints accessible so the frontend/agent can switch at runtime based on health checks or cost considerations.
- All configs/datasets/scripts are committed, so future reruns (e.g., updated FIQA or new proprietary datasets) require only updating the YAML + DVC snapshot.

### Artifacts Index
- `reports/milestone4/model_finetuning.md` – design rationale, dataset notes, command references.
- `src/llm/finetuning/configs/fiqa_gemini.yaml` – reproducible config.
- `src/llm/finetuning/train_gemini_full.py` – Vertex tuning script.
- `src/llm/finetuning/evaluate_tuned_model.py` – dual-model evaluation & metrics.
- `reports/milestone4/llm_judge.py` – LLM judge evaluation.
- `data/evaluation_compare.json` & `reports/milestone4/llm_judge_results.json` – evaluation outputs (add to repo once generated/sanitized).
