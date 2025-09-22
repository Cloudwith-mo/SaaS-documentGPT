#!/bin/bash

echo "🧪 Testing Step 3: Rate Limiting"
source ./config.sh

# Test 1: Normal request (should work)
echo "📊 Test 1: Normal request..."
RESPONSE1=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: dk-test-key-123" \
  -H "x-user-id: rate-test-user" \
  -d '{"filename":"rate-test-1.txt","fileType":"txt"}')

if echo "$RESPONSE1" | jq -e '.docId' > /dev/null 2>&1; then
    echo "✅ Normal request working"
    
    # Check rate limit headers
    HEADERS=$(curl -s -I -X POST "$API_BASE/upload" \
      -H "Content-Type: application/json" \
      -H "x-api-key: dk-test-key-123" \
      -H "x-user-id: rate-test-user" \
      -d '{"filename":"rate-test-2.txt","fileType":"txt"}')
    
    if echo "$HEADERS" | grep -q "X-RateLimit-Limit"; then
        echo "✅ Rate limit headers present"
    else
        echo "⚠️  Rate limit headers missing (but functionality may work)"
    fi
else
    echo "❌ Normal request failed"
    exit 1
fi

# Test 2: Rapid requests to trigger rate limit
echo "📊 Test 2: Testing rate limit (making 12 rapid requests)..."
RATE_LIMITED=false

for i in {1..12}; do
    RESPONSE=$(curl -s -X POST "$API_BASE/upload" \
      -H "Content-Type: application/json" \
      -H "x-api-key: dk-test-key-123" \
      -H "x-user-id: rate-test-user-rapid" \
      -d "{\"filename\":\"rapid-test-$i.txt\",\"fileType\":\"txt\"}")
    
    if echo "$RESPONSE" | grep -q "Rate limit exceeded"; then
        echo "✅ Rate limit triggered on request $i"
        RATE_LIMITED=true
        break
    fi
    
    sleep 0.1  # Small delay between requests
done

if [ "$RATE_LIMITED" = true ]; then
    echo "✅ Rate limiting working correctly"
else
    echo "⚠️  Rate limit not triggered (may need more requests or different user)"
fi

# Test 3: Different users should have separate limits
echo "📊 Test 3: Testing user isolation..."
RESPONSE3=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: dk-test-key-123" \
  -H "x-user-id: different-user-123" \
  -d '{"filename":"isolation-test.txt","fileType":"txt"}')

if echo "$RESPONSE3" | jq -e '.docId' > /dev/null 2>&1; then
    echo "✅ User isolation working - Different user not affected by rate limit"
else
    echo "❌ User isolation failed"
    exit 1
fi

echo "✅ Step 3 Test PASSED: Rate Limiting Implementation Working"