#!/bin/bash
# Test LangChain deployment with real user simulation

API_URL="https://snfkv26x4h5rojzzhql622whym0hvxjy.lambda-url.us-east-1.on.aws"

echo "🧪 Testing LangChain/MCP Deployment"
echo "===================================="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
curl -s "${API_URL}/dev/health" | jq '.'
echo ""

# Test 2: Upload Document
echo "Test 2: Upload Test Document"
DOC_RESPONSE=$(curl -s -X POST "${API_URL}/dev/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_langchain",
    "filename": "test_doc.txt",
    "content": "LangChain is a framework for developing applications powered by language models. It enables applications that are context-aware and can reason. Key features include: 1) Modular components for working with language models, 2) Off-the-shelf chains for common tasks, 3) Agents that can use tools and make decisions."
  }')

echo "$DOC_RESPONSE" | jq '.'
DOC_ID=$(echo "$DOC_RESPONSE" | jq -r '.doc_id')
echo "Document ID: $DOC_ID"
echo ""

# Wait for vectorization
echo "⏳ Waiting 3 seconds for vectorization..."
sleep 3
echo ""

# Test 3: Simple Question
echo "Test 3: Simple Question - What is LangChain?"
curl -s -X POST "${API_URL}/dev/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What is LangChain?\",
    \"doc_id\": \"$DOC_ID\"
  }" | jq '.'
echo ""

# Test 4: Specific Question
echo "Test 4: Specific Question - What are the key features?"
curl -s -X POST "${API_URL}/dev/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What are the key features of LangChain?\",
    \"doc_id\": \"$DOC_ID\"
  }" | jq '.'
echo ""

# Test 5: Question requiring web search (no doc context)
echo "Test 5: Web Search Test - Latest AI news"
curl -s -X POST "${API_URL}/dev/chat" \
  -H "Content-Type: application/json" \
  -d '{
    \"query\": \"What is the latest news about GPT-4?\"
  }' | jq '.'
echo ""

echo "✅ All tests complete!"
