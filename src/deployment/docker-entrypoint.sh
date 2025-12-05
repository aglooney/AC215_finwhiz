#!/bin/bash
set -euo pipefail

ENV_FILE="${ENV_FILE:-/app/.env}"

load_env_file() {
    local env_file="$1"
    if [ ! -f "$env_file" ]; then
        return
    fi

    echo "Loading environment variables from ${env_file}"
    while IFS= read -r raw_line || [ -n "$raw_line" ]; do
        local line="${raw_line%$'\r'}"
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

        local key="${line%%=*}"
        local value="${line#*=}"
        key="$(echo "$key" | xargs)"

        if [ -z "$key" ]; then
            continue
        fi

        if [ -z "${!key:-}" ]; then
            export "$key=$value"
        fi
    done < "$env_file"
}

require_env() {
    local var_name="$1"
    if [ -z "${!var_name:-}" ]; then
        echo "Environment variable '$var_name' must be set. Check your .env file or docker-shell configuration." >&2
        exit 1
    fi
}

load_env_file "$ENV_FILE"

require_env "GOOGLE_APPLICATION_CREDENTIALS"
require_env "GCP_PROJECT"
require_env "PULUMI_BUCKET"
PULUMI_BUCKET_LOCATION="${PULUMI_BUCKET_LOCATION:-us-central1}"

echo "Container is running!!!"
echo "Architecture: $(uname -m)"
echo "Environment ready! Virtual environment activated."
echo "Python version: $(python --version)"
echo "UV version: $(uv --version)"

GOOGLE_CRED_PATH="$GOOGLE_APPLICATION_CREDENTIALS"
if [[ "$GOOGLE_CRED_PATH" != /* ]]; then
    GOOGLE_CRED_PATH="/app/$GOOGLE_CRED_PATH"
fi
export GOOGLE_APPLICATION_CREDENTIALS="$GOOGLE_CRED_PATH"
if [ ! -f "$GOOGLE_CRED_PATH" ]; then
    echo "Credentials file '$GOOGLE_CRED_PATH' not found inside the container." >&2
    exit 1
fi

# Authenticate gcloud using service account
gcloud auth activate-service-account --key-file "$GOOGLE_CRED_PATH"
gcloud config set project "$GCP_PROJECT"
# login to artifact-registry
gcloud auth configure-docker us-docker.pkg.dev --quiet
# Check if the bucket exists
if ! gsutil ls -b "$PULUMI_BUCKET" >/dev/null 2>&1; then
    echo "Bucket does not exist. Creating..."
    gsutil mb -p "$GCP_PROJECT" -l "$PULUMI_BUCKET_LOCATION" "$PULUMI_BUCKET"
else
    echo "Bucket already exists. Skipping creation."
fi

echo "Logging into Pulumi using GCS bucket: $PULUMI_BUCKET"
pulumi login "$PULUMI_BUCKET"

# List available stacks
echo "Available Pulumi stacks in GCS:"
gsutil ls "$PULUMI_BUCKET/.pulumi/stacks/"  || echo "No stacks found."

if [ -d /app/src/deployment ]; then
    cd /app/src/deployment
else
    echo "Warning: /app/src/deployment not found. Staying in $(pwd)."
fi

# Run Bash for interactive mode
/bin/bash
