#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/config.sh"

docId="${1:?Provide docId to test indexer}"

echo "=== INDEXER TEST: $docId ==="

# Check for index file
derived_index_key="derived/${docId}.index.json"
echo "Checking for $derived_index_key..."

if ! aws s3api head-object --bucket "$S3_BUCKET" --key "$derived_index_key" --region "$AWS_REGION" >/dev/null 2>&1; then
  echo "❌ Index file not found"
  exit 1
fi

# Download and validate index
aws s3api get-object --bucket "$S3_BUCKET" --key "$derived_index_key" "/tmp/index_${docId}.json" --region "$AWS_REGION"

# Validate structure
if ! jq empty "/tmp/index_${docId}.json" 2>/dev/null; then
  echo "❌ Invalid JSON in index file"
  exit 2
fi

chunk_count=$(jq '.chunks | length' "/tmp/index_${docId}.json")
echo "Chunks: $chunk_count"

if [[ "$chunk_count" -eq 0 ]]; then
  echo "❌ No chunks in index"
  exit 3
fi

# Check embedding dimensions
sample_emb_len=$(jq '.chunks[0].embedding | length' "/tmp/index_${docId}.json")
echo "Embedding dimension: $sample_emb_len"

if [[ "$sample_emb_len" -lt 1000 ]]; then
  echo "❌ Embedding dimension too small: $sample_emb_len"
  exit 4
fi

echo "✅ INDEXER TEST PASSED"