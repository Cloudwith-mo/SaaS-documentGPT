#!/bin/bash

echo "🧪 Testing S3 Trigger Fix"
source ./config.sh

# Upload a test document
echo "Test document for trigger verification. Microsoft Azure provides cloud services." > "$TMPDIR/trigger-test.txt"

UPLOAD_RESP=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: trigger-test-user" \
  -d '{"filename":"trigger-test.txt","fileType":"txt"}')

DOC_ID=$(echo "$UPLOAD_RESP" | jq -r '.docId')
UPLOAD_URL=$(echo "$UPLOAD_RESP" | jq -r '.uploadUrl')

echo "📤 Uploading test document..."
echo "DocId: $DOC_ID"

# Upload file
curl -s -X PUT "$UPLOAD_URL" --data-binary "@$TMPDIR/trigger-test.txt"

echo "✅ File uploaded to S3"
echo "⏳ Waiting for S3 trigger to fire..."

# Check status every 3 seconds for 30 seconds
for i in {1..10}; do
    sleep 3
    STATUS_RESP=$(curl -s -X GET "$API_BASE/status?docId=$DOC_ID" \
      -H "x-api-key: $API_KEY" \
      -H "x-user-id: trigger-test-user")
    
    echo "[$i] Status: $STATUS_RESP"
    
    if echo "$STATUS_RESP" | jq -e '.status' > /dev/null 2>&1; then
        echo "✅ S3 trigger working - document processing started!"
        exit 0
    fi
done

echo "❌ S3 trigger still not working after 30 seconds"
exit 1