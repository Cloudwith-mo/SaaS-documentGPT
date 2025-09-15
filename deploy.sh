#!/bin/bash

echo "🚀 Deploying DocumentGPT API to AWS..."

# Check if serverless is installed
if ! command -v serverless &> /dev/null; then
    echo "Installing Serverless Framework..."
    npm install -g serverless
fi

# Install serverless plugins
echo "Installing plugins..."
npm install serverless-python-requirements

# Deploy to AWS
echo "Deploying to AWS..."
serverless deploy --stage prod

echo "✅ Deployment complete!"
echo "API endpoints will be available at:"
echo "https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/api/agents"
echo "https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/api/pdf/search"
echo "https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/api/v5/health"