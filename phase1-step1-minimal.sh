#!/bin/bash

echo "🚀 Phase 1 Step 1: Adding Minimal Provisioned Concurrency"

# Add minimal provisioned concurrency to chat function only (most critical)
echo "📈 Setting up provisioned concurrency for chat function..."
aws lambda put-provisioned-concurrency-config \
  --function-name documentgpt-rag-chat \
  --qualifier 1 \
  --provisioned-concurrent-executions 2 \
  --region us-east-1

echo "📊 Checking status..."
aws lambda get-provisioned-concurrency-config \
  --function-name documentgpt-rag-chat \
  --qualifier 1 \
  --region us-east-1

echo "✅ Step 1 Complete: Minimal Provisioned Concurrency Added"