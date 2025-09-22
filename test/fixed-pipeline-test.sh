#!/bin/bash

echo "🧪 Fixed Pipeline Test"
source ./config.sh

# Create test document
echo "Fixed pipeline test document. Microsoft Azure provides cloud computing services including virtual machines and databases." > "$TMPDIR/fixed-test.txt"

# Upload document
UPLOAD_RESP=$(curl -s -X POST "$UPLOAD_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: fixed-test-user" \
  -d '{"filename":"fixed-test.txt","contentType":"text/plain"}')

DOC_ID=$(echo "$UPLOAD_RESP" | jq -r '.docId')
UPLOAD_URL=$(echo "$UPLOAD_RESP" | jq -r '.uploadUrl')

echo "📤 DocId: $DOC_ID"

# Upload file
curl -s -X PUT "$UPLOAD_URL" -H "Content-Type: text/plain" --data-binary "@$TMPDIR/fixed-test.txt"
echo "✅ File uploaded"

# Wait for processing with proper status checking
echo "⏳ Waiting for processing..."
PROCESSED=false
for i in {1..20}; do
    sleep 3
    STATUS_RESP=$(bash ./status-check.sh "$DOC_ID" "fixed-test-user")
    
    echo "[$i] Status: $STATUS_RESP"
    
    PHASE=$(echo "$STATUS_RESP" | jq -r '.phase // "unknown"')
    if [ "$PHASE" = "ready" ]; then
        PROCESSED=true
        echo "✅ Document processed successfully!"
        break
    fi
done

if [ "$PROCESSED" = true ]; then
    # Test chat
    echo "📊 Testing RAG chat..."
    CHAT_RESP=$(curl -s -X POST "$CHAT_BASE/rag-chat" \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      -H "x-user-id: fixed-test-user" \
      -d "{\"question\":\"What cloud services are mentioned?\",\"docId\":\"$DOC_ID\"}")
    
    echo "Chat response: $CHAT_RESP"
    
    ANSWER=$(echo "$CHAT_RESP" | jq -r '.answer // "null"')
    HAS_CONTEXT=$(echo "$CHAT_RESP" | jq -r '.hasContext // false')
    
    if [ "$HAS_CONTEXT" = "true" ] && [ ${#ANSWER} -gt 10 ]; then
        echo "✅ RAG chat working with context"
        echo "✅ PIPELINE FULLY FUNCTIONAL"
        exit 0
    else
        echo "❌ RAG chat not working properly"
        exit 1
    fi
else
    echo "❌ Document processing failed"
    exit 1
fi