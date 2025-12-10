#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

STACK_NAME="${PULUMI_STACK:-dev}"

echo "=== Building and pushing images ==="
cd deploy_images
pulumi up --stack "$STACK_NAME" --refresh -y

echo "=== Deploying to K8s ==="
cd ../deploy_k8s

# Delete LLM first to avoid any conflicts; ignore failures if kubectl is unset
if command -v kubectl >/dev/null 2>&1; then
  kubectl delete deployment llm -n finwhiz-namespace --ignore-not-found || true
else
  echo "kubectl not found; skipping llm delete pre-step"
fi

pulumi up --stack "$STACK_NAME" --refresh -y
