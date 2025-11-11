"""
Gemini 2.5 Flash Lite Full Finetuning Script

This script trains Gemini 2.5 Flash Lite on the complete FIQA dataset.

Usage:
    python train_gemini_full.py

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
    split: str = "train",
    output_file: str = "data/gemini_train_full.jsonl",
    num_examples: int = None
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
        split: Which split to use ("train" or "test")
        output_file: Path to save formatted data
        num_examples: Number of examples to include (None = all)

    Returns:
        Path object pointing to the output file
    """
    data_split = dataset[split]
    total_examples = len(data_split)
    num_to_process = num_examples if num_examples else total_examples
    
    logger.info(f"Converting {num_to_process} {split} examples to Gemini GenerateContent format")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    examples_written = 0

    with open(output_path, "w") as f:
        for item in data_split:
            if num_examples and examples_written >= num_examples:
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
    blob_name: str
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
    validation_data_uri: str,
    model_display_name: str = "gemini-flash-lite-fiqa-full",
    epochs: int = 3,
    adapter_size: str = "ADAPTER_SIZE_FOUR"
) -> str:
    """
    Submit a Gemini 2.5 Flash Lite finetuning job to Vertex AI using Python SDK.

    Args:
        project_id: GCP project ID
        location: GCP region (e.g., 'us-central1')
        training_data_uri: GCS URI of training data
        validation_data_uri: GCS URI of validation data
        model_display_name: Display name for the tuned model
        epochs: Number of training epochs (default: 3)
        adapter_size: Adapter size enum - valid values:
                      "ADAPTER_SIZE_ONE", "ADAPTER_SIZE_FOUR", "ADAPTER_SIZE_EIGHT",
                      "ADAPTER_SIZE_SIXTEEN", "ADAPTER_SIZE_THIRTY_TWO"
                      (default: "ADAPTER_SIZE_FOUR")

    Returns:
        Tuning job resource name
    """
    logger.info("Initializing Vertex AI")
    aiplatform.init(project=project_id, location=location)

    logger.info(f"Submitting finetuning job for Gemini 2.5 Flash Lite")
    logger.info(f"Training data: {training_data_uri}")
    logger.info(f"Validation data: {validation_data_uri}")
    logger.info(f"Epochs: {epochs}")
    logger.info(f"Adapter size: {adapter_size}")

    try:
        from google.cloud.aiplatform_v1 import GenAiTuningServiceClient
        from google.cloud.aiplatform_v1.types import (
            TuningJob,
            SupervisedTuningSpec,
        )

        client = GenAiTuningServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )

        parent = f"projects/{project_id}/locations/{location}"

        # Create hyperparameters with correct types
        hyper_params = {
            "epoch_count": epochs,
            "adapter_size": adapter_size,
            "learning_rate_multiplier": 1.0
        }

        # Create supervised tuning spec with validation dataset
        supervised_tuning_spec = SupervisedTuningSpec(
            training_dataset_uri=training_data_uri,
            validation_dataset_uri=validation_data_uri,
            hyper_parameters=hyper_params
        )

        tuning_job = TuningJob(
            base_model="gemini-2.5-flash-lite",
            supervised_tuning_spec=supervised_tuning_spec,
            tuned_model_display_name=model_display_name
        )

        logger.info("Submitting tuning job with hyperparameters:")
        logger.info(f"  - Model: gemini-2.5-flash-lite")
        logger.info(f"  - Epochs: {epochs}")
        logger.info(f"  - Adapter size: {adapter_size}")
        logger.info(f"  - Learning rate multiplier: 1.0")
        
        response = client.create_tuning_job(parent=parent, tuning_job=tuning_job)

        logger.info(f"Tuning job submitted: {response.name}")
        logger.info("Job is running. Monitor progress in the Vertex AI console.")

        # Save the job name for later reference
        job_info_path = Path("data/tuning_job_info.json")
        with open(job_info_path, "w") as f:
            json.dump({
                "job_name": response.name,
                "model_display_name": model_display_name,
                "base_model": "gemini-2.5-flash-lite",
                "training_data_uri": training_data_uri,
                "validation_data_uri": validation_data_uri,
                "epochs": epochs,
                "adapter_size": adapter_size,
                "hyper_parameters": hyper_params,
                "timestamp": str(response.create_time) if hasattr(response, 'create_time') else None
            }, f, indent=2)
        logger.info(f"Job info saved to {job_info_path}")

        return response.name

    except Exception as e:
        logger.error(f"Error submitting tuning job: {e}")
        logger.info("\nTroubleshooting:")
        logger.info("1. Ensure Vertex AI API is enabled")
        logger.info("2. Check service account has 'Vertex AI User' role")
        logger.info("3. Verify the training data format is correct")
        logger.info("4. Valid adapter sizes: ADAPTER_SIZE_ONE, ADAPTER_SIZE_FOUR, ADAPTER_SIZE_EIGHT, ADAPTER_SIZE_SIXTEEN, ADAPTER_SIZE_THIRTY_TWO")
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
    logger.info("")
    logger.info("Expected cost for Gemini 2.5 Flash Lite:")
    logger.info("  - Training: $1.50 per million tokens")
    logger.info("  - For 15K examples (~4.1M tokens) x 3 epochs:")
    logger.info("  - Estimated cost: ~$18.50")
    logger.info("="*70 + "\n")


def main():
    """
    Main execution flow for full training.
    """
    logger.info("Starting Gemini 2.5 Flash Lite FULL training on FIQA dataset")

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

    # Step 2: Prepare ALL training examples in Gemini format
    formatted_file = prepare_gemini_format(
        dataset, 
        split="train",
        output_file="data/gemini_train_full.jsonl",
        num_examples=None
    )

    # Step 3: Prepare validation set
    validation_formatted_file = prepare_gemini_format(
        dataset,
        split="test",
        output_file="data/gemini_validation.jsonl",
        num_examples=None
    )
    logger.info(f"Validation set prepared: {validation_formatted_file}")

    # Step 4: Upload training data to GCS
    train_gcs_uri = upload_to_gcs(
        formatted_file, 
        bucket_name,
        "finetuning/gemini_train_full.jsonl"
    )

    # Step 5: Upload validation data to GCS
    validation_gcs_uri = upload_to_gcs(
        validation_formatted_file,
        bucket_name,
        "finetuning/gemini_validation.jsonl"
    )
    logger.info(f"Validation data uploaded: {validation_gcs_uri}")

    # Step 6: Run full finetuning job with 3 epochs
    job_name = run_gemini_tuning(
        project_id, 
        location, 
        train_gcs_uri,
        validation_gcs_uri,
        model_display_name="gemini-flash-lite-fiqa-full",
        epochs=3,
        adapter_size="ADAPTER_SIZE_FOUR"
    )

    # Step 7: Show billing instructions
    check_billing_cost(project_id)

    logger.info("\n" + "="*70)
    logger.info("FULL TRAINING INITIATED SUCCESSFULLY")
    logger.info("="*70)
    logger.info(f"Job name: {job_name}")
    logger.info(f"Model: Gemini 2.5 Flash Lite")
    logger.info(f"Training examples: {len(dataset['train'])}")
    logger.info(f"Validation examples: {len(dataset['test'])}")
    logger.info(f"Epochs: 3")
    logger.info(f"Adapter size: ADAPTER_SIZE_FOUR")
    logger.info("\nNext steps:")
    logger.info("1. Monitor job at: https://console.cloud.google.com/vertex-ai/generative/language/tuning")
    logger.info(f"   Project: {project_id}")
    logger.info("2. Wait for completion (may take 60-120 minutes for 3 epochs)")
    logger.info("3. Check billing for actual costs")
    logger.info("4. Run evaluate_tuned_model.py to test the model")
    logger.info("="*70 + "\n")


if __name__ == "__main__":
    main()