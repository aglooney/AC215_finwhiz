"""
Gemini 1.5 Flash Finetuning Cost Test Script - Pure Python SDK

This script downloads the FIQA dataset from HuggingFace, prepares a small subset
(100 examples) in Gemini's expected format, uploads to GCS, and runs a test
finetuning job to verify actual costs before committing to full training.

Uses pure Python SDK without gcloud CLI dependencies.

Usage:
    python test_gemini_cost_pure_python.py

Environment Variables Required:
    - GCP_PROJECT_ID: Your Google Cloud project ID
    - GCS_BUCKET_NAME: GCS bucket name for storing training data
    - GOOGLE_APPLICATION_CREDENTIALS: Path to service account key JSON
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from datasets import load_dataset
from google.cloud import aiplatform, storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def download_fiqa_dataset(output_dir: str = "data") -> Dict[str, Any]:
    """
    Download FIQA dataset from HuggingFace and save locally.

    Args:
        output_dir: Directory to save the dataset

    Returns:
        Dictionary containing train and test datasets
    """
    logger.info("Downloading FIQA dataset from HuggingFace")

    dataset = load_dataset("LLukas22/fiqa")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    train_path = output_path / "fiqa_train.jsonl"
    test_path = output_path / "fiqa_test.jsonl"

    with open(train_path, "w") as f:
        for item in dataset["train"]:
            f.write(json.dumps(item) + "\n")

    with open(test_path, "w") as f:
        for item in dataset["test"]:
            f.write(json.dumps(item) + "\n")

    logger.info(f"Saved train set to {train_path} ({len(dataset['train'])} examples)")
    logger.info(f"Saved test set to {test_path} ({len(dataset['test'])} examples)")

    return dataset


def prepare_gemini_format(
    dataset: Dict[str, Any],
    output_file: str = "data/gemini_train_100.jsonl",
    num_examples: int = 100
) -> Path:
    """
    Convert FIQA dataset to Gemini finetuning format.

    Gemini expects JSONL with Google's GenerateContent format:
    {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": "question text"}]
            },
            {
                "role": "model",
                "parts": [{"text": "answer text"}]
            }
        ]
    }

    Args:
        dataset: HuggingFace dataset object
        output_file: Path to save formatted data
        num_examples: Number of examples to include

    Returns:
        Path object pointing to the output file
    """
    logger.info(f"Converting {num_examples} examples to Gemini GenerateContent format")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    examples_written = 0

    with open(output_path, "w") as f:
        for item in dataset["train"]:
            if examples_written >= num_examples:
                break

            question = item.get("question", "").strip()
            answer = item.get("answer", "").strip()

            if not question or not answer:
                continue

            # Google's GenerateContent format
            gemini_format = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": question}]
                    },
                    {
                        "role": "model",
                        "parts": [{"text": answer}]
                    }
                ]
            }

            f.write(json.dumps(gemini_format) + "\n")
            examples_written += 1

    logger.info(f"Saved {examples_written} formatted examples to {output_path}")
    return output_path


def upload_to_gcs(
    local_file: Path,
    bucket_name: str,
    blob_name: str = "finetuning/gemini_train_100.jsonl"
) -> str:
    """
    Upload training data to Google Cloud Storage.

    Args:
        local_file: Path to local file
        bucket_name: GCS bucket name
        blob_name: Destination path in bucket

    Returns:
        GCS URI (gs://bucket/path)
    """
    logger.info(f"Uploading {local_file} to gs://{bucket_name}/{blob_name}")

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.upload_from_filename(str(local_file))

    gcs_uri = f"gs://{bucket_name}/{blob_name}"
    logger.info(f"Upload complete: {gcs_uri}")

    return gcs_uri


def run_gemini_tuning(
    project_id: str,
    location: str,
    training_data_uri: str,
    model_display_name: str = "gemini-flash-fiqa-test"
) -> str:
    """
    Submit a Gemini 1.5 Flash finetuning job to Vertex AI using Python SDK.

    Args:
        project_id: GCP project ID
        location: GCP region (e.g., 'us-central1')
        training_data_uri: GCS URI of training data
        model_display_name: Display name for the tuned model

    Returns:
        Tuning job resource name
    """
    logger.info("Initializing Vertex AI")
    aiplatform.init(project=project_id, location=location)

    logger.info(f"Submitting finetuning job for Gemini 1.5 Flash")
    logger.info(f"Training data: {training_data_uri}")

    try:
        # Create a tuning job using the aiplatform library
        from google.cloud.aiplatform_v1 import GenAiTuningServiceClient
        from google.cloud.aiplatform_v1.types import (
            TuningJob,
            SupervisedTuningSpec,
        )

        client = GenAiTuningServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )

        parent = f"projects/{project_id}/locations/{location}"

        # Create supervised tuning spec
        supervised_tuning_spec = SupervisedTuningSpec(
            training_dataset_uri=training_data_uri,
        )

        # Try with gemini-1.5-flash-001 (older stable version)
        tuning_job = TuningJob(
            base_model="gemini-2.5-flash-lite",
            supervised_tuning_spec=supervised_tuning_spec,
            tuned_model_display_name=model_display_name
        )

        logger.info("Submitting tuning job...")
        response = client.create_tuning_job(parent=parent, tuning_job=tuning_job)

        logger.info(f"Tuning job submitted: {response.name}")
        logger.info("Job is running. Monitor progress in the Vertex AI console.")

        return response.name

    except Exception as e:
        logger.error(f"Error submitting tuning job: {e}")
        logger.info("\nTroubleshooting:")
        logger.info("1. Ensure Vertex AI API is enabled")
        logger.info("2. Check service account has 'Vertex AI User' role")
        logger.info("3. Verify the training data format is correct")
        logger.info("4. Try checking supported models in Vertex AI console")
        raise


def check_billing_cost(project_id: str) -> None:
    """
    Print instructions for checking actual billing costs.

    Args:
        project_id: GCP project ID
    """
    logger.info("\n" + "="*70)
    logger.info("COST VERIFICATION INSTRUCTIONS")
    logger.info("="*70)
    logger.info(f"1. Visit: https://console.cloud.google.com/billing")
    logger.info(f"2. Select project: {project_id}")
    logger.info(f"3. Navigate to 'Reports' tab")
    logger.info(f"4. Filter by service: 'Vertex AI'")
    logger.info(f"5. Look for charges related to 'Model Tuning'")
    logger.info("="*70 + "\n")


def main():
    """
    Main execution flow for the cost test.
    """
    logger.info("Starting Gemini 1.5 Flash cost test")

    # Verify environment variables
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    location = os.getenv("GCP_REGION", "us-central1")

    if not project_id or not bucket_name:
        raise ValueError(
            "Missing required environment variables: GCP_PROJECT_ID, GCS_BUCKET_NAME"
        )

    logger.info(f"Project ID: {project_id}")
    logger.info(f"Bucket: {bucket_name}")
    logger.info(f"Region: {location}")

    # Step 1: Download FIQA dataset
    dataset = download_fiqa_dataset()

    # Step 2: Prepare 100 examples in Gemini format
    formatted_file = prepare_gemini_format(dataset, num_examples=100)

    # Step 3: Upload to GCS
    gcs_uri = upload_to_gcs(formatted_file, bucket_name)

    # Step 4: Run test finetuning job
    job_name = run_gemini_tuning(project_id, location, gcs_uri)

    # Step 5: Show billing instructions
    check_billing_cost(project_id)

    logger.info("Cost test initiated successfully")
    logger.info(f"Job name: {job_name}")
    logger.info("Monitor the job and check billing after completion.")


if __name__ == "__main__":
    main()