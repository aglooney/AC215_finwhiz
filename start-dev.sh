#!/bin/bash

# FinWhiz Development Startup Script
# This script starts the backend services and waits for them to be healthy

set -e

echo "🚀 Starting FinWhiz Backend Services"
echo "===================================="
echo ""

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down
echo ""

# Start the backend services
echo "🔧 Starting backend services (postgres, agent, llm)..."
echo "This will take 1-2 minutes for the LLM service to load models..."
echo ""

docker-compose up -d postgres agent llm

echo ""
echo "⏳ Waiting for services to become healthy..."
echo ""

# Wait for postgres
echo -n "Waiting for PostgreSQL..."
until docker exec finwhiz_postgres pg_isready -U finwhiz > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo " ✅"

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

echo ""
echo "🎉 All backend services are running!"
echo ""
echo "Service Status:"
echo "  ✅ PostgreSQL: http://localhost:5432"
echo "  ✅ Agent API:  http://localhost:8010"
echo "  ✅ LLM API:    http://localhost:8001"
echo ""
echo "📝 To start the frontend, run in another terminal:"
echo "   cd src/frontend"
echo "   ./dev-setup.sh"
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f agent llm"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose down"
echo ""
