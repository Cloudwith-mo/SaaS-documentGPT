#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/config.sh"

echo "1) Request presigned upload URL..."
resp=$(curl -sS -X POST "$API_BASE/upload" -H "Content-Type: application/json" -d '{"filename":"smoke-test.txt","contentType":"text/plain"}')
echo "$resp" | jq .

uploadUrl=$(echo "$resp" | jq -r '.uploadUrl // empty')
objectKey=$(echo "$resp" | jq -r '.key // empty')
docId=$(echo "$resp" | jq -r '.docId // empty')

if [[ -z "$uploadUrl" || -z "$objectKey" ]]; then
  echo "FAILED: presign response missing uploadUrl/objectKey"
  exit 2
fi

echo "Got presigned URL, will PUT a tiny file..."
curl -sS -X PUT -H "Content-Type:text/plain" --data-binary "hello smoke test" "$uploadUrl" -w "\nHTTP_CODE:%{http_code}\n"

# Check S3 object exists
echo "Checking S3 object existence..."
aws s3api head-object --bucket "$S3_BUCKET" --key "$objectKey" --region "$AWS_REGION" >/dev/null
echo "S3 object exists."

# Check DynamoDB record
if [[ -n "$docId" ]]; then
  echo "Checking DynamoDB record for docId=$docId..."
  aws dynamodb get-item --table-name "$UPLOAD_TABLE" --key "{\"docId\":{\"S\":\"$docId\"}}" --region "$AWS_REGION" | jq .
fi

echo "SMOKE test passed."