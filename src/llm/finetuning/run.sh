#!/bin/bash

set -e

# Navigate to project root
cd ../../..

if [ "$1" == "train" ]; then
    echo "Building and running training..."
    docker build -t finwhiz_llm -f src/llm/Dockerfile .
    
    docker run --rm \
      --env-file .env \
      -v $(pwd)/secrets:/secrets:ro \
      -v $(pwd)/src/llm/finetuning/data:/app/data \
      finwhiz_llm bash -c "source /home/app/.venv/bin/activate && python src/llm/finetuning/train_gemini_full.py"

elif [ "$1" == "eval" ]; then
    echo "Building and running evaluation..."
    docker build -t finwhiz_llm -f src/llm/Dockerfile .
    
    docker run --rm \
      --env-file .env \
      -v $(pwd)/secrets:/secrets:ro \
      -v $(pwd)/src/llm/finetuning/data:/app/data \
      finwhiz_llm bash -c "source /home/app/.venv/bin/activate && python src/llm/finetuning/evaluate_tuned_model.py --model-endpoint 'projects/492818598297/locations/us-central1/endpoints/2818346269641015296' --num-samples 50"

else
    echo "Usage: ./run.sh [train|eval]"
fi