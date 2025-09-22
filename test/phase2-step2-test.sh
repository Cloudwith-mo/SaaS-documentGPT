#!/bin/bash

echo "🧪 Testing Step 2: Simple Authentication"
source ./config.sh

# Test 1: Request without API key (should fail)
echo "📊 Test 1: Request without API key..."
RESPONSE1=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -d '{"filename":"auth-test.txt","fileType":"txt"}')

echo "Response: $RESPONSE1"

if echo "$RESPONSE1" | grep -q "API key required"; then
    echo "✅ Authentication blocking working - No API key rejected"
else
    echo "❌ Authentication not blocking requests without API key"
    exit 1
fi

# Test 2: Request with invalid API key (should fail)
echo "📊 Test 2: Request with invalid API key..."
RESPONSE2=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: invalid-key-123" \
  -d '{"filename":"auth-test.txt","fileType":"txt"}')

if echo "$RESPONSE2" | grep -q "Invalid API key"; then
    echo "✅ Invalid API key rejected"
else
    echo "❌ Invalid API key not rejected"
    exit 1
fi

# Test 3: Request with valid API key (should succeed)
echo "📊 Test 3: Request with valid API key..."
RESPONSE3=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: dk-test-key-123" \
  -d '{"filename":"auth-test.txt","fileType":"txt"}')

if echo "$RESPONSE3" | jq -e '.docId' > /dev/null 2>&1; then
    echo "✅ Valid API key accepted"
else
    echo "❌ Valid API key rejected"
    exit 1
fi

# Test 4: Bearer token authentication
echo "📊 Test 4: Bearer token authentication..."
RESPONSE4=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dk-demo-key-456" \
  -d '{"filename":"bearer-test.txt","fileType":"txt"}')

if echo "$RESPONSE4" | jq -e '.docId' > /dev/null 2>&1; then
    echo "✅ Bearer token authentication working"
else
    echo "❌ Bearer token authentication failed"
    exit 1
fi

echo "✅ Step 2 Test PASSED: Simple Authentication Working"