#!/bin/bash
API_ID="ns7ycm3h04"
ROOT_ID="q09bfdsqhg"
LAMBDA_ARN="arn:aws:lambda:us-east-1:995805900737:function:documentgpt-v5-api"

echo "🔧 Setting up API Gateway for v5 endpoints..."

# Create /api/v5 resource
V5_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part "v5" \
    --query "id" --output text)

# Create endpoints
for endpoint in "chat" "search" "models" "presets"; do
    echo "Creating /$endpoint endpoint..."
    
    RESOURCE_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $V5_RESOURCE \
        --path-part $endpoint \
        --query "id" --output text)
    
    # Create method
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method ANY \
        --authorization-type NONE
    
    # Set integration
    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method ANY \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations"
    
    # Add Lambda permission
    aws lambda add-permission \
        --function-name documentgpt-v5-api \
        --statement-id "api-gateway-$endpoint" \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "arn:aws:execute-api:us-east-1:995805900737:$API_ID/*/*"
done

# Deploy API
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod

echo "✅ API Gateway configured!"
echo "🌐 Base URL: https://$API_ID.execute-api.us-east-1.amazonaws.com/prod/v5/"