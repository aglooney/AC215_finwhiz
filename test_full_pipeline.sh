#!/bin/bash
set -e

# -------------------------------------------------------------------
# Initial configuration
# -------------------------------------------------------------------
AGENT_URL="http://localhost:8010"
LLM_URL="http://localhost:8001/query"
W2_FILE="src/synthetic_data/w2/outputs/w2_000.pdf"
INT1099_FILE="src/synthetic_data/int_1099/outputs/1099int_002_flat.pdf"

# -------------------------------------------------------------------
# Generate user and session IDs
# -------------------------------------------------------------------
USER_ID=$(uuidgen)
echo "Generated User ID: $USER_ID"

SESSION_ID=$(curl -s -X POST "$AGENT_URL/sessions/" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$USER_ID\"}" | jq -r '.session_id // .id')

echo "Created Session ID: $SESSION_ID"
echo -e "\n"

# -------------------------------------------------------------------
# Verify empty session
# -------------------------------------------------------------------
echo "Initial session context:"
curl -s "$AGENT_URL/sessions/$SESSION_ID/context" | jq
echo -e "\n"

# -------------------------------------------------------------------
# Upload example 1099 (corrected endpoint!)
# -------------------------------------------------------------------
echo "Uploading 1099 form..."
curl -s -X POST \
    -F "file=@$INT1099_FILE" \
    "$AGENT_URL/sessions/$SESSION_ID/1099" | jq
echo -e "\n"

# -------------------------------------------------------------------
# Send message to user
# -------------------------------------------------------------------
echo "Logging user message (1099)..."
curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"role\": \"user\", \"content\": \"tell me about my personal 1099\"}" \
    "$AGENT_URL/sessions/$SESSION_ID/messages" | jq
echo -e "\n"

# -------------------------------------------------------------------
# Retrieve session context (with 1099)
# -------------------------------------------------------------------
echo "Current session context (with 1099):"
curl -s "$AGENT_URL/sessions/$SESSION_ID/context" | jq
echo -e "\n"

# -------------------------------------------------------------------
# Query LLM for 1099 summary
# -------------------------------------------------------------------
QUERY="Can you summarize my 1099?"
echo "Querying LLM: $QUERY"
LLM_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$QUERY\", \"session_id\": \"$SESSION_ID\", \"user_id\": \"$USER_ID\"}" \
    "$LLM_URL")

echo "LLM Response:"
echo "$LLM_RESPONSE" | jq
echo -e "\n"

# -------------------------------------------------------------------
# Upload example W-2
# -------------------------------------------------------------------
echo "Uploading W-2 form..."
curl -s -X POST \
    -F "file=@$W2_FILE" \
    "$AGENT_URL/sessions/$SESSION_ID/w2" | jq
echo -e "\n"

# -------------------------------------------------------------------
# Send message to user
# -------------------------------------------------------------------
echo "Logging user message (W-2)..."
curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"role\": \"user\", \"content\": \"tell me about my personal W-2\"}" \
    "$AGENT_URL/sessions/$SESSION_ID/messages" | jq
echo -e "\n"

# -------------------------------------------------------------------
# Retrieve session context (with W-2)
# -------------------------------------------------------------------
echo "Current session context (with W-2):"
curl -s "$AGENT_URL/sessions/$SESSION_ID/context" | jq
echo -e "\n"

# -------------------------------------------------------------------
# Query LLM for W-2 summary
# -------------------------------------------------------------------
QUERY="Can you summarize my W-2?"
echo "Querying LLM: $QUERY"
LLM_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$QUERY\", \"session_id\": \"$SESSION_ID\", \"user_id\": \"$USER_ID\"}" \
    "$LLM_URL")

echo "LLM Response:"
echo "$LLM_RESPONSE" | jq
echo -e "\n"

# -------------------------------------------------------------------
# Wrap up
# -------------------------------------------------------------------
echo "Full pipeline test completed successfully!"
