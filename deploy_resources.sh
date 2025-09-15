#!/bin/bash

echo "🚀 Deploying AWS Resources for DocumentGPT..."

# Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file aws_resources.yml \
  --stack-name documentgpt-resources \
  --capabilities CAPABILITY_IAM \
  --region us-east-1

echo "✅ AWS Resources deployed!"

# Deploy serverless functions
echo "🚀 Deploying Serverless Functions..."
./deploy.sh

echo "✅ All resources deployed successfully!"

# Update test configuration with new endpoints
echo "📝 Updating test configuration..."
API_URL=$(aws cloudformation describe-stacks \
  --stack-name documentgpt-api-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`ServiceEndpoint`].OutputValue' \
  --output text \
  --region us-east-1)

echo "New API URL: $API_URL"
echo "Update your test suite with this URL"