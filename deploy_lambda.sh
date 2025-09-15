#!/bin/bash
# Deploy DocumentsGPT v5 to AWS Lambda

echo "🚀 Deploying DocumentsGPT v5 Light Theme to Lambda..."

# Create deployment package
zip -r documentgpt-v5.zip lambda_handler.py

# Update Lambda function
aws lambda update-function-code \
    --function-name documentgpt \
    --zip-file fileb://documentgpt-v5.zip

echo "✅ Lambda updated! Light theme now live at https://documentgpt.io/"

# Clean up
rm documentgpt-v5.zip