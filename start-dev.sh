#!/bin/bash

# FinWhiz Development Startup Script
# This script starts the backend services and waits for them to be healthy

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/src/frontend"
LOG_DIR="$PROJECT_ROOT/logs"
FRONTEND_LOG="$LOG_DIR/frontend-dev.log"
FRONTEND_PID_FILE="$PROJECT_ROOT/.frontend-dev.pid"

require_command() {
    local cmd=$1
    local help_msg=$2
    if ! command -v "$cmd" > /dev/null 2>&1; then
        echo "❌ Required command '$cmd' not found. $help_msg"
        exit 1
    fi
}

wait_for_cloudsql_proxy() {
    echo -n "Waiting for Cloud SQL proxy (cloudsql-proxy:5432)..."

    local cloudsql_container=""
    for _ in {1..10}; do
        cloudsql_container=$(docker-compose ps -q cloudsql-proxy || true)
        if [ -n "$cloudsql_container" ]; then
            break
        fi
        sleep 1
    done

    if [ -z "$cloudsql_container" ]; then
        echo " ❌"
        echo ""
        echo "⚠️  Could not find the Cloud SQL proxy container. Check docker-compose output."
        exit 1
    fi

    local cloudsql_network
    cloudsql_network=$(docker inspect -f '{{range $name,$conf := .NetworkSettings.Networks}}{{println $name}}{{end}}' "$cloudsql_container" | head -n 1 | tr -d '\r')

    if [ -z "$cloudsql_network" ]; then
        echo " ❌"
        echo ""
        echo "⚠️  Failed to determine the Docker network for cloudsql-proxy."
        exit 1
    fi

    if ! docker image inspect busybox:1.36 > /dev/null 2>&1; then
        echo ""
        echo "   📦 Pulling helper image busybox:1.36 (first run only)..."
        docker pull busybox:1.36 > /dev/null
    fi

    local cloudsql_ready=0
    for _ in {1..60}; do
        if docker run --rm --network "$cloudsql_network" busybox:1.36 sh -c "nc -z -w1 cloudsql-proxy 5432" > /dev/null 2>&1; then
            cloudsql_ready=1
            break
        fi
        echo -n "."
        sleep 2
    done

    if [ $cloudsql_ready -eq 1 ]; then
        echo " ✅"
    else
        echo " ❌"
        echo ""
        echo "⚠️  Cloud SQL proxy failed to become reachable on port 5432."
        echo "   docker-compose logs cloudsql-proxy"
        exit 1
    fi
}

echo "🚀 Starting FinWhiz Backend Services"
echo "===================================="
echo ""

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down
echo ""

# Start the backend services
echo "🔧 Starting backend services (cloudsql-proxy, agent, llm)..."
echo "This will take 1-2 minutes for the LLM service to load models..."
echo ""

docker-compose up -d cloudsql-proxy agent llm

echo ""
echo "⏳ Waiting for services to become healthy..."
echo ""

# Wait for Cloud SQL proxy
wait_for_cloudsql_proxy

# Wait for agent service
echo -n "Waiting for Agent service..."
AGENT_READY=0
for i in {1..60}; do
    if curl -f -s http://localhost:8010/health > /dev/null 2>&1; then
        AGENT_READY=1
        break
    fi
    echo -n "."
    sleep 2
done

if [ $AGENT_READY -eq 1 ]; then
    echo " ✅"
else
    echo " ❌"
    echo ""
    echo "⚠️  Agent service failed to start. Check logs:"
    echo "   docker logs finwhiz_agent"
    exit 1
fi

# Wait for LLM service (this takes longer)
echo -n "Waiting for LLM service (loading models, this may take 1-2 minutes)..."
LLM_READY=0
for i in {1..120}; do
    if curl -f -s http://localhost:8001/health > /dev/null 2>&1; then
        LLM_READY=1
        break
    fi
    echo -n "."
    sleep 2
done

if [ $LLM_READY -eq 1 ]; then
    echo " ✅"
else
    echo " ❌"
    echo ""
    echo "⚠️  LLM service failed to start. Check logs:"
    echo "   docker logs finwhiz_llm"
    exit 1
fi

start_frontend_dev_server() {
    echo ""
    echo "🖥️  Starting frontend development server (Vite)..."
    echo "🧱 Building frontend image..."
    docker-compose build frontend
    echo "🚀 Launching frontend container..."
    docker-compose up -d frontend
    echo "✅ Frontend container running (http://localhost:3000)"
}

start_frontend_dev_server

echo ""
echo "🎉 All services are running!"
echo ""
echo "Service Status:"
echo "  ✅ Cloud SQL Proxy: cloudsql-proxy:5432 (inside Docker network)"
echo "  ✅ Agent API:  http://localhost:8010"
echo "  ✅ LLM API:    http://localhost:8001"
echo "  ✅ Frontend Dev: http://localhost:3000 (Vite)"
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f cloudsql-proxy agent llm"
echo "   tail -f $FRONTEND_LOG"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose down"
echo "   if [ -f .frontend-dev.pid ]; then kill \$(cat .frontend-dev.pid); fi"
echo ""
