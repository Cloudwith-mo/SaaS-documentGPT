#!/bin/bash

# Fix CORS for DocumentGPT API Gateway
API_ID="i1dy8i3692"
REGION="us-east-1"

echo "🔧 Fixing CORS for API Gateway: $API_ID"

# Deploy the API to apply Lambda changes
echo "📦 Deploying API to prod stage..."
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region $REGION

echo "✅ CORS fix complete!"
echo ""
echo "🧪 Test your chatbot at: https://documentgpt.io/backup.html"
echo "⏱️  Wait 10-15 seconds for deployment to propagate"
