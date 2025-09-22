#!/bin/bash

echo "🧪 Phase 3: End-to-End Pipeline Battle Test"
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

# Test 1: Multi-Format Document Processing
echo "📊 Test 1: Multi-Format Document Processing"

# Create test documents
echo "This is a comprehensive test document for DocumentGPT. Microsoft Azure provides cloud computing services including virtual machines, databases, and AI services. The document contains multiple paragraphs to test chunking and indexing. Azure supports various programming languages and frameworks. Users can deploy applications globally using Azure's data centers." > "$TMPDIR/comprehensive-test.txt"

# Upload and process
UPLOAD_RESP=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: pipeline-test-user" \
  -d '{"filename":"comprehensive-test.txt","fileType":"txt"}')

DOC_ID=$(echo "$UPLOAD_RESP" | jq -r '.docId')
UPLOAD_URL=$(echo "$UPLOAD_RESP" | jq -r '.uploadUrl')

if [ "$DOC_ID" != "null" ] && [ "$UPLOAD_URL" != "null" ]; then
    test_result 0 "Document upload URL generation"
    
    # Upload file
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$UPLOAD_URL" --data-binary "@$TMPDIR/comprehensive-test.txt")
    [ "$HTTP_CODE" = "200" ]
    test_result $? "Document file upload (HTTP $HTTP_CODE)"
    
    # Wait for processing with timeout
    echo "⏳ Waiting for document processing (max 60s)..."
    PROCESSED=false
    for i in {1..12}; do
        sleep 5
        STATUS_RESP=$(curl -s -X GET "$API_BASE/status/$DOC_ID" \
          -H "x-api-key: $API_KEY" \
          -H "x-user-id: pipeline-test-user")
        
        if echo "$STATUS_RESP" | jq -e '.status' | grep -q "s1.ckpt-08.chat"; then
            PROCESSED=true
            break
        fi
        echo "   Processing... (${i}/12)"
    done
    
    [ "$PROCESSED" = true ]
    test_result $? "Document processing pipeline completion"
    
    if [ "$PROCESSED" = true ]; then
        # Test 2: RAG Chat Functionality
        echo "📊 Test 2: RAG Chat & Context Retrieval"
        
        # Test specific question about content
        CHAT_RESP=$(curl -s -X POST "$API_BASE/chat" \
          -H "Content-Type: application/json" \
          -H "x-api-key: $API_KEY" \
          -H "x-user-id: pipeline-test-user" \
          -d "{\"question\":\"What cloud services does Azure provide?\",\"docId\":\"$DOC_ID\"}")
        
        ANSWER=$(echo "$CHAT_RESP" | jq -r '.answer')
        HAS_CONTEXT=$(echo "$CHAT_RESP" | jq -r '.hasContext')
        
        [ "$HAS_CONTEXT" = "true" ] && [ ${#ANSWER} -gt 20 ]
        test_result $? "RAG chat with context retrieval"
        
        # Test question not in document
        UNRELATED_RESP=$(curl -s -X POST "$API_BASE/chat" \
          -H "Content-Type: application/json" \
          -H "x-api-key: $API_KEY" \
          -H "x-user-id: pipeline-test-user" \
          -d "{\"question\":\"What is the capital of Mars?\",\"docId\":\"$DOC_ID\"}")
        
        UNRELATED_ANSWER=$(echo "$UNRELATED_RESP" | jq -r '.answer')
        echo "$UNRELATED_ANSWER" | grep -qi "context\|document\|information"
        test_result $? "Handles questions outside document scope"
        
        # Test 3: Caching Performance
        echo "📊 Test 3: Response Caching Performance"
        
        # First request (cache miss)
        START_TIME=$(date +%s%3N)
        FIRST_RESP=$(curl -s -X POST "$API_BASE/chat" \
          -H "Content-Type: application/json" \
          -H "x-api-key: $API_KEY" \
          -H "x-user-id: cache-test-user" \
          -d "{\"question\":\"What is Microsoft Azure?\",\"docId\":\"$DOC_ID\"}")
        FIRST_TIME=$(date +%s%3N)
        FIRST_DURATION=$((FIRST_TIME - START_TIME))
        
        # Second request (potential cache hit)
        START_TIME=$(date +%s%3N)
        SECOND_RESP=$(curl -s -X POST "$API_BASE/chat" \
          -H "Content-Type: application/json" \
          -H "x-api-key: $API_KEY" \
          -H "x-user-id: cache-test-user" \
          -d "{\"question\":\"What is Microsoft Azure?\",\"docId\":\"$DOC_ID\"}")
        SECOND_TIME=$(date +%s%3N)
        SECOND_DURATION=$((SECOND_TIME - START_TIME))
        
        # Both should return valid answers
        echo "$FIRST_RESP" | jq -e '.answer' > /dev/null && echo "$SECOND_RESP" | jq -e '.answer' > /dev/null
        test_result $? "Caching system functional (${FIRST_DURATION}ms vs ${SECOND_DURATION}ms)"
    else
        test_result 1 "RAG chat (document not processed)"
        test_result 1 "Context handling (document not processed)"
        test_result 1 "Caching system (document not processed)"
    fi
else
    test_result 1 "Document upload URL generation"
    test_result 1 "Document file upload"
    test_result 1 "Document processing pipeline"
    test_result 1 "RAG chat"
    test_result 1 "Context handling"
    test_result 1 "Caching system"
fi

# Test 4: Error Handling & Edge Cases
echo "📊 Test 4: Error Handling & Edge Cases"

# Test chat with non-existent document
NONEXISTENT_RESP=$(curl -s -X POST "$API_BASE/chat" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: edge-test-user" \
  -d '{"question":"Test question","docId":"nonexistent-doc-123"}')

echo "$NONEXISTENT_RESP" | jq -e '.answer' > /dev/null
test_result $? "Handles non-existent document gracefully"

# Test empty question
EMPTY_RESP=$(curl -s -X POST "$API_BASE/chat" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: edge-test-user" \
  -d "{\"question\":\"\",\"docId\":\"$DOC_ID\"}")

echo "$EMPTY_RESP" | jq -e '.answer' > /dev/null
test_result $? "Handles empty questions gracefully"

echo ""
echo "Phase 3 Results: $PASS_COUNT/$TOTAL_TESTS tests passed"
[ $PASS_COUNT -eq $TOTAL_TESTS ] && echo "✅ Phase 3: PIPELINE BATTLE-TESTED" || echo "❌ Phase 3: PIPELINE ISSUES"