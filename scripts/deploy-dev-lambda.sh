#!/bin/bash
# Deploy Dev Lambda with RAG capabilities

set -e

echo "🚀 Deploying Dev Lambda Handler..."

cd lambda

# Create deployment package
echo "📦 Creating deployment package..."
rm -f dev-deployment.zip
zip -r dev-deployment.zip dev_handler.py

# Add existing dependencies (reuse from main lambda)
if [ -d "boto3" ]; then
    zip -r dev-deployment.zip boto3/ botocore/ urllib3/ PyPDF2/ -q
fi

# Upload to Lambda
echo "⬆️  Uploading to AWS Lambda..."
aws lambda update-function-code \
    --function-name documentgpt-dev \
    --zip-file fileb://dev-deployment.zip \
    --region us-east-1

echo "⏳ Waiting for Lambda to update..."
aws lambda wait function-updated \
    --function-name documentgpt-dev \
    --region us-east-1

echo "✅ Dev Lambda deployed successfully!"
echo ""
echo "🔧 Next steps:"
echo "1. Set PINECONE_API_KEY environment variable in Lambda console"
echo "2. Set PINECONE_INDEX_NAME=documentgpt-dev"
echo "3. Test with: curl https://YOUR_DEV_API/dev/health"
