#!/bin/bash

echo "🚀 Phase 1 Step 1: Adding Provisioned Concurrency (Fixed)"

# Publish versions first, then add provisioned concurrency
echo "📦 Publishing function versions..."

CHAT_VERSION=$(aws lambda publish-version --function-name documentgpt-rag-chat --region us-east-1 --query 'Version' --output text)
PARSER_VERSION=$(aws lambda publish-version --function-name documentgpt-parser --region us-east-1 --query 'Version' --output text)
INDEXER_VERSION=$(aws lambda publish-version --function-name documentgpt-indexer --region us-east-1 --query 'Version' --output text)

echo "📈 Setting up provisioned concurrency..."
aws lambda put-provisioned-concurrency-config \
  --function-name documentgpt-rag-chat \
  --qualifier $CHAT_VERSION \
  --provisioned-concurrent-executions 5 \
  --region us-east-1

aws lambda put-provisioned-concurrency-config \
  --function-name documentgpt-parser \
  --qualifier $PARSER_VERSION \
  --provisioned-concurrent-executions 3 \
  --region us-east-1

aws lambda put-provisioned-concurrency-config \
  --function-name documentgpt-indexer \
  --qualifier $INDEXER_VERSION \
  --provisioned-concurrent-executions 3 \
  --region us-east-1

echo "✅ Provisioned concurrency configured for versions: Chat=$CHAT_VERSION, Parser=$PARSER_VERSION, Indexer=$INDEXER_VERSION"