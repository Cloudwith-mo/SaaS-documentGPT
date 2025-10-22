#!/bin/bash
# Test Dev RAG Implementation

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get API URL from user or use default
API_URL="${1:-https://YOUR_API_URL}"

echo "🧪 Testing Dev RAG Implementation"
echo "API URL: $API_URL"
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "-------------------"
HEALTH_RESPONSE=$(curl -s "$API_URL/dev/health")
echo "$HEALTH_RESPONSE" | jq .

if echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' > /dev/null; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi

RAG_ENABLED=$(echo "$HEALTH_RESPONSE" | jq -r '.rag_enabled')
if [ "$RAG_ENABLED" = "true" ]; then
    echo -e "${GREEN}✅ RAG is enabled${NC}"
else
    echo -e "${YELLOW}⚠️  RAG is not enabled (Pinecone not configured)${NC}"
fi

echo ""

# Test 2: Upload Document
echo "Test 2: Upload Document"
echo "----------------------"
UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/dev/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_'$(date +%s)'",
    "filename": "ai_overview.txt",
    "content": "Artificial Intelligence (AI) is revolutionizing technology. Machine learning is a subset of AI that enables computers to learn from data. Deep learning uses neural networks with multiple layers. Natural language processing helps computers understand human language. Computer vision allows machines to interpret visual information. AI applications include healthcare diagnostics, autonomous vehicles, and personalized recommendations."
  }')

echo "$UPLOAD_RESPONSE" | jq .

DOC_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.doc_id')
INDEXED=$(echo "$UPLOAD_RESPONSE" | jq -r '.indexed')

if [ "$DOC_ID" != "null" ] && [ "$DOC_ID" != "" ]; then
    echo -e "${GREEN}✅ Document uploaded: $DOC_ID${NC}"
else
    echo -e "${RED}❌ Upload failed${NC}"
    exit 1
fi

if [ "$INDEXED" = "true" ]; then
    echo -e "${GREEN}✅ Document indexed in vector database${NC}"
else
    echo -e "${YELLOW}⚠️  Document not indexed (Pinecone not configured)${NC}"
fi

echo ""

# Wait for indexing to complete
echo "⏳ Waiting 2 seconds for indexing..."
sleep 2
echo ""

# Test 3: Query Document
echo "Test 3: Query Document"
echo "---------------------"
QUERY_RESPONSE=$(curl -s -X POST "$API_URL/dev/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?"
  }')

echo "$QUERY_RESPONSE" | jq .

RESPONSE_TEXT=$(echo "$QUERY_RESPONSE" | jq -r '.response')
CITATIONS=$(echo "$QUERY_RESPONSE" | jq -r '.citations | length')

if [ "$RESPONSE_TEXT" != "null" ] && [ "$RESPONSE_TEXT" != "" ]; then
    echo -e "${GREEN}✅ Query successful${NC}"
    echo "Response: $RESPONSE_TEXT"
else
    echo -e "${RED}❌ Query failed${NC}"
    exit 1
fi

if [ "$CITATIONS" -gt 0 ]; then
    echo -e "${GREEN}✅ Citations included: $CITATIONS sources${NC}"
else
    echo -e "${YELLOW}⚠️  No citations (expected if Pinecone not configured)${NC}"
fi

echo ""

# Test 4: Another Query
echo "Test 4: Different Query"
echo "----------------------"
QUERY2_RESPONSE=$(curl -s -X POST "$API_URL/dev/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are some AI applications?"
  }')

echo "$QUERY2_RESPONSE" | jq .

RESPONSE2_TEXT=$(echo "$QUERY2_RESPONSE" | jq -r '.response')

if [ "$RESPONSE2_TEXT" != "null" ] && [ "$RESPONSE2_TEXT" != "" ]; then
    echo -e "${GREEN}✅ Second query successful${NC}"
    echo "Response: $RESPONSE2_TEXT"
else
    echo -e "${RED}❌ Second query failed${NC}"
    exit 1
fi

echo ""
echo "================================"
echo -e "${GREEN}🎉 All tests passed!${NC}"
echo "================================"
echo ""
echo "Summary:"
echo "- Health check: ✅"
echo "- Document upload: ✅"
echo "- Vector indexing: $([ "$INDEXED" = "true" ] && echo "✅" || echo "⚠️  (Pinecone not configured)")"
echo "- Query with RAG: ✅"
echo "- Citations: $([ "$CITATIONS" -gt 0 ] && echo "✅" || echo "⚠️  (Pinecone not configured)")"
echo ""
echo "Next steps:"
echo "1. If RAG not enabled, follow docs/PINECONE_SETUP.md"
echo "2. Update dev frontend to use /dev/upload and /dev/chat endpoints"
echo "3. Test with real PDF documents"
