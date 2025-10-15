#!/bin/bash
set -e

#initial configuration
AGENT_URL="http://localhost:8010"
LLM_URL="http://localhost:8001/query"
W2_FILE="src/synthetic_data/w2/outputs/w2_000.pdf"

#generate session IDs
USER_ID=$(uuidgen)
echo "Generated User ID: $USER_ID"

SESSION_ID=$(curl -s -X POST "$AGENT_URL/sessions/" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$USER_ID\"}" | jq -r '.id')

echo "Created Session ID: $SESSION_ID"

#Verify Empty Session
echo "Initial session context:"
curl -s "$AGENT_URL/sessions/$SESSION_ID/context" | jq
echo -e "\n"

#upload example W-2
echo "Uploading W-2"
curl -s -X POST \
    -F "file=@$W2_FILE" \
    "$AGENT_URL/sessions/$SESSION_ID/w2" | jq
echo -e "\n"

#Send message to user
echo "Logging user message"
curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"role\": \"user\", \"content\": \"tell me about my personal w-2\"}" \
    "$AGENT_URL/sessions/$SESSION_ID/messages" | jq
echo -e "\n"

#agent data retrieval
echo "Current session context (with messages and W-2):"
curl -s "$AGENT_URL/sessions/$SESSION_ID/context" | jq
echo -e "\n"

#query LLM
QUERY="Can you summarize my W-2?"
echo "Querying LLM: $QUERY"
LLM_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$QUERY\", \"session_id\": \"$SESSION_ID\", \"user_id\": \"$USER_ID\"}" \
    "$LLM_URL")

echo "LLM Response:"
echo "$LLM_RESPONSE" | jq
