#!/bin/bash
API_ID="9voqzgx3ch"
RESOURCE_ID="k19r7h"

# Add GET method
aws apigateway put-method --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method GET --authorization-type NONE

# Add OPTIONS method for CORS
aws apigateway put-method --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method OPTIONS --authorization-type NONE

# Add Lambda integration for GET
aws apigateway put-integration --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method GET --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:995805900737:function:pdf-content-handler/invocations"

# Add CORS integration for OPTIONS
aws apigateway put-integration --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method OPTIONS --type MOCK --request-templates '{"application/json": "{\"statusCode\": 200}"}'

# Add method responses
aws apigateway put-method-response --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method OPTIONS --status-code 200 --response-parameters '{"method.response.header.Access-Control-Allow-Origin": false, "method.response.header.Access-Control-Allow-Methods": false, "method.response.header.Access-Control-Allow-Headers": false}'

# Add integration responses
aws apigateway put-integration-response --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method OPTIONS --status-code 200 --response-parameters '{"method.response.header.Access-Control-Allow-Origin": "'\''https://documentgpt.io'\''", "method.response.header.Access-Control-Allow-Methods": "'\''GET,OPTIONS'\''", "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,Authorization'\''"}'

# Add Lambda permission
aws lambda add-permission --function-name pdf-content-handler --statement-id apigateway-invoke --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:995805900737:9voqzgx3ch/*/*"

# Deploy
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod