# Model Fine-Tuning Notes

## Overview
We adapted Google’s Gemini 2.5 Flash Lite (preview) using the FIQA financial QA dataset. The workflow mirrors the class finetuning tutorial: curate/version a question-answer dataset, convert it to Gemini’s `GenerateContent` JSONL schema, upload it to GCS, and launch a Vertex AI tuning job. The scripts live in `src/llm/finetuning/` and are referenced by the config files + DVC metadata described below.

## Dataset & Versioning
- **Source**: `huggingface://LLukas22/fiqa` (train/test splits totaling 17,072 QA pairs).
- **Local path**: `src/llm/finetuning/data/`
- **Versioning tool**: DVC (per Tutorial T7); remote `finetuning_gcs` points to `gs://finwhiz-storage/finetuning_dvc`. The dataset is tracked via `src/llm/finetuning/data.dvc`, so anyone can run `dvc pull` with the shared service-account key to recreate the exact files.
- **Formats**:
  - `fiqa_train.jsonl`, `fiqa_test.jsonl` (raw HuggingFace export).
  - `gemini_train_full.jsonl`, `gemini_test_full.jsonl` (GenerateContent format: alternating user/model messages matching the tutorial schema).
- **Config**: `src/llm/finetuning/configs/fiqa_gemini.yaml` records dataset metadata, remote name, and tuning/eval parameters so runs are reproducible.

## Training Configuration
- **Base model**: `gemini-2.5-flash-lite-preview-02`
- **Adapter size**: `ADAPTER_SIZE_FOUR` (balances token throughput and cost, similar to tutorial defaults).
- **Epochs**: `3`
- **Vertex project / region**: `finwhiz-ac215`, `us-central1`
- **Expected tuned display name**: `gemini-flash-lite-fiqa-v1`
- **Artifacts**: `train_gemini_full.py` handles dataset download, formatting, GCS upload (`gs://finwhiz-storage/finetuning/gemini_fiqa_v1/...`), and submits the tuning job via `GenAiTuningServiceClient`. Successful runs update `src/llm/finetuning/data/tuning_job_info.json` with the Vertex endpoint/model IDs (to be committed/redacted as appropriate).

## Design Rationale
1. **Model choice** – Gemini Flash Lite is optimized for short-form QA responses with low-latency inference, aligning with FinWhiz chat UX. Adapter tuning avoids copying full weights while letting us specialize on finance QA, matching the tutorial guidance of “use Vertex tuning APIs rather than rolling your own trainer.”
2. **Dataset** – FIQA already captures fact-based financial Q&A, so it accelerates experimentation while we continue building our own domain dataset. Using DVC mirrors the class’ cheese dataset registry and gives us reproducible snapshots for this milestone.
3. **Configuration files** – Instead of hardcoding settings, the YAML config lets us capture project IDs, bucket paths, adapter size, evaluation plan, and dataset hashes. This satisfies the milestone requirement to keep datasets/configs versioned and readable by teammates.
4. **Workflow parity with tutorial** – The same sequence exists here: `cli.py --prepare` analogue is the JSONL formatter in `train_gemini_full.py`; GCS upload + Vertex tuning is identical to the tutorial’s `gemini-finetuner` container, except we run it through our repo scripts so CI and documentation stay in one place.

## Evaluation Results

Evaluated tuned endpoint (`projects/492818598297/.../endpoints/2818346269641015296`) vs. baseline `gemini-2.5-pro` on 50 FIQA holdout samples.

### Quantitative Metrics
| Model | Rouge-L | Exact Match |
|-------|---------|-------------|
| **Tuned (Flash Lite)** | 0.111 | 0.0 |
| **Base (Gemini 2.5 Pro)** | 0.070 | 0.0 |

The tuned model shows ~59% higher Rouge-L, indicating better semantic overlap with ground-truth FIQA answers.

### LLM-as-Judge (gemini-2.5-pro)
| Winner | Count |
|--------|-------|
| Base Model | 48 |
| Tuned Model | 1 |
| Tie | 1 |

Despite higher Rouge-L, the judge strongly preferred the base model's responses. Review of rationales shows base model responses are more comprehensive, better structured, and more detailed. The tuned model occasionally produced repetitive or truncated answers, suggesting the fine-tuning optimized for brevity over completeness.

### Deployment Implications
- **Tuned model** delivers faster, more concise responses aligned with FIQA training data. Best suited for quick financial QA lookups where brevity is valued.
- **Base model** provides thorough, well-formatted explanations. Recommended when users need comprehensive guidance (e.g., complex tax scenarios, investment education).
- **Hybrid strategy**: Route simple fact-based queries to the tuned endpoint; escalate complex/open-ended questions to the base model. This balances cost (tuned endpoint is cheaper per token) with quality.
- All evaluation artifacts (`data/evaluation_compare.json`, `reports/milestone4/llm_judge_results.json`) are committed for reproducibility.
