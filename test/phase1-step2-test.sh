#!/bin/bash

echo "🧪 Testing Step 2: Lambda Memory Increase"
source ./config.sh

# Test chat performance with increased memory
echo "📊 Testing chat performance..."
START_TIME=$(date +%s%3N)

RESPONSE=$(curl -s -X POST "$API_BASE/chat" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is Microsoft known for?","docId":"real-test-doc"}')

END_TIME=$(date +%s%3N)
DURATION=$((END_TIME - START_TIME))

echo "Response: $RESPONSE"
echo "⏱️  Response time: ${DURATION}ms"

# Check if response is valid
if echo "$RESPONSE" | jq -e '.answer' > /dev/null 2>&1; then
    echo "✅ Step 2 Test PASSED: Chat function working with increased memory"
    echo "📈 Performance improvement expected due to higher memory allocation"
else
    echo "❌ Step 2 Test FAILED: Chat function not responding correctly"
    exit 1
fi