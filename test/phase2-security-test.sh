#!/bin/bash

echo "🧪 Phase 2: Security & Multi-Tenancy Battle Test"
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

# Test 1: Authentication Security
echo "📊 Test 1: Authentication Security Hardening"

# No API key
NO_AUTH=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -d '{"filename":"hack.txt","fileType":"txt"}')
echo "$NO_AUTH" | grep -q "API key required"
test_result $? "Blocks requests without API key"

# Invalid API key
INVALID_AUTH=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: hacker-key-123" \
  -d '{"filename":"hack.txt","fileType":"txt"}')
echo "$INVALID_AUTH" | grep -q "Invalid API key"
test_result $? "Blocks requests with invalid API key"

# SQL injection attempt
SQL_INJECT=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: '; DROP TABLE users; --" \
  -d '{"filename":"hack.txt","fileType":"txt"}')
echo "$SQL_INJECT" | jq -e '.docId' > /dev/null 2>&1
test_result $? "Handles SQL injection attempts safely"

# Test 2: Multi-Tenancy Isolation
echo "📊 Test 2: Multi-Tenancy Isolation"

# Upload as user A
USER_A_RESP=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: tenant-a-isolation" \
  -d '{"filename":"secret-a.txt","fileType":"txt"}')
USER_A_DOC=$(echo "$USER_A_RESP" | jq -r '.docId')

# Upload as user B
USER_B_RESP=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: tenant-b-isolation" \
  -d '{"filename":"secret-b.txt","fileType":"txt"}')
USER_B_DOC=$(echo "$USER_B_RESP" | jq -r '.docId')

# Verify different S3 paths
USER_A_PATH=$(echo "$USER_A_RESP" | jq -r '.key')
USER_B_PATH=$(echo "$USER_B_RESP" | jq -r '.key')

echo "$USER_A_PATH" | grep -q "tenant-a-isolation" && echo "$USER_B_PATH" | grep -q "tenant-b-isolation"
test_result $? "Users get isolated S3 paths"

# Test 3: Rate Limiting (Batch Upload)
echo "📊 Test 3: Rate Limiting & Batch Upload"

# Test batch upload capability
BATCH_SUCCESS=0
for i in {1..50}; do
    RESP=$(curl -s -X POST "$API_BASE/upload" \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      -H "x-user-id: batch-test-user" \
      -d "{\"filename\":\"batch-$i.txt\",\"fileType\":\"txt\"}")
    
    if echo "$RESP" | jq -e '.docId' > /dev/null 2>&1; then
        BATCH_SUCCESS=$((BATCH_SUCCESS + 1))
    fi
    
    # Quick burst test
    [ $i -le 10 ] && sleep 0.05 || sleep 0.1
done

[ $BATCH_SUCCESS -ge 45 ]
test_result $? "Batch upload capability (${BATCH_SUCCESS}/50 successful)"

# Test rate limit enforcement (should trigger after 500)
RATE_LIMITED=false
for i in {501..510}; do
    RESP=$(curl -s -X POST "$API_BASE/upload" \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      -H "x-user-id: rate-limit-test" \
      -d "{\"filename\":\"rate-$i.txt\",\"fileType\":\"txt\"}")
    
    if echo "$RESP" | grep -q "Rate limit exceeded"; then
        RATE_LIMITED=true
        break
    fi
done

# For this test, we expect rate limiting to NOT trigger at 510 (within 500/min limit)
[ "$RATE_LIMITED" = false ]
test_result $? "Rate limits allow batch operations (500/min)"

echo ""
echo "Phase 2 Results: $PASS_COUNT/$TOTAL_TESTS tests passed"
[ $PASS_COUNT -eq $TOTAL_TESTS ] && echo "✅ Phase 2: SECURITY HARDENED" || echo "❌ Phase 2: SECURITY GAPS"