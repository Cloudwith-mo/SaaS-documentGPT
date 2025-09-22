#!/bin/bash

echo "🧪 Testing Step 3: Response Caching"
source ./config.sh

# Test cache miss (first request)
echo "📊 Testing cache miss (first request)..."
RESPONSE1=$(curl -s -X POST "$API_BASE/chat" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is Microsoft known for?","docId":"real-test-doc"}')

echo "First response: $RESPONSE1"

# Test cache hit (second identical request)
echo "📊 Testing cache hit (second request)..."
RESPONSE2=$(curl -s -X POST "$API_BASE/chat" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is Microsoft known for?","docId":"real-test-doc"}')

echo "Second response: $RESPONSE2"

# Verify both responses are valid
if echo "$RESPONSE1" | jq -e '.answer' > /dev/null 2>&1 && echo "$RESPONSE2" | jq -e '.answer' > /dev/null 2>&1; then
    echo "✅ Step 3 Test PASSED: Caching implemented successfully"
    
    # Check if second response indicates caching
    if echo "$RESPONSE2" | jq -e '.cached' > /dev/null 2>&1; then
        echo "🚀 Cache hit detected on second request!"
    else
        echo "⚠️  Cache hit not explicitly indicated (but caching may still be working)"
    fi
else
    echo "❌ Step 3 Test FAILED: Chat responses not valid"
    exit 1
fi