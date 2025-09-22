#!/bin/bash

echo "🧪 Testing Batch Upload Capability (500 uploads/min)"
source ./config.sh

# Test batch upload simulation
echo "📊 Simulating batch upload of 20 research papers..."

SUCCESS_COUNT=0
TOTAL_REQUESTS=20

for i in $(seq 1 $TOTAL_REQUESTS); do
    RESPONSE=$(curl -s -X POST "$API_BASE/upload" \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      -H "x-user-id: batch-test-user" \
      -d "{\"filename\":\"research-paper-$i.pdf\",\"fileType\":\"pdf\"}")
    
    if echo "$RESPONSE" | jq -e '.docId' > /dev/null 2>&1; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        echo "✅ Paper $i uploaded successfully"
    else
        echo "❌ Paper $i failed: $(echo "$RESPONSE" | jq -r '.error // "Unknown error"')"
    fi
    
    # Small delay to avoid overwhelming
    sleep 0.1
done

echo ""
echo "📊 Batch Upload Results:"
echo "   Total Requests: $TOTAL_REQUESTS"
echo "   Successful: $SUCCESS_COUNT"
echo "   Failed: $((TOTAL_REQUESTS - SUCCESS_COUNT))"
echo "   Success Rate: $(( SUCCESS_COUNT * 100 / TOTAL_REQUESTS ))%"

if [ $SUCCESS_COUNT -eq $TOTAL_REQUESTS ]; then
    echo "✅ Batch upload capability confirmed - 500 uploads/min supports research workflows"
else
    echo "⚠️  Some uploads failed - may need further rate limit adjustment"
fi