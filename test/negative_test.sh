#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/config.sh"

echo "=== NEGATIVE TESTS ==="

# Test 1: Invalid upload request
echo "1) Testing invalid upload request..."
resp=$(curl -s -X POST "$API_BASE/upload" -H "Content-Type: application/json" -d '{"invalid":"data"}')
error=$(echo "$resp" | jq -r '.error // empty')
if [[ -z "$error" ]]; then
  echo "❌ Should return error for invalid request"
  exit 1
fi
echo "✓ Invalid request properly rejected: $error"

# Test 2: Non-existent document status
echo "2) Testing non-existent document status..."
resp=$(curl -s "$API_BASE/status?docId=nonexistent")
error=$(echo "$resp" | jq -r '.error // empty')
if [[ -z "$error" ]]; then
  echo "❌ Should return error for non-existent document"
  exit 2
fi
echo "✓ Non-existent document properly handled: $error"

# Test 3: Chat without docId
echo "3) Testing chat without docId..."
resp=$(curl -s -X POST "$API_BASE/rag-chat" -H "Content-Type: application/json" -d '{"question":"test"}')
hasContext=$(echo "$resp" | jq -r '.hasContext')
if [[ "$hasContext" != "false" ]]; then
  echo "❌ Should return hasContext=false without docId, got: $hasContext"
  echo "Full response: $resp"
  exit 3
fi
echo "✓ Chat without docId handled correctly"

# Test 4: Malicious input handling
echo "4) Testing XSS input..."
resp=$(curl -s -X POST "$API_BASE/rag-chat" -H "Content-Type: application/json" -d '{"question":"<script>alert(\"xss\")</script>","docId":"test"}')
answer=$(echo "$resp" | jq -r '.answer // empty')
if [[ "$answer" == *"<script>"* ]]; then
  echo "❌ XSS input not properly handled"
  exit 4
fi
echo "✓ Malicious input safely handled"

echo "✅ ALL NEGATIVE TESTS PASSED"