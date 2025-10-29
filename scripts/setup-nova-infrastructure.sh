#!/bin/bash
set -e

echo "🚀 Setting up Nova Multimodal Infrastructure..."

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account: $ACCOUNT_ID"

# 1. Create S3 bucket
echo ""
echo "📦 Step 1: Creating S3 bucket..."
aws s3api create-bucket \
  --bucket docgpt-media-dev \
  --region us-east-1 || echo "Bucket already exists"

# Enable encryption
echo "🔒 Enabling encryption..."
aws s3api put-bucket-encryption \
  --bucket docgpt-media-dev \
  --server-side-encryption-configuration '{
    "Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]
  }'

# Enable versioning
echo "📚 Enabling versioning..."
aws s3api put-bucket-versioning \
  --bucket docgpt-media-dev \
  --versioning-configuration Status=Enabled

echo "✅ S3 bucket configured"

# 2. Create SQS queue
echo ""
echo "📬 Step 2: Creating SQS queue..."
MEDIA_QUEUE_URL=$(aws sqs create-queue \
  --queue-name docgpt-media-queue \
  --query 'QueueUrl' \
  --output text 2>/dev/null || aws sqs get-queue-url --queue-name docgpt-media-queue --query 'QueueUrl' --output text)

echo "Queue URL: $MEDIA_QUEUE_URL"

MEDIA_QUEUE_ARN=$(aws sqs get-queue-attributes \
  --queue-url "$MEDIA_QUEUE_URL" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)

echo "Queue ARN: $MEDIA_QUEUE_ARN"
echo "⏱️  Setting queue visibility timeout..."
aws sqs set-queue-attributes \
  --queue-url "$MEDIA_QUEUE_URL" \
  --attributes VisibilityTimeout=910
echo "✅ SQS queue configured"

# 3. Create IAM role
echo ""
echo "👤 Step 3: Creating IAM role..."

# Create trust policy
cat > /tmp/lambda-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create role
aws iam create-role \
  --role-name DocumentGPTMediaWorkerRole \
  --assume-role-policy-document file:///tmp/lambda-trust.json 2>/dev/null || echo "Role already exists"

# Attach basic execution policy
aws iam attach-role-policy \
  --role-name DocumentGPTMediaWorkerRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create inline policy
cat > /tmp/policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject","s3:PutObject"],
      "Resource": ["arn:aws:s3:::docgpt-media-dev/*"]
    },
    {
      "Effect": "Allow",
      "Action": ["sqs:ReceiveMessage","sqs:DeleteMessage","sqs:GetQueueAttributes"],
      "Resource": ["$MEDIA_QUEUE_ARN"]
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem","dynamodb:UpdateItem","dynamodb:PutItem"],
      "Resource": ["arn:aws:dynamodb:us-east-1:$ACCOUNT_ID:table/docgpt"]
    },
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],
      "Resource": ["arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-*"]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name DocumentGPTMediaWorkerRole \
  --policy-name DocumentGPTMediaWorkerPolicy \
  --policy-document file:///tmp/policy.json

echo "✅ IAM role configured"

# Wait for role to propagate
echo "⏳ Waiting for IAM role to propagate..."
sleep 10

# 4. Package and deploy Lambda
echo ""
echo "📦 Step 4: Packaging Lambda function..."
cd "$(dirname "$0")/../lambda"

# Create package directory
rm -rf package media_worker.zip
mkdir -p package

# Install dependencies (prefer minimal worker requirements if present)
echo "📥 Installing dependencies..."
REQ_FILE="media_worker_requirements.txt"
if [ -f "$REQ_FILE" ]; then
  pip3 install --no-cache-dir -r "$REQ_FILE" --target package --quiet
else
  pip3 install --no-cache-dir -r requirements.txt --target package --quiet
fi

# Copy worker code and shared modules
cp media_worker.py package/ 2>/dev/null || echo "⚠️  media_worker.py not found - will create placeholder"
cp config.py package/ 2>/dev/null || true
if [ -d embeddings ]; then
  cp -R embeddings package/
fi

# Create placeholder if doesn't exist
if [ ! -f package/media_worker.py ]; then
  cat > package/media_worker.py <<'PYEOF'
import json
import os
import boto3
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('DOC_TABLE', 'docgpt'))

def lambda_handler(event, context):
    """Process media files from SQS queue."""
    print(f"Received {len(event.get('Records', []))} messages")
    
    for record in event.get('Records', []):
        try:
            body = json.loads(record['body'])
            doc_id = body.get('doc_id')
            user_id = body.get('user_id')
            s3_key = body.get('s3_key')
            media_type = body.get('media_type')
            
            print(f"Processing: doc={doc_id} type={media_type} key={s3_key}")
            
            # Update status to processing
            table.update_item(
                Key={'pk': f'USER#{user_id}', 'sk': f'DOC#{doc_id}'},
                UpdateExpression='SET processing_status = :status, updated_at = :time',
                ExpressionAttributeValues={
                    ':status': 'processing',
                    ':time': datetime.utcnow().isoformat()
                }
            )
            
            # TODO: Add Nova embedding logic here
            # For now, just mark as ready
            table.update_item(
                Key={'pk': f'USER#{user_id}', 'sk': f'DOC#{doc_id}'},
                UpdateExpression='SET processing_status = :status, updated_at = :time',
                ExpressionAttributeValues={
                    ':status': 'ready',
                    ':time': datetime.utcnow().isoformat()
                }
            )
            
            print(f"✅ Processed {doc_id}")
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            raise
    
    return {'statusCode': 200, 'body': json.dumps('Processed')}
PYEOF
fi

# Create zip
cd package
zip -r ../media_worker.zip . -q
cd ..

echo "✅ Lambda package created"

# 5. Create/Update Lambda function
echo ""
echo "🚀 Step 5: Deploying Lambda function..."

# Check if function exists
if aws lambda get-function --function-name documentgpt-media-worker 2>/dev/null; then
  echo "Updating existing function..."
  aws lambda update-function-code \
    --function-name documentgpt-media-worker \
    --zip-file fileb://media_worker.zip
else
  echo "Creating new function..."
  aws lambda create-function \
    --function-name documentgpt-media-worker \
    --runtime python3.11 \
    --role arn:aws:iam::$ACCOUNT_ID:role/DocumentGPTMediaWorkerRole \
    --handler media_worker.lambda_handler \
    --timeout 900 \
    --memory-size 1024 \
    --zip-file fileb://media_worker.zip
fi

# Wait for function to be ready
echo "⏳ Waiting for Lambda to be ready..."
aws lambda wait function-updated --function-name documentgpt-media-worker

# 6. Set environment variables
echo ""
echo "⚙️  Step 6: Configuring environment variables..."

# Get Pinecone config from existing Lambda
PINECONE_KEY=$(aws lambda get-function-configuration \
  --function-name documentgpt-dev-node \
  --query 'Environment.Variables.PINECONE_API_KEY' \
  --output text 2>/dev/null || echo "")

PINECONE_HOST=$(aws lambda get-function-configuration \
  --function-name documentgpt-dev-node \
  --query 'Environment.Variables.PINECONE_INDEX_HOST' \
  --output text 2>/dev/null || echo "")

aws lambda update-function-configuration \
  --function-name documentgpt-media-worker \
  --environment "Variables={
    DOC_TABLE=docgpt,
    PINECONE_API_KEY=$PINECONE_KEY,
    PINECONE_INDEX_HOST=$PINECONE_HOST,
    PINECONE_INDEX=documentgpt-dev,
    BEDROCK_REGION=us-east-1,
    NOVA_EMBEDDING_MODEL=amazon.nova-2-multimodal-embeddings-v1:0,
    MEDIA_BUCKET=docgpt-media-dev,
    MEDIA_QUEUE_URL=$MEDIA_QUEUE_URL
  }"

echo "✅ Environment variables configured"

# 7. Connect SQS to Lambda
echo ""
echo "🔗 Step 7: Connecting SQS to Lambda..."

# Check if mapping exists
EXISTING_MAPPING=$(aws lambda list-event-source-mappings \
  --function-name documentgpt-media-worker \
  --query "EventSourceMappings[?EventSourceArn=='$MEDIA_QUEUE_ARN'].UUID" \
  --output text)

if [ -z "$EXISTING_MAPPING" ]; then
  aws lambda create-event-source-mapping \
    --function-name documentgpt-media-worker \
    --event-source-arn "$MEDIA_QUEUE_ARN" \
    --batch-size 1
  echo "✅ Event source mapping created"
else
  echo "✅ Event source mapping already exists"
fi

# Cleanup
rm -rf package media_worker.zip /tmp/lambda-trust.json /tmp/policy.json

echo ""
echo "🎉 Infrastructure setup complete!"
echo ""
echo "📋 Summary:"
echo "  S3 Bucket: docgpt-media-dev"
echo "  SQS Queue: $MEDIA_QUEUE_URL"
echo "  Lambda: documentgpt-media-worker"
echo "  IAM Role: DocumentGPTMediaWorkerRole"
echo ""
echo "🔍 Next steps:"
echo "  1. Test with: aws sqs send-message --queue-url $MEDIA_QUEUE_URL --message-body '{\"doc_id\":\"test\",\"user_id\":\"test\",\"s3_key\":\"test.jpg\",\"media_type\":\"image\"}'"
echo "  2. Check logs: aws logs tail /aws/lambda/documentgpt-media-worker --follow"
echo "  3. Update GitHub secrets with MEDIA_QUEUE_URL"
echo ""
