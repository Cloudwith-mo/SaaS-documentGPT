#!/bin/bash

echo "🧪 Testing Step 1: Multi-Tenancy Implementation"
source ./config.sh

# Test 1: Upload with user ID
echo "📊 Test 1: Upload with user ID..."
RESPONSE1=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "x-user-id: test-user-123" \
  -d '{"filename":"multi-tenant-test.txt","fileType":"txt"}')

echo "Response: $RESPONSE1"

if echo "$RESPONSE1" | jq -e '.userId' > /dev/null 2>&1; then
    USER_ID=$(echo "$RESPONSE1" | jq -r '.userId')
    DOC_ID=$(echo "$RESPONSE1" | jq -r '.docId')
    echo "✅ Multi-tenant upload working - User: $USER_ID, Doc: $DOC_ID"
else
    echo "❌ Multi-tenant upload failed"
    exit 1
fi

# Test 2: Upload without user ID (anonymous)
echo "📊 Test 2: Anonymous upload..."
RESPONSE2=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -d '{"filename":"anonymous-test.txt","fileType":"txt"}')

if echo "$RESPONSE2" | jq -e '.userId' > /dev/null 2>&1; then
    ANON_USER=$(echo "$RESPONSE2" | jq -r '.userId')
    echo "✅ Anonymous user generation working - User: $ANON_USER"
else
    echo "❌ Anonymous user generation failed"
    exit 1
fi

# Test 3: Verify user isolation
if [ "$USER_ID" != "$ANON_USER" ]; then
    echo "✅ User isolation working - Different users get different IDs"
else
    echo "❌ User isolation failed - Same user ID generated"
    exit 1
fi

echo "✅ Step 1 Test PASSED: Multi-Tenancy Implementation Working"