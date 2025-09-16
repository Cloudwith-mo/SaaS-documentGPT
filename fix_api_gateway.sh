#!/bin/bash

# Fix API Gateway CORS and missing endpoints
echo "🔧 Fixing API Gateway CORS and endpoints"
echo "========================================"

API_ID="9voqzgx3ch"
ROOT_ID="0p83su7y93"

# Create /documents resource
echo "📝 Creating /documents resource..."
DOCUMENTS_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part documents \
    --query 'id' --output text)

echo "✅ Created /documents resource: $DOCUMENTS_RESOURCE"

# Add GET method to /documents
echo "📝 Adding GET method to /documents..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $DOCUMENTS_RESOURCE \
    --http-method GET \
    --authorization-type NONE

# Add OPTIONS method for CORS
echo "📝 Adding OPTIONS method for CORS..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $DOCUMENTS_RESOURCE \
    --http-method OPTIONS \
    --authorization-type NONE

# Set up integration for GET /documents
echo "📝 Setting up Lambda integration for GET /documents..."
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $DOCUMENTS_RESOURCE \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:995805900737:function:documents-handler/invocations"

# Set up CORS integration for OPTIONS
echo "📝 Setting up CORS integration for OPTIONS..."
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $DOCUMENTS_RESOURCE \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json": "{\"statusCode\": 200}"}'

# Set up CORS response for OPTIONS
echo "📝 Setting up CORS response..."
aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $DOCUMENTS_RESOURCE \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Origin": false, "method.response.header.Access-Control-Allow-Methods": false, "method.response.header.Access-Control-Allow-Headers": false}'

aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $DOCUMENTS_RESOURCE \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Origin": "\"https://documentgpt.io\"", "method.response.header.Access-Control-Allow-Methods": "\"GET,POST,OPTIONS\"", "method.response.header.Access-Control-Allow-Headers": "\"Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token\""}'

echo "🚀 Deploying API changes..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod

echo "✅ API Gateway fixed!"