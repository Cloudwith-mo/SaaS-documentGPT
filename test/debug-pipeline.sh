#!/bin/bash

echo "🔍 Debug Pipeline: Upload + Monitor Logs"
source ./config.sh

# Create test file
echo "Debug test document for pipeline verification. Microsoft Azure provides cloud computing services." > "$TMPDIR/debug-pipeline.txt"

# Upload document
echo "📤 Uploading test document..."
UPLOAD_RESP=$(curl -s -X POST "$API_BASE/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: debug-pipeline-user" \
  -d '{"filename":"debug-pipeline.txt","fileType":"txt"}')

DOC_ID=$(echo "$UPLOAD_RESP" | jq -r '.docId')
UPLOAD_URL=$(echo "$UPLOAD_RESP" | jq -r '.uploadUrl')

echo "DocId: $DOC_ID"
echo "Upload URL: $UPLOAD_URL"

# Upload file to S3
echo "📤 Uploading to S3..."
curl -s -X PUT "$UPLOAD_URL" --data-binary "@$TMPDIR/debug-pipeline.txt"
echo "✅ File uploaded to S3"

# Wait and check logs
echo "⏳ Waiting 10 seconds for S3 trigger..."
sleep 10

# Check recent CloudWatch logs
echo "📋 Checking CloudWatch logs..."
LOG_STREAM=$(aws logs describe-log-streams \
  --log-group-name "/aws/lambda/documentgpt-s3-trigger" \
  --order-by LastEventTime --descending --max-items 1 \
  --query 'logStreams[0].logStreamName' --output text)

echo "Latest log stream: $LOG_STREAM"

# Get recent log events
aws logs get-log-events \
  --log-group-name "/aws/lambda/documentgpt-s3-trigger" \
  --log-stream-name "$LOG_STREAM" \
  --start-time $(($(date +%s) - 300))000 \
  --query 'events[*].message' --output text | tail -20

# Check Step Functions executions
echo "📋 Checking Step Functions executions..."
aws stepfunctions list-executions \
  --state-machine-arn "arn:aws:states:us-east-1:995805900737:stateMachine:documentgpt-processing" \
  --max-items 3 \
  --query 'executions[*].[name,status,startDate]' --output table

# Check document status
echo "📋 Checking document status..."
STATUS_RESP=$(curl -s -X GET "$API_BASE/status?docId=$DOC_ID" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: debug-pipeline-user")
echo "Status: $STATUS_RESP"