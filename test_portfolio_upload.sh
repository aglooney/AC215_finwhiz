#!/bin/bash
set -e

# Test script for Fidelity portfolio summary upload and extraction
# This script tests the new /portfolio endpoint

# Configuration
AGENT_URL="http://localhost:8010"
LLM_URL="http://localhost:8001"
PORTFOLIO_FILE="Fidelity_statement.pdf"

echo "==================================="
echo "Portfolio Upload Test Script"
echo "==================================="
echo ""

# Generate user and session
USER_ID=$(uuidgen)
echo "Generated User ID: $USER_ID"

SESSION_ID=$(curl -s -X POST "$AGENT_URL/sessions/" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$USER_ID\"}" | jq -r '.session_id // .id')

echo "Created Session ID: $SESSION_ID"
echo ""

# Upload portfolio
echo "Uploading Fidelity portfolio summary..."
UPLOAD_RESPONSE=$(curl -s -X POST \
    -F "file=@$PORTFOLIO_FILE" \
    "$AGENT_URL/sessions/$SESSION_ID/portfolio")

echo "Upload Response:"
echo "$UPLOAD_RESPONSE" | jq
echo ""

# Check for errors in upload
if echo "$UPLOAD_RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    echo "ERROR: Upload failed!"
    echo "$UPLOAD_RESPONSE" | jq '.detail'
    exit 1
fi

# Retrieve session context to verify extraction
echo "Retrieving session context with portfolio data..."
CONTEXT_RESPONSE=$(curl -s "$AGENT_URL/sessions/$SESSION_ID/context")

echo "Session Context:"
echo "$CONTEXT_RESPONSE" | jq
echo ""

# Check if portfolio_fields exists
if echo "$CONTEXT_RESPONSE" | jq -e '.portfolio_fields' > /dev/null 2>&1; then
    echo "✓ Portfolio fields found in context"
    echo ""
    echo "Extracted Portfolio Fields:"
    echo "$CONTEXT_RESPONSE" | jq '.portfolio_fields'
    echo ""
else
    echo "⚠ Warning: No portfolio_fields found in context"
    echo ""
fi

# Test LLM query with portfolio context
echo "Querying LLM about portfolio..."
QUERY="Can you summarize my portfolio?"
LLM_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$QUERY\", \"session_id\": \"$SESSION_ID\", \"user_id\": \"$USER_ID\"}" \
    "$LLM_URL/query")

echo "LLM Response to '$QUERY':"
echo "$LLM_RESPONSE" | jq
echo ""

# Additional test query
echo "Querying LLM with specific portfolio question..."
QUERY2="What is my total portfolio value?"
LLM_RESPONSE2=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$QUERY2\", \"session_id\": \"$SESSION_ID\", \"user_id\": \"$USER_ID\"}" \
    "$LLM_URL/query")

echo "LLM Response to '$QUERY2':"
echo "$LLM_RESPONSE2" | jq
echo ""

echo "==================================="
echo "Test completed successfully!"
echo "==================================="

