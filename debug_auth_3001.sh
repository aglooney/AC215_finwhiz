#!/bin/bash

# Debug authentication flow for port 3001
# This tests the full flow from signup to session creation

echo "=== Debugging Port 3001 Authentication Flow ==="
echo ""

# Test 1: Check if dev server is accessible
echo "1. Testing if Vite dev server proxy is working..."
PROXY_TEST=$(curl -s http://localhost:3001/api/agent/health)
echo "Response: $PROXY_TEST"
echo ""

if [ "$PROXY_TEST" != '{"status":"ok"}' ]; then
    echo "❌ Dev server proxy not working! Make sure 'npm run dev' is running."
    exit 1
fi

echo "✅ Dev server proxy is working"
echo ""

# Test 2: Try to login with existing user (if any)
echo "2. Attempting to login with test user..."
echo "Enter email address (or press Enter to skip):"
read USER_EMAIL

if [ -n "$USER_EMAIL" ]; then
    echo "Enter password:"
    read -s USER_PASSWORD

    LOGIN_RESPONSE=$(curl -s -X POST http://localhost:3001/api/agent/auth/signin \
      -H "Content-Type: application/json" \
      -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASSWORD\"}")

    echo "Login response: $LOGIN_RESPONSE"
    echo ""

    # Extract access token
    ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

    if [ -z "$ACCESS_TOKEN" ]; then
        echo "❌ Login failed. Check credentials or try a different email."
        exit 1
    fi

    echo "✅ Login successful!"
    echo "Access token: ${ACCESS_TOKEN:0:30}..."
    echo ""

    # Test 3: Try to create a session
    echo "3. Attempting to create a session..."
    SESSION_RESPONSE=$(curl -s -X POST http://localhost:3001/api/agent/sessions/ \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -d '{}')

    echo "Session creation response: $SESSION_RESPONSE"
    echo ""

    # Check if session was created
    SESSION_ID=$(echo $SESSION_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

    if [ -n "$SESSION_ID" ]; then
        echo "✅ Session created successfully!"
        echo "Session ID: $SESSION_ID"
        echo ""

        # Test 4: Get session context
        echo "4. Testing get session context..."
        CONTEXT=$(curl -s http://localhost:3001/api/agent/sessions/$SESSION_ID/context \
          -H "Authorization: Bearer $ACCESS_TOKEN")
        echo "Context response: $CONTEXT"
        echo ""
        echo "✅ All tests passed!"
    else
        echo "❌ Session creation failed!"
        echo "This is the main issue we need to fix."
        echo ""
        echo "Checking for error details..."
        if echo "$SESSION_RESPONSE" | grep -q "403"; then
            echo "Error: 403 Forbidden - Authentication token is valid but session creation is denied"
            echo "Possible causes:"
            echo "  1. Database connection issue"
            echo "  2. User not created in CloudSQL database"
            echo "  3. Permission issue with database"
        elif echo "$SESSION_RESPONSE" | grep -q "401"; then
            echo "Error: 401 Unauthorized - Token is invalid or expired"
        else
            echo "Unknown error. Response: $SESSION_RESPONSE"
        fi
    fi
else
    echo "Skipped login test."
fi

echo ""
echo "=== Debug complete ==="
echo ""
echo "Next steps:"
echo "1. If login works but session creation fails with 403:"
echo "   - Check database connection"
echo "   - Check agent container logs: docker compose logs agent | tail -50"
echo ""
echo "2. If login fails:"
echo "   - Check Supabase dashboard for existing users"
echo "   - Wait for rate limit to reset (~1 hour)"
echo "   - Try with a confirmed email address"
