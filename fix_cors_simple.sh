#!/bin/bash

# Simple CORS fix
echo "🔧 Fixing CORS with simple approach"
echo "==================================="

API_ID="9voqzgx3ch"
DOCUMENTS_RESOURCE="cotdc6"

# Fix the integration response with proper escaping
echo "📝 Fixing CORS integration response..."
aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $DOCUMENTS_RESOURCE \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Origin": "'\''https://documentgpt.io'\''",
        "method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,OPTIONS'\''",
        "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,Authorization'\''"
    }'

# Deploy changes
echo "🚀 Deploying API changes..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod

echo "✅ CORS fixed!"