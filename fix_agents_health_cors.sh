#!/bin/bash
API_ID="9voqzgx3ch"

# Fix agents endpoint (resource: goi09e)
AGENTS_ID="goi09e"
aws apigateway put-integration --rest-api-id $API_ID --resource-id $AGENTS_ID --http-method OPTIONS --type MOCK --request-templates '{"application/json": "{\"statusCode\": 200}"}'
aws apigateway put-method-response --rest-api-id $API_ID --resource-id $AGENTS_ID --http-method OPTIONS --status-code 200 --response-parameters '{"method.response.header.Access-Control-Allow-Origin": false, "method.response.header.Access-Control-Allow-Methods": false, "method.response.header.Access-Control-Allow-Headers": false}'
aws apigateway put-integration-response --rest-api-id $API_ID --resource-id $AGENTS_ID --http-method OPTIONS --status-code 200 --response-parameters '{"method.response.header.Access-Control-Allow-Origin": "'\''https://documentgpt.io'\''", "method.response.header.Access-Control-Allow-Methods": "'\''GET,OPTIONS'\''", "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,Authorization'\''"}'

# Find health endpoint
HEALTH_ID=$(aws apigateway get-resources --rest-api-id $API_ID --query 'items[?pathPart==`health`].id' --output text | head -1)
echo "Health resource ID: $HEALTH_ID"

# Fix health endpoint
aws apigateway put-method --rest-api-id $API_ID --resource-id $HEALTH_ID --http-method OPTIONS --authorization-type NONE
aws apigateway put-integration --rest-api-id $API_ID --resource-id $HEALTH_ID --http-method OPTIONS --type MOCK --request-templates '{"application/json": "{\"statusCode\": 200}"}'
aws apigateway put-method-response --rest-api-id $API_ID --resource-id $HEALTH_ID --http-method OPTIONS --status-code 200 --response-parameters '{"method.response.header.Access-Control-Allow-Origin": false, "method.response.header.Access-Control-Allow-Methods": false, "method.response.header.Access-Control-Allow-Headers": false}'
aws apigateway put-integration-response --rest-api-id $API_ID --resource-id $HEALTH_ID --http-method OPTIONS --status-code 200 --response-parameters '{"method.response.header.Access-Control-Allow-Origin": "'\''https://documentgpt.io'\''", "method.response.header.Access-Control-Allow-Methods": "'\''GET,OPTIONS'\''", "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,Authorization'\''"}'

# Deploy
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod