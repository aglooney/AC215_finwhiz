"""
Compare tuned Gemini model vs. foundation baseline on the FIQA test split.

Usage examples:
    python evaluate_tuned_model.py --tuned-endpoint <endpoint> --base-model gemini-2.5-flash-lite-preview-02
    python evaluate_tuned_model.py --num-samples 100 --sample-seed 42

If --tuned-endpoint is omitted, the script falls back to data/tuning_job_info.json.
"""

import argparse
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_test_data(test_file: str = "data/fiqa_test.jsonl") -> List[Dict]:
    """
    Load test data from JSONL file.

    Args:
        test_file: Path to test data file

    Returns:
        List of test examples
    """
    test_path = Path(test_file)
    if not test_path.exists():
        raise FileNotFoundError(f"Test file not found: {test_file}")

    test_data = []
    with open(test_path, "r") as f:
        for line in f:
            test_data.append(json.loads(line))

    logger.info(f"Loaded {len(test_data)} test examples from {test_file}")
    return test_data


def get_model_endpoint() -> str:
    """
    Get the tuned model endpoint from job info file.

    Returns:
        Model endpoint name
    """
    job_info_path = Path("data/tuning_job_info.json")

    if not job_info_path.exists():
        raise FileNotFoundError(
            "Tuning job info not found. Please provide --model-endpoint argument " "or ensure train_gemini_full.py has completed successfully."
        )

    with open(job_info_path, "r") as f:
        job_info = json.load(f)

    model_name = job_info.get("model_display_name", "gemini-flash-fiqa-full")
    logger.info(f"Using model: {model_name}")

    return model_name


def rouge_l_score(reference: str, candidate: str) -> float:
    """Compute Rouge-L F1 using LCS."""

    def tokenize(text: str) -> List[str]:
        return text.lower().split()

    ref_tokens = tokenize(reference)
    cand_tokens = tokenize(candidate)
    if not ref_tokens or not cand_tokens:
        return 0.0

    m, n = len(ref_tokens), len(cand_tokens)
    lcs = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m - 1, -1, -1):
        for j in range(n - 1, -1, -1):
            if ref_tokens[i] == cand_tokens[j]:
                lcs[i][j] = 1 + lcs[i + 1][j + 1]
            else:
                lcs[i][j] = max(lcs[i + 1][j], lcs[i][j + 1])

    lcs_len = lcs[0][0]
    precision = lcs_len / n
    recall = lcs_len / m
    if precision + recall == 0:
        return 0.0
    return (2 * precision * recall) / (precision + recall)


def exact_match(reference: str, candidate: str) -> float:
    """Simple case-insensitive exact match metric."""

    ref = reference.strip().lower()
    cand = candidate.strip().lower()
    return 1.0 if ref and ref == cand else 0.0


def generate_response(model, question: str, is_langchain: bool = False):
    """Helper to run a prompt through a Vertex model."""
    if is_langchain:
        # Langchain VertexAI uses a simpler interface
        response = model.invoke(question, temperature=0.2, max_tokens=1024, top_p=0.8, top_k=40)
        return response.strip()
    else:
        # Native vertexai GenerativeModel
        from vertexai.generative_models import Content, Part

        user_content = Content(role="user", parts=[Part.from_text(question)])
        response = model.generate_content(
            contents=[user_content],
            generation_config={
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,
            },
        )
        return response.text.strip()


def evaluate_models(
    tuned_endpoint: str,
    base_model_name: Optional[str],
    test_data: List[Dict],
    project_id: str,
    location: str = "us-central1",
    num_samples: int = 50,
    sample_seed: Optional[int] = None,
    output_file: str = "data/evaluation_compare.json",
) -> Dict:
    """Run both tuned and baseline models on the same subset and compute metrics."""
    logger.info(f"Initializing Vertex AI for project {project_id}")

    from google.cloud import aiplatform
    from vertexai.generative_models import GenerativeModel
    from langchain_google_vertexai import VertexAI

    aiplatform.init(project=project_id, location=location)

    tuned_model = GenerativeModel(tuned_endpoint)
    logger.info(f"Loaded tuned model: {tuned_endpoint}")
    base_model = None
    if base_model_name:
        # Use langchain's VertexAI for base model (works with existing permissions)
        base_model = VertexAI(model_name=base_model_name, project=project_id, location=location)
        logger.info(f"Loaded base model via langchain: {base_model_name}")

    if sample_seed is not None:
        random.seed(sample_seed)
        random.shuffle(test_data)

    subset = test_data[: min(num_samples, len(test_data))]
    logger.info(f"Evaluating {len(subset)} examples")

    aggregate = {
        "tuned": {"rouge_l": 0.0, "exact_match": 0.0},
        "base": {"rouge_l": 0.0, "exact_match": 0.0},
        "count": 0,
    }
    comparison_rows: List[Dict] = []

    for idx, example in enumerate(subset, start=1):
        question = example.get("question", "").strip()
        reference = example.get("answer", "").strip()
        if not question or not reference:
            continue

        tuned_prediction = ""
        base_prediction = ""
        try:
            tuned_prediction = generate_response(tuned_model, question, is_langchain=False)
        except Exception as exc:  # pragma: no cover - network call
            logger.warning(f"Tuned model failed on example {idx}: {exc}")

        if base_model is not None:
            try:
                base_prediction = generate_response(base_model, question, is_langchain=True)
            except Exception as exc:  # pragma: no cover - network call
                logger.warning(f"Base model failed on example {idx}: {exc}")

        tuned_metrics = {
            "rouge_l": rouge_l_score(reference, tuned_prediction),
            "exact_match": exact_match(reference, tuned_prediction),
        }
        base_metrics = {
            "rouge_l": rouge_l_score(reference, base_prediction) if base_prediction else 0.0,
            "exact_match": exact_match(reference, base_prediction) if base_prediction else 0.0,
        }

        aggregate["tuned"]["rouge_l"] += tuned_metrics["rouge_l"]
        aggregate["tuned"]["exact_match"] += tuned_metrics["exact_match"]
        aggregate["base"]["rouge_l"] += base_metrics["rouge_l"]
        aggregate["base"]["exact_match"] += base_metrics["exact_match"]
        aggregate["count"] += 1

        comparison_rows.append(
            {
                "question": question,
                "ground_truth": reference,
                "tuned_prediction": tuned_prediction,
                "base_prediction": base_prediction,
                "tuned_metrics": tuned_metrics,
                "base_metrics": base_metrics,
            }
        )

        if idx % 10 == 0:
            logger.info("Processed %s/%s examples", idx, len(subset))
        time.sleep(1)  # basic rate limiting

    total = max(aggregate["count"], 1)
    summary = {
        "samples": aggregate["count"],
        "tuned_avg_rouge_l": aggregate["tuned"]["rouge_l"] / total,
        "tuned_exact_match": aggregate["tuned"]["exact_match"] / total,
        "base_avg_rouge_l": aggregate["base"]["rouge_l"] / total,
        "base_exact_match": aggregate["base"]["exact_match"] / total,
    }

    results = {"summary": summary, "examples": comparison_rows}
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(results, f, indent=2)

    logger.info("Saved comparison results to %s", output_path)
    logger.info("Tuned Rouge-L: %.3f | Base Rouge-L: %.3f", summary["tuned_avg_rouge_l"], summary["base_avg_rouge_l"])
    return results


def main():
    parser = argparse.ArgumentParser(description="Compare tuned Gemini model vs base model")
    parser.add_argument(
        "--tuned-endpoint",
        "--model-endpoint",
        type=str,
        help="Tuned model endpoint name (e.g., 'projects/123/locations/us-central1/endpoints/456')",
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default="gemini-2.5-pro",
        help="Vertex foundation model name to use as baseline (set empty string to skip)",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=50,
        help="Number of test samples to evaluate (default: 50)",
    )
    parser.add_argument(
        "--sample-seed",
        type=int,
        help="Optional random seed for shuffling the holdout set",
    )
    parser.add_argument(
        "--test-file",
        type=str,
        default="data/fiqa_test.jsonl",
        help="Path to holdout JSONL file",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="data/evaluation_compare.json",
        help="Where to store the comparison JSON",
    )
    parser.add_argument("--project-id", type=str, help="GCP project ID (defaults to GCP_PROJECT_ID env var)")

    args = parser.parse_args()

    # Get configuration
    project_id = args.project_id or os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise ValueError("Please provide --project-id or set GCP_PROJECT_ID env var")

    tuned_endpoint = args.tuned_endpoint or get_model_endpoint()
    base_model = args.base_model.strip() if args.base_model else None

    test_data = load_test_data(args.test_file)

    evaluate_models(
        tuned_endpoint=tuned_endpoint,
        base_model_name=base_model,
        test_data=test_data,
        project_id=project_id,
        num_samples=args.num_samples,
        sample_seed=args.sample_seed,
        output_file=args.output_file,
    )


if __name__ == "__main__":
    main()
