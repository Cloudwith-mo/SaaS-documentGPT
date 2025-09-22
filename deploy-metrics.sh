#!/bin/bash

echo "🚀 Deploying DocumentGPT Lambda functions with observability metrics..."

# Create deployment packages
cd lambda

# Package metrics helper
echo "📦 Packaging metrics helper..."
zip -r metrics-helper.zip metrics-helper.js

# Package parser with metrics
echo "📦 Packaging parser with metrics..."
zip -r parser-with-metrics.zip parser.js metrics-helper.js

# Package indexer with metrics  
echo "📦 Packaging indexer with metrics..."
zip -r indexer-with-metrics.zip indexer.js metrics-helper.js

# Package chat with metrics
echo "📦 Packaging chat with metrics..."
zip -r chat-with-metrics.zip rag-chat-v2.js metrics-helper.js

# Deploy Lambda functions
echo "🔄 Updating Lambda functions..."

aws lambda update-function-code \
    --function-name documentgpt-parser \
    --zip-file fileb://parser-with-metrics.zip \
    --region us-east-1

aws lambda update-function-code \
    --function-name documentgpt-indexer \
    --zip-file fileb://indexer-with-metrics.zip \
    --region us-east-1

aws lambda update-function-code \
    --function-name documentgpt-rag-chat \
    --zip-file fileb://chat-with-metrics.zip \
    --region us-east-1

# Add CloudWatch permissions to Lambda execution roles
echo "🔐 Adding CloudWatch permissions..."

aws iam attach-role-policy \
    --role-name documentgpt-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy \
    --region us-east-1 2>/dev/null || echo "Policy already attached or role not found"

# Clean up
rm -f *.zip

echo "✅ Deployment complete! Check CloudWatch Dashboard: DocumentGPT-Dashboard"
echo "📊 Dashboard URL: https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=DocumentGPT-Dashboard"