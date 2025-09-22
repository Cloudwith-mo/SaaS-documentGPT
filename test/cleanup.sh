#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/config.sh"

docId="${1:?Provide docId to cleanup}"

echo "=== CLEANUP: $docId ==="

# Remove S3 objects
echo "Removing S3 objects..."
aws s3 rm "s3://$S3_BUCKET/derived/${docId}.txt" 2>/dev/null || true
aws s3 rm "s3://$S3_BUCKET/derived/${docId}.index.json" 2>/dev/null || true

# Find and remove original object
objectKey=$(aws dynamodb get-item --table-name "$UPLOAD_TABLE" --key "{\"docId\":{\"S\":\"$docId\"}}" --region "$AWS_REGION" --query 'Item.filename.S' --output text 2>/dev/null || echo "")
if [[ -n "$objectKey" && "$objectKey" != "None" ]]; then
  aws s3 rm "s3://$S3_BUCKET/${docId}/${objectKey}" 2>/dev/null || true
fi

# Remove DynamoDB record
echo "Removing DynamoDB record..."
aws dynamodb delete-item --table-name "$UPLOAD_TABLE" --key "{\"docId\":{\"S\":\"$docId\"}}" --region "$AWS_REGION" 2>/dev/null || true

echo "✓ Cleanup completed for $docId"