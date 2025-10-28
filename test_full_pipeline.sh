#!/bin/bash
set -e

#initial config
AGENT_URL="http://localhost:8010"
LLM_URL="http://localhost:8001"
W2_FILE="src/synthetic_data/w2/outputs/w2_000.pdf"
INT1099_FILE="src/synthetic_data/int_1099/outputs/1099int_002_flat.pdf"

#start session
USER_ID=$(uuidgen)
echo "Generated User ID: $USER_ID"

SESSION_ID=$(curl -s -X POST "$AGENT_URL/sessions/" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$USER_ID\"}" | jq -r '.session_id // .id')

echo "Created Session ID: $SESSION_ID"
echo -e "\n"


#upload 1099 form
echo "Uploading 1099 form"
curl -s -X POST \
    -F "file=@$INT1099_FILE" \
    "$AGENT_URL/sessions/$SESSION_ID/1099" | jq
echo -e "\n"

#retrieve full session context
echo "Current session context (with 1099):"
curl -s "$AGENT_URL/sessions/$SESSION_ID/context" | jq
echo -e "\n"

#query llm with 1099 in session context
QUERY="Can you summarize my 1099?"
echo "Querying LLM: $QUERY"
LLM_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$QUERY\", \"session_id\": \"$SESSION_ID\", \"user_id\": \"$USER_ID\"}" \
    "$LLM_URL/query")

echo "LLM Response:"
echo "$LLM_RESPONSE"
echo -e "\n"

#upload w-2
echo "Uploading W-2 form"
curl -s -X POST \
    -F "file=@$W2_FILE" \
    "$AGENT_URL/sessions/$SESSION_ID/w2" | jq
echo -e "\n"

#retrieve full session context
echo "Current session context (with W-2):"
curl -s "$AGENT_URL/sessions/$SESSION_ID/context" | jq
echo -e "\n"

#query w-2
QUERY="Can you summarize my W-2?"
echo "Querying LLM: $QUERY"
LLM_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$QUERY\", \"session_id\": \"$SESSION_ID\", \"user_id\": \"$USER_ID\"}" \
    "$LLM_URL/query")

echo "LLM Response:"
echo "$LLM_RESPONSE"