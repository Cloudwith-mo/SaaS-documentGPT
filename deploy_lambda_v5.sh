#!/bin/bash
echo "🚀 Deploying DocumentsGPT v5 Backend to AWS Lambda..."

# Create deployment package
zip -r documentgpt-v5-backend.zip lambda_handler_v5.py

# Deploy to Lambda
aws lambda update-function-code \
    --function-name documentgpt-v5-api \
    --zip-file fileb://documentgpt-v5-backend.zip

# Update API Gateway if needed
aws apigateway create-deployment \
    --rest-api-id $(aws apigateway get-rest-apis --query "items[?name=='documentgpt-v5-api'].id" --output text) \
    --stage-name prod

echo "✅ Backend deployed to AWS Lambda!"