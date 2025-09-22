#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/config.sh"

FILE="${1:-../test-comprehensive.txt}"
TMP="/tmp/doc_test_$(date +%s)"
mkdir -p "$TMP"

echo "=== E2E TEST: $FILE ==="

echo "1) Request presigned URL"
resp=$(curl -s -X POST "$API_BASE/upload" -H "Content-Type: application/json" -d "{\"filename\":\"$(basename $FILE)\",\"contentType\":\"text/plain\"}")
uploadUrl=$(echo "$resp" | jq -r '.uploadUrl')
objectKey=$(echo "$resp" | jq -r '.key')
docId=$(echo "$resp" | jq -r '.docId')

echo "DocId: $docId"

echo "2) Upload file..."
curl -sS -X PUT -H "Content-Type: text/plain" --upload-file "$FILE" "$uploadUrl" -o /dev/null

echo "3) Wait for processing (derived files)..."
derived_txt="derived/${docId}.txt"
derived_index="derived/${docId}.index.json"

# Wait for derived text
for i in {1..60}; do
  if aws s3api head-object --bucket "$S3_BUCKET" --key "$derived_txt" --region "$AWS_REGION" 2>/dev/null; then
    echo "✓ Derived text exists"
    break
  fi
  echo "Waiting for derived text... ($i/60)"
  sleep 3
done

# Wait for index
for i in {1..60}; do
  if aws s3api head-object --bucket "$S3_BUCKET" --key "$derived_index" --region "$AWS_REGION" 2>/dev/null; then
    echo "✓ Derived index exists"
    break
  fi
  echo "Waiting for derived index... ($i/60)"
  sleep 3
done

echo "4) Check status polling..."
status_resp=$(curl -s "$API_BASE/status?docId=$docId")
echo "$status_resp" | jq .
phase=$(echo "$status_resp" | jq -r '.phase // empty')

if [[ "$phase" != "ready" ]]; then
  echo "FAIL: Document not ready, phase=$phase"
  exit 10
fi

echo "5) Test RAG chat..."
question="What does this document test?"
chat_resp=$(curl -s -X POST "$API_BASE/rag-chat" -H "Content-Type: application/json" -d "{\"question\":\"$question\",\"docId\":\"$docId\"}")
echo "$chat_resp" | jq .

answer=$(echo "$chat_resp" | jq -r '.answer // empty')
hasContext=$(echo "$chat_resp" | jq -r '.hasContext // false')

if [[ -z "$answer" ]]; then
  echo "FAIL: Chat returned empty answer"
  exit 11
fi

if [[ "$hasContext" != "true" ]]; then
  echo "FAIL: Chat should have context for uploaded document"
  exit 12
fi

echo "6) Verify DynamoDB status..."
db_resp=$(aws dynamodb get-item --table-name "$UPLOAD_TABLE" --key "{\"docId\":{\"S\":\"$docId\"}}" --region "$AWS_REGION")
status=$(echo "$db_resp" | jq -r '.Item.status.S // empty')

if [[ "$status" != "s1.ckpt-08.chat" ]]; then
  echo "FAIL: Expected status s1.ckpt-08.chat, got $status"
  exit 13
fi

echo "✅ E2E TEST PASSED - Full pipeline working!"
echo "DocId: $docId (cleanup manually if needed)"

# Save docId for component tests
echo "$docId" > /tmp/last_docid.txt