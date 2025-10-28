#!/bin/bash

# Gemini Cost Test Runner
# This script builds and runs the Docker container for testing Gemini finetuning costs

set -e

echo "Building Docker image..."
docker build -t gemini-cost-test .

echo "Running cost test..."
docker run --rm \
  --env-file .env \
  -v $(pwd)/../../secrets:/secrets:ro \
  -v $(pwd)/data:/app/data \
  gemini-cost-test

echo "Cost test complete. Check the output above for results."