#!/bin/bash

# Test authentication and session creation flow
# This script helps debug the authentication and session issues

echo "=== Testing FinWhiz Authentication Flow ==="
echo ""

# Test 1: Health check
echo "1. Testing backend health..."
HEALTH=$(curl -s http://localhost:8010/health)
echo "Response: $HEALTH"
echo ""

# Test 2: Try to create session without auth (should fail)
echo "2. Testing session creation without auth (should fail with 'Not authenticated')..."
SESSION_NO_AUTH=$(curl -s -X POST http://localhost:8010/sessions/ -H "Content-Type: application/json" -d '{}')
echo "Response: $SESSION_NO_AUTH"
echo ""

# Test 3: Sign up a test user
echo "3. Creating a test user..."
TEST_EMAIL="test$(date +%s)@testfinwhiz.com"
echo "Email: $TEST_EMAIL"
SIGNUP_RESPONSE=$(curl -s -X POST http://localhost:8010/auth/signup \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"test123456\"}")
echo "Response: $SIGNUP_RESPONSE"
echo ""

# Extract access token
ACCESS_TOKEN=$(echo $SIGNUP_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to get access token. Check Supabase configuration."
    exit 1
fi

echo "✅ Got access token: ${ACCESS_TOKEN:0:20}..."
echo ""

# Test 4: Create session with auth
echo "4. Testing session creation WITH auth..."
SESSION_WITH_AUTH=$(curl -s -X POST http://localhost:8010/sessions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{}')
echo "Response: $SESSION_WITH_AUTH"
echo ""

# Extract session ID
SESSION_ID=$(echo $SESSION_WITH_AUTH | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SESSION_ID" ]; then
    echo "❌ Failed to create session"
    exit 1
fi

echo "✅ Session created successfully: $SESSION_ID"
echo ""

# Test 5: Get session context
echo "5. Testing get session context..."
CONTEXT=$(curl -s http://localhost:8010/sessions/$SESSION_ID/context \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo "Response: $CONTEXT"
echo ""

echo "=== All tests completed ==="
