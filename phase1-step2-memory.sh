#!/bin/bash

echo "🚀 Phase 1 Step 2: Increasing Lambda Memory for Better Performance"

# Increase memory for better performance (more CPU allocated with more memory)
echo "📈 Updating chat function memory to 1024MB..."
aws lambda update-function-configuration \
  --function-name documentgpt-rag-chat \
  --memory-size 1024 \
  --timeout 60 \
  --region us-east-1

echo "📈 Updating parser function memory to 512MB..."
aws lambda update-function-configuration \
  --function-name documentgpt-parser \
  --memory-size 512 \
  --timeout 120 \
  --region us-east-1

echo "📈 Updating indexer function memory to 1024MB..."
aws lambda update-function-configuration \
  --function-name documentgpt-indexer \
  --memory-size 1024 \
  --timeout 300 \
  --region us-east-1

echo "✅ Step 2 Complete: Lambda Memory Increased"