#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from $ENV_FILE"
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
else
    echo "Warning: $ENV_FILE not found. Continuing without automatically loading env values."
fi

export IMAGE_NAME="${IMAGE_NAME:-cheese-app-deployment}"
export BASE_DIR="$SCRIPT_DIR"
export SECRETS_DIR="${SECRETS_DIR:-$PROJECT_ROOT/secrets}"
export SSH_DIR="${SSH_DIR:-$SECRETS_DIR}"

: "${GCP_PROJECT:=finwhiz-ac215}"
: "${GCP_REGION:=us-central1}"
: "${GCP_ZONE:=us-central1-a}"
: "${GOOGLE_APPLICATION_CREDENTIALS:=/app/secrets/deployment.json}"
: "${PULUMI_BUCKET:=gs://${GCP_PROJECT}-pulumi-state-bucket}"

export GCP_PROJECT GCP_REGION GCP_ZONE GOOGLE_APPLICATION_CREDENTIALS PULUMI_BUCKET

# Create local Pulumi plugins directory if it doesn't exist
mkdir -p "$BASE_DIR/pulumi-plugins"

# Check if container is already running
if docker ps --format "table {{.Names}}" | grep -q "^${IMAGE_NAME}$"; then
    echo "Container '${IMAGE_NAME}' is already running. Shelling into existing container..."
    docker exec -it "$IMAGE_NAME" /bin/bash src/deployment/docker-entrypoint.sh
else
    echo "Container '${IMAGE_NAME}' is not running. Building and starting new container..."

    # Build the image based on the Dockerfile
    #docker build -t $IMAGE_NAME -f Dockerfile .
    docker build -t $IMAGE_NAME --platform=linux/amd64 -f "$BASE_DIR/Dockerfile" "$BASE_DIR"

    # Run the container
    DOCKER_RUN_OPTS=(
        --rm
        --name "$IMAGE_NAME"
        -ti
        -v /var/run/docker.sock:/var/run/docker.sock
        -v "$PROJECT_ROOT":/app
        -v "$SECRETS_DIR":/secrets
        -v "$SSH_DIR/.ssh":/home/app/.ssh:ro
        -v "$BASE_DIR/docker_config.json":/root/.docker/config.json
        -v "$BASE_DIR/pulumi-plugins":/root/.pulumi/plugins
        -v "$BASE_DIR/../api-service":/api-service
        -v "$BASE_DIR/../frontend-react":/frontend-react
        -v "$BASE_DIR/../vector-db":/vector-db
        -e GOOGLE_APPLICATION_CREDENTIALS="$GOOGLE_APPLICATION_CREDENTIALS"
        -e USE_GKE_GCLOUD_AUTH_PLUGIN=True
        -e GCP_PROJECT="$GCP_PROJECT"
        -e GCP_REGION="$GCP_REGION"
        -e GCP_ZONE="$GCP_ZONE"
        -e PULUMI_BUCKET="$PULUMI_BUCKET"
    )

    if [ -f "$ENV_FILE" ]; then
        DOCKER_RUN_OPTS+=(--env-file "$ENV_FILE")
    fi

    docker run "${DOCKER_RUN_OPTS[@]}" "$IMAGE_NAME"
fi
