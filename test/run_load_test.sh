#!/bin/bash

# Load test configuration for DocumentGPT
source ./config.sh

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
    echo "❌ k6 not found. Install from: https://k6.io/docs/getting-started/installation"
    exit 1
fi

# Get existing document IDs from our test data
echo "🔍 Finding processed documents for load testing..."

# Use the document we know exists from previous tests
DOC_IDS='["real-test-doc"]'

# If you have multiple docs, add them here:
# DOC_IDS='["real-test-doc","another-doc-id","third-doc-id"]'

echo "📊 Starting DocumentGPT Chat Load Test"
echo "   API: $API_BASE"
echo "   Docs: $DOC_IDS"
echo "   RPS: ${RPS:-20}"
echo "   Duration: ${DURATION:-5m}"

# Run the load test
API_BASE="$API_BASE" \
AUTH_TYPE="none" \
DOC_IDS="$DOC_IDS" \
RPS="${RPS:-20}" \
DURATION="${DURATION:-5m}" \
RAMP_DURATION="${RAMP_DURATION:-30s}" \
MAX_VUS="${MAX_VUS:-100}" \
PREALLOC_VUS="${PREALLOC_VUS:-25}" \
k6 run chat_load_test.js

echo "✅ Load test completed. Check results above for performance metrics."