#!/bin/bash

# FinWhiz Frontend Development Setup Script

set -e

echo "FinWhiz Frontend Development Setup"
echo "======================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js 20+ first."
    exit 1
fi

echo "Node.js version: $(node --version)"
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install npm first."
    exit 1
fi

echo "npm version: $(npm --version)"
echo ""

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo "Dependencies installed"
else
    echo "Dependencies already installed"
fi
echo ""

# Check if backend services are running
echo "Checking backend services..."
echo ""

AGENT_HEALTHY=false
LLM_HEALTHY=false

if curl -f -s http://localhost:8010/health > /dev/null 2>&1; then
    echo "Agent service is running (http://localhost:8010)"
    AGENT_HEALTHY=true
else
    echo "Agent service is NOT running (http://localhost:8010)"
fi

if curl -f -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "LLM service is running (http://localhost:8001)"
    LLM_HEALTHY=true
else
    echo "LLM service is NOT running (http://localhost:8001)"
fi

echo ""

if [ "$AGENT_HEALTHY" = false ] || [ "$LLM_HEALTHY" = false ]; then
    echo "Warning: Backend services are not running!"
    echo ""
    echo "To start backend services, run from project root:"
    echo "  docker-compose up agent llm postgres"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Setup complete! Starting development server..."
echo ""
echo "The app will be available at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev
