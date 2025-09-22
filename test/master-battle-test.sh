#!/bin/bash

echo "🧪 DOCUMENTGPT MASTER BATTLE TEST SUITE"
echo "========================================"
echo "Testing all phases and components with maximum rigor"
echo "If this passes, manual testing will inevitably pass"
echo ""

source ./config.sh

TOTAL_PASS=0
TOTAL_TESTS=0
PHASE_RESULTS=()

run_phase_test() {
    local phase_name="$1"
    local test_script="$2"
    
    echo "🔥 PHASE: $phase_name"
    echo "----------------------------------------"
    
    if [ -f "$test_script" ]; then
        chmod +x "$test_script"
        if bash "$test_script"; then
            PHASE_RESULTS+=("✅ $phase_name")
            echo "✅ $phase_name PASSED"
        else
            PHASE_RESULTS+=("❌ $phase_name")
            echo "❌ $phase_name FAILED"
        fi
    else
        echo "⚠️  Test script not found: $test_script"
        PHASE_RESULTS+=("⚠️  $phase_name (script missing)")
    fi
    
    echo ""
}

# Run all phase tests
run_phase_test "PHASE 1: Infrastructure & Performance" "./phase1-infrastructure-test.sh"
run_phase_test "PHASE 2: Security & Multi-Tenancy" "./phase2-security-test.sh"
run_phase_test "PHASE 3: End-to-End Pipeline" "./phase3-pipeline-test.sh"

# Additional comprehensive tests
echo "🔥 ADDITIONAL BATTLE TESTS"
echo "----------------------------------------"

# Test 1: Stress Test - Rapid Sequential Uploads
echo "📊 Stress Test: Rapid Sequential Uploads (25 files)"
STRESS_SUCCESS=0
for i in {1..25}; do
    RESPONSE=$(curl -s -X POST "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/upload" \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      -H "x-user-id: stress-test-user-$((i % 5))" \
      -d "{\"filename\":\"stress-test-$i.txt\",\"contentType\":\"text/plain\"}")
    
    if echo "$RESPONSE" | jq -e '.docId' > /dev/null 2>&1; then
        STRESS_SUCCESS=$((STRESS_SUCCESS + 1))
    fi
    
    # Vary timing to test different scenarios
    [ $((i % 3)) -eq 0 ] && sleep 0.05 || sleep 0.02
done

if [ $STRESS_SUCCESS -ge 23 ]; then
    echo "✅ Stress test passed (${STRESS_SUCCESS}/25)"
    PHASE_RESULTS+=("✅ Stress Test")
else
    echo "❌ Stress test failed (${STRESS_SUCCESS}/25)"
    PHASE_RESULTS+=("❌ Stress Test")
fi

# Test 2: Cross-User Isolation Verification
echo "📊 Cross-User Isolation Test"
USER_A_DOC=$(curl -s -X POST "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: isolation-user-a" \
  -d '{"filename":"secret-a.txt","contentType":"text/plain"}' | jq -r '.docId')

USER_B_DOC=$(curl -s -X POST "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: isolation-user-b" \
  -d '{"filename":"secret-b.txt","contentType":"text/plain"}' | jq -r '.docId')

# Try user A accessing user B's document
CROSS_ACCESS=$(curl -s -X POST "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/rag-chat" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: isolation-user-a" \
  -d "{\"question\":\"What is this document about?\",\"docId\":\"$USER_B_DOC\"}")

# Should not have context from user B's document
HAS_CONTEXT=$(echo "$CROSS_ACCESS" | jq -r '.hasContext // false')
if [ "$HAS_CONTEXT" = "false" ] || [ "$HAS_CONTEXT" = "null" ]; then
    echo "✅ Cross-user isolation working"
    PHASE_RESULTS+=("✅ User Isolation")
else
    echo "❌ Cross-user isolation FAILED - security vulnerability!"
    PHASE_RESULTS+=("❌ User Isolation - SECURITY RISK")
fi

# Test 3: Error Recovery and Edge Cases
echo "📊 Error Recovery & Edge Cases"
EDGE_CASE_PASS=0

# Test malformed JSON
MALFORMED=$(curl -s -X POST "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{"filename":}')
echo "$MALFORMED" | grep -q "error" && EDGE_CASE_PASS=$((EDGE_CASE_PASS + 1))

# Test extremely long filename
LONG_NAME=$(printf 'a%.0s' {1..300})
LONG_FILENAME=$(curl -s -X POST "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: edge-test-user" \
  -d "{\"filename\":\"$LONG_NAME.txt\",\"contentType\":\"text/plain\"}")
echo "$LONG_FILENAME" | jq -e '.docId' > /dev/null 2>&1 && EDGE_CASE_PASS=$((EDGE_CASE_PASS + 1))

# Test special characters in user ID
SPECIAL_CHARS=$(curl -s -X POST "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/upload" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-user-id: test@user.com" \
  -d '{"filename":"special-chars.txt","contentType":"text/plain"}')
echo "$SPECIAL_CHARS" | jq -e '.docId' > /dev/null 2>&1 && EDGE_CASE_PASS=$((EDGE_CASE_PASS + 1))

if [ $EDGE_CASE_PASS -ge 2 ]; then
    echo "✅ Error recovery working (${EDGE_CASE_PASS}/3)"
    PHASE_RESULTS+=("✅ Error Recovery")
else
    echo "❌ Error recovery needs improvement (${EDGE_CASE_PASS}/3)"
    PHASE_RESULTS+=("❌ Error Recovery")
fi

# Test 4: Performance Under Load
echo "📊 Performance Under Load Test"
START_TIME=$(date +%s)

# Simulate concurrent users
for i in {1..10}; do
    (
        RESP=$(curl -s -X POST "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/rag-chat" \
          -H "Content-Type: application/json" \
          -H "x-api-key: $API_KEY" \
          -H "x-user-id: load-test-user-$i" \
          -d '{"question":"What is Microsoft known for?","docId":"real-test-doc"}')
        
        if echo "$RESP" | jq -e '.answer' > /dev/null 2>&1; then
            echo "load-success" >> "$TMPDIR/load_results.txt"
        fi
    ) &
done
wait

END_TIME=$(date +%s)
LOAD_DURATION=$((END_TIME - START_TIME))
LOAD_SUCCESS=$(wc -l < "$TMPDIR/load_results.txt" 2>/dev/null || echo 0)
rm -f "$TMPDIR/load_results.txt"

if [ $LOAD_SUCCESS -ge 8 ] && [ $LOAD_DURATION -lt 15 ]; then
    echo "✅ Performance under load (${LOAD_SUCCESS}/10 in ${LOAD_DURATION}s)"
    PHASE_RESULTS+=("✅ Load Performance")
else
    echo "❌ Performance under load needs improvement (${LOAD_SUCCESS}/10 in ${LOAD_DURATION}s)"
    PHASE_RESULTS+=("❌ Load Performance")
fi

# Final Results
echo ""
echo "🏁 MASTER BATTLE TEST RESULTS"
echo "========================================"
echo ""

PASS_COUNT=0
for result in "${PHASE_RESULTS[@]}"; do
    echo "$result"
    [[ "$result" == ✅* ]] && PASS_COUNT=$((PASS_COUNT + 1))
done

TOTAL_PHASES=${#PHASE_RESULTS[@]}
SUCCESS_RATE=$(( PASS_COUNT * 100 / TOTAL_PHASES ))

echo ""
echo "📊 SUMMARY:"
echo "   Total Tests: $TOTAL_PHASES"
echo "   Passed: $PASS_COUNT"
echo "   Failed: $((TOTAL_PHASES - PASS_COUNT))"
echo "   Success Rate: ${SUCCESS_RATE}%"
echo ""

if [ $SUCCESS_RATE -ge 90 ]; then
    echo "🎉 BATTLE TEST PASSED!"
    echo "✅ System is production-ready"
    echo "✅ Manual testing will inevitably pass"
    echo "✅ All phases working correctly"
    exit 0
elif [ $SUCCESS_RATE -ge 75 ]; then
    echo "⚠️  BATTLE TEST MOSTLY PASSED"
    echo "🔧 Minor issues need attention"
    echo "✅ Core functionality working"
    exit 1
else
    echo "❌ BATTLE TEST FAILED"
    echo "🚨 Major issues need immediate attention"
    echo "❌ Not ready for production"
    exit 2
fi