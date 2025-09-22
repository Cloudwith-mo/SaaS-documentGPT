#!/bin/bash

echo "🧪 Phase 1: Infrastructure & Performance Battle Test"
source ./config.sh

PASS_COUNT=0
TOTAL_TESTS=0

test_result() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ $1 -eq 0 ]; then
        PASS_COUNT=$((PASS_COUNT + 1))
        echo "✅ PASS: $2"
    else
        echo "❌ FAIL: $2"
    fi
}

# Test 1: Lambda Memory Performance
echo "📊 Test 1: Lambda Memory & Timeout Performance"
START_TIME=$(date +%s)
RESPONSE=$(curl -s -X POST "$API_BASE/chat" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: perf-test-user" \
  -d '{"question":"What is Microsoft known for?","docId":"real-test-doc"}')
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if echo "$RESPONSE" | jq -e '.answer' > /dev/null 2>&1 && [ $DURATION -lt 10 ]; then
    test_result 0 "Lambda performance under 10s"
else
    test_result 1 "Lambda performance (took ${DURATION}s or failed)"
fi

# Test 2: Concurrent Load Test
echo "📊 Test 2: Concurrent Request Handling"
CONCURRENT_SUCCESS=0
for i in {1..5}; do
    (
        RESP=$(curl -s -X POST "$API_BASE/upload" \
          -H "Content-Type: application/json" \
          -H "x-api-key: $API_KEY" \
          -H "x-user-id: concurrent-user-$i" \
          -d "{\"filename\":\"concurrent-$i.txt\",\"fileType\":\"txt\"}")
        if echo "$RESP" | jq -e '.docId' > /dev/null 2>&1; then
            echo "concurrent-success" >> /tmp/concurrent_results.txt
        fi
    ) &
done
wait
CONCURRENT_SUCCESS=$(wc -l < /tmp/concurrent_results.txt 2>/dev/null || echo 0)
rm -f /tmp/concurrent_results.txt

if [ $CONCURRENT_SUCCESS -ge 4 ]; then
    test_result 0 "Concurrent requests (${CONCURRENT_SUCCESS}/5 successful)"
else
    test_result 1 "Concurrent requests (${CONCURRENT_SUCCESS}/5 successful)"
fi

# Test 3: Memory Optimization Validation
echo "📊 Test 3: Memory Optimization Check"
MEMORY_TEST=$(aws lambda get-function-configuration --function-name documentgpt-rag-chat --region us-east-1 --query 'MemorySize' --output text)
if [ "$MEMORY_TEST" -ge 1024 ]; then
    test_result 0 "Lambda memory optimization (${MEMORY_TEST}MB)"
else
    test_result 1 "Lambda memory optimization (${MEMORY_TEST}MB < 1024MB)"
fi

echo ""
echo "Phase 1 Results: $PASS_COUNT/$TOTAL_TESTS tests passed"
[ $PASS_COUNT -eq $TOTAL_TESTS ] && echo "✅ Phase 1: INFRASTRUCTURE SOLID" || echo "❌ Phase 1: NEEDS ATTENTION"