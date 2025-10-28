"""
Evaluate Tuned Gemini Model

This script evaluates the tuned Gemini model on the FIQA test set.

Usage:
    python evaluate_tuned_model.py --model-endpoint <endpoint-name>

Or set the model endpoint in data/tuning_job_info.json
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict
import time

import vertexai
from vertexai.generative_models import GenerativeModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
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
            "Tuning job info not found. Please provide --model-endpoint argument "
            "or ensure train_gemini_full.py has completed successfully."
        )

    with open(job_info_path, "r") as f:
        job_info = json.load(f)

    model_name = job_info.get("model_display_name", "gemini-flash-fiqa-full")
    logger.info(f"Using model: {model_name}")
    
    return model_name


def evaluate_model(
    model_endpoint: str,
    test_data: List[Dict],
    project_id: str,
    location: str = "us-central1",
    num_samples: int = 50
) -> Dict:
    """
    Evaluate the tuned model on test data.
    """
    logger.info(f"Initializing Vertex AI for project {project_id}")
    
    from google.cloud import aiplatform
    from vertexai.generative_models import GenerativeModel, Content, Part
    
    aiplatform.init(project=project_id, location=location)

    try:
        # Load the tuned model using the full resource name
        model = GenerativeModel(model_endpoint)
        logger.info(f"Successfully loaded model: {model_endpoint}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    results = {
        "total_tested": 0,
        "successful": 0,
        "failed": 0,
        "examples": []
    }

    num_to_test = min(num_samples, len(test_data))
    logger.info(f"Evaluating on {num_to_test} test examples...")

    for i, example in enumerate(test_data[:num_to_test]):
        question = example.get("question", "").strip()
        ground_truth = example.get("answer", "").strip()

        if not question or not ground_truth:
            continue

        try:
            # Create properly formatted content for tuned model
            # Use the same format as training data
            user_content = Content(
                role="user",
                parts=[Part.from_text(question)]
            )
            
            # Generate prediction using generate_content with proper format
            response = model.generate_content(
                contents=[user_content],
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            
            predicted_answer = response.text.strip()

            results["successful"] += 1
            results["examples"].append({
                "question": question,
                "ground_truth": ground_truth,
                "prediction": predicted_answer
            })

            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{num_to_test} examples")

            # Rate limiting
            time.sleep(1)

        except Exception as e:
            logger.warning(f"Failed to generate for example {i}: {e}")
            results["failed"] += 1

        results["total_tested"] += 1

    # Save results
    results_path = Path("data/evaluation_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"\nEvaluation complete!")
    logger.info(f"Results saved to: {results_path}")
    logger.info(f"Successfully evaluated: {results['successful']}/{results['total_tested']}")
    logger.info(f"Failed: {results['failed']}/{results['total_tested']}")

    # Print sample results
    logger.info("\n" + "="*70)
    logger.info("SAMPLE PREDICTIONS")
    logger.info("="*70)
    for i, ex in enumerate(results["examples"][:3]):
        logger.info(f"\nExample {i+1}:")
        logger.info(f"Q: {ex['question'][:100]}...")
        logger.info(f"Ground Truth: {ex['ground_truth'][:150]}...")
        logger.info(f"Prediction: {ex['prediction'][:150]}...")
        logger.info("-" * 70)

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate tuned Gemini model")
    parser.add_argument(
        "--model-endpoint",
        type=str,
        help="Tuned model endpoint name (e.g., 'projects/123/locations/us-central1/endpoints/456')"
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=50,
        help="Number of test samples to evaluate (default: 50)"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        help="GCP project ID (defaults to GCP_PROJECT_ID env var)"
    )

    args = parser.parse_args()

    # Get configuration
    project_id = args.project_id or os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise ValueError("Please provide --project-id or set GCP_PROJECT_ID env var")

    model_endpoint = args.model_endpoint or get_model_endpoint()

    # Load test data
    test_data = load_test_data()

    # Run evaluation
    results = evaluate_model(
        model_endpoint=model_endpoint,
        test_data=test_data,
        project_id=project_id,
        num_samples=args.num_samples
    )

    logger.info("\nEvaluation completed successfully!")


if __name__ == "__main__":
    import os
    main()