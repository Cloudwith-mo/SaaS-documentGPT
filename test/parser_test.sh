#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/config.sh"

FILE="${1:?Provide test file path}"

echo "=== PARSER TEST: $FILE ==="

# 1. Upload file
resp=$(curl -s -X POST "$API_BASE/upload" -H "Content-Type: application/json" -d "{\"filename\":\"$(basename $FILE)\",\"contentType\":\"text/plain\"}")
uploadUrl=$(echo "$resp" | jq -r '.uploadUrl')
objectKey=$(echo "$resp" | jq -r '.key')
docId=$(echo "$resp" | jq -r '.docId')

curl -sS -X PUT -H "Content-Type: text/plain" --upload-file "$FILE" "$uploadUrl"
echo "Uploaded: $docId"

# 2. Wait for parsing (derived text)
derived_key="derived/${docId}.txt"
echo "Waiting for $derived_key..."

for i in {1..60}; do
  if aws s3api head-object --bucket "$S3_BUCKET" --key "$derived_key" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "✓ Derived file exists"
    aws s3api get-object --bucket "$S3_BUCKET" --key "$derived_key" "/tmp/derived_${docId}.txt" --region "$AWS_REGION"
    echo "Preview:"
    head -n 10 "/tmp/derived_${docId}.txt"
    break
  fi
  echo "Waiting... ($i/60)"
  sleep 3
done

# 3. Check DynamoDB status
db_resp=$(aws dynamodb get-item --table-name "$UPLOAD_TABLE" --key "{\"docId\":{\"S\":\"$docId\"}}" --region "$AWS_REGION")
status=$(echo "$db_resp" | jq -r '.Item.status.S // empty')
echo "Status: $status"

if [[ "$status" == "s1.ckpt-07.parsing" || "$status" == "s1.ckpt-08.chat" ]]; then
  echo "✅ PARSER TEST PASSED"
else
  echo "❌ PARSER TEST FAILED - Status: $status"
  exit 1
fi