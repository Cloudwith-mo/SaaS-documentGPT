#!/bin/bash

echo "🚀 Phase 1 Step 1: Adding Provisioned Concurrency"

# Add provisioned concurrency to critical Lambda functions
echo "📈 Setting up provisioned concurrency for chat function..."
aws lambda put-provisioned-concurrency-config \
  --function-name documentgpt-rag-chat \
  --qualifier '$LATEST' \
  --provisioned-concurrent-executions 5 \
  --region us-east-1

echo "📈 Setting up provisioned concurrency for parser function..."
aws lambda put-provisioned-concurrency-config \
  --function-name documentgpt-parser \
  --qualifier '$LATEST' \
  --provisioned-concurrent-executions 3 \
  --region us-east-1

echo "📈 Setting up provisioned concurrency for indexer function..."
aws lambda put-provisioned-concurrency-config \
  --function-name documentgpt-indexer \
  --qualifier '$LATEST' \
  --provisioned-concurrent-executions 3 \
  --region us-east-1

echo "✅ Provisioned concurrency configured"
echo "⏳ Waiting 30 seconds for provisioned concurrency to initialize..."
sleep 30

echo "📊 Checking provisioned concurrency status..."
aws lambda get-provisioned-concurrency-config \
  --function-name documentgpt-rag-chat \
  --qualifier '$LATEST' \
  --region us-east-1

echo "✅ Step 1 Complete: Provisioned Concurrency Added"