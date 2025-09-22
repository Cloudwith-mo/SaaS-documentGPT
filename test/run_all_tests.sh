#!/usr/bin/env bash
set -uo pipefail

TEST_DIR="$(dirname "$0")"
cd "$TEST_DIR"

echo "🧪 DOCUMENTGPT BATTLE-HARDENED TEST SUITE"
echo "=========================================="

# Make all scripts executable
chmod +x *.sh

# Track test results
PASSED=0
FAILED=0
FAILED_TESTS=()

run_test() {
  local test_name="$1"
  local test_script="$2"
  shift 2
  
  echo ""
  echo "🔬 Running: $test_name"
  echo "---"
  
  if $test_script "$@" 2>&1; then
    echo "✅ PASSED: $test_name"
    ((PASSED++))
  else
    echo "❌ FAILED: $test_name"
    ((FAILED++))
    FAILED_TESTS+=("$test_name")
  fi
}

# Create test file
echo "DocumentGPT Test File - Microsoft was founded in 1975 by Bill Gates and Paul Allen in Redmond, Washington." > ../test_files/test.txt

echo "Starting test suite..."

# 1. Smoke tests
run_test "Smoke Upload Test" "./smoke_upload_test.sh"

# 2. Negative tests
run_test "Negative Tests" "./negative_test.sh"

# 3. End-to-end test (most comprehensive)
run_test "End-to-End Pipeline Test" "./end_to_end_test.sh" "../test_files/test.txt"

# Get docId from last E2E test for component tests
if [[ -f "/tmp/last_docid.txt" ]]; then
  LAST_DOCID=$(cat /tmp/last_docid.txt)
  
  # 4. Component tests using the uploaded document
  run_test "Indexer Validation" "./indexer_test.sh" "$LAST_DOCID"
  run_test "Chat Functionality" "./chat_test.sh" "$LAST_DOCID" "Who founded Microsoft?"
fi

# Summary
echo ""
echo "🏁 TEST SUITE COMPLETE"
echo "======================"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"

if [[ $FAILED -gt 0 ]]; then
  echo ""
  echo "Failed tests:"
  for test in "${FAILED_TESTS[@]}"; do
    echo "  - $test"
  done
  echo ""
  echo "🚨 PIPELINE NOT READY FOR PRODUCTION"
  exit 1
else
  echo ""
  echo "🎉 ALL TESTS PASSED - PIPELINE IS BATTLE-HARDENED!"
  exit 0
fi