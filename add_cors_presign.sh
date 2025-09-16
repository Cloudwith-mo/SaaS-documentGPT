#!/bin/bash
API_ID="9voqzgx3ch"
RESOURCE_ID="eb8prv"

# Add CORS integration for OPTIONS
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json": "{\"statusCode\": 200}"}'

# Add method response
aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Origin": false, "method.response.header.Access-Control-Allow-Methods": false, "method.response.header.Access-Control-Allow-Headers": false}'

# Add integration response
aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Origin": "'\''https://documentgpt.io'\''",
        "method.response.header.Access-Control-Allow-Methods": "'\''POST,OPTIONS'\''",
        "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,Authorization'\''"
    }'

# Deploy
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod