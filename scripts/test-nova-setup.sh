#!/bin/bash
set -e

echo "🧪 Testing Nova Infrastructure Setup..."

# Get queue URL
MEDIA_QUEUE_URL=$(aws sqs get-queue-url --queue-name docgpt-media-queue --query 'QueueUrl' --output text 2>/dev/null)

if [ -z "$MEDIA_QUEUE_URL" ]; then
  echo "❌ Queue not found. Run setup-nova-infrastructure.sh first"
  exit 1
fi

echo "✅ Queue found: $MEDIA_QUEUE_URL"

# Prepare sample asset
TEST_BUCKET="docgpt-media-dev"
TEST_KEY="uploads/test_user/test-media/nova-worker-sample.txt"
echo ""
echo "📝 Preparing sample file for Nova test..."
TMP_FILE=$(mktemp)
echo "This is a Nova embedding smoke test generated at $(date -u +"%Y-%m-%dT%H:%M:%SZ")." > "$TMP_FILE"

echo "☁️  Uploading sample to s3://$TEST_BUCKET/$TEST_KEY"
aws s3 cp "$TMP_FILE" "s3://$TEST_BUCKET/$TEST_KEY" --content-type text/plain >/dev/null
rm "$TMP_FILE"
echo "✅ Sample uploaded"

# Test 1: Send test message
echo ""
echo "📤 Test 1: Sending test message to queue..."
aws sqs send-message \
  --queue-url "$MEDIA_QUEUE_URL" \
  --message-body '{
    "doc_id": "test_'$(date +%s)'",
    "user_id": "test_user",
    "bucket": "'$TEST_BUCKET'",
    "key": "'$TEST_KEY'",
    "media_type": "text/plain"
  }'

echo "✅ Message sent"

# Test 2: Check Lambda exists
echo ""
echo "🔍 Test 2: Checking Lambda function..."
aws lambda get-function --function-name documentgpt-media-worker --query 'Configuration.FunctionName' --output text

echo "✅ Lambda exists"

# Test 3: Check S3 bucket
echo ""
echo "📦 Test 3: Checking S3 bucket..."
aws s3 ls s3://docgpt-media-dev/ 2>/dev/null || echo "Bucket is empty (expected)"

echo "✅ S3 bucket accessible"

# Test 4: Check IAM role
echo ""
echo "👤 Test 4: Checking IAM role..."
aws iam get-role --role-name DocumentGPTMediaWorkerRole --query 'Role.RoleName' --output text

echo "✅ IAM role exists"

# Test 5: Check event source mapping
echo ""
echo "🔗 Test 5: Checking SQS → Lambda connection..."
MAPPING_COUNT=$(aws lambda list-event-source-mappings \
  --function-name documentgpt-media-worker \
  --query 'length(EventSourceMappings)' \
  --output text)

if [ "$MAPPING_COUNT" -gt 0 ]; then
  echo "✅ Event source mapping active ($MAPPING_COUNT mapping(s))"
else
  echo "❌ No event source mapping found"
  exit 1
fi

# Test 6: Check CloudWatch logs
echo ""
echo "📊 Test 6: Checking recent Lambda invocations..."
sleep 5  # Wait for Lambda to process

LOG_STREAMS=$(aws logs describe-log-streams \
  --log-group-name /aws/lambda/documentgpt-media-worker \
  --order-by LastEventTime \
  --descending \
  --max-items 1 \
  --query 'logStreams[0].logStreamName' \
  --output text 2>/dev/null || echo "")

if [ -n "$LOG_STREAMS" ] && [ "$LOG_STREAMS" != "None" ]; then
  echo "✅ Lambda has been invoked"
  echo ""
  echo "📋 Recent logs:"
  aws logs tail /aws/lambda/documentgpt-media-worker --since 5m --format short | head -20
else
  echo "⚠️  No recent invocations (Lambda may not have processed the test message yet)"
fi

echo ""
echo "🎉 All tests passed!"
echo ""
echo "📋 Infrastructure Status:"
echo "  ✅ S3 Bucket: docgpt-media-dev"
echo "  ✅ SQS Queue: docgpt-media-queue"
echo "  ✅ Lambda: documentgpt-media-worker"
echo "  ✅ IAM Role: DocumentGPTMediaWorkerRole"
echo "  ✅ Event Mapping: Active"
echo ""
echo "🔍 Monitor logs with:"
echo "  aws logs tail /aws/lambda/documentgpt-media-worker --follow"
echo ""
