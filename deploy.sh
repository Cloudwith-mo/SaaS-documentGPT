#!/bin/bash

# Create deployment package
cd lambda
zip -r chat.zip chat.js

# Create Lambda function
aws lambda create-function \
  --function-name documentgpt-chat \
  --runtime nodejs18.x \
  --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/lambda-execution-role \
  --handler chat.handler \
  --zip-file fileb://chat.zip \
  --environment Variables="{OPENAI_API_KEY=$(aws secretsmanager get-secret-value --secret-id OPENAI_API_KEY --query SecretString --output text)}" \
  --timeout 30

# Create API Gateway
API_ID=$(aws apigatewayv2 create-api \
  --name documentgpt-api \
  --protocol-type HTTP \
  --cors-configuration AllowOrigins="*",AllowMethods="*",AllowHeaders="*" \
  --query ApiId --output text)

# Create integration
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id $API_ID \
  --integration-type AWS_PROXY \
  --integration-uri arn:aws:lambda:us-east-1:$(aws sts get-caller-identity --query Account --output text):function:documentgpt-chat \
  --payload-format-version 2.0 \
  --query IntegrationId --output text)

# Create route
aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST /chat" \
  --target integrations/$INTEGRATION_ID

# Create stage
aws apigatewayv2 create-stage \
  --api-id $API_ID \
  --stage-name prod \
  --auto-deploy

# Add Lambda permission
aws lambda add-permission \
  --function-name documentgpt-chat \
  --statement-id api-gateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/*"

echo "API URL: https://$API_ID.execute-api.us-east-1.amazonaws.com/prod"