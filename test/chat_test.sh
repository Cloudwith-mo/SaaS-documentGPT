#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/config.sh"

docId="${1:?Provide docId to test chat}"
question="${2:-What is this document about?}"

echo "=== CHAT TEST: $docId ==="
echo "Question: $question"

# Test chat endpoint
resp=$(curl -s -X POST "$API_BASE/rag-chat" -H "Content-Type: application/json" -d "{\"question\":\"$question\",\"docId\":\"$docId\"}")
echo "$resp" | jq .

# Validate response
answer=$(echo "$resp" | jq -r '.answer // empty')
hasContext=$(echo "$resp" | jq -r '.hasContext // false')

if [[ -z "$answer" ]]; then
  echo "❌ Empty answer"
  exit 1
fi

if [[ "$hasContext" != "true" ]]; then
  echo "❌ No context used (expected for uploaded document)"
  exit 2
fi

echo "Answer: $answer"
echo "✅ CHAT TEST PASSED"