#!/usr/bin/env bash
# Test configuration - set these before running tests
# Working endpoints
export UPLOAD_BASE="https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod"
export CHAT_BASE="https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod"
export API_BASE="https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod"
export AWS_REGION="us-east-1"
export S3_BUCKET="documentgpt-uploads"
export UPLOAD_TABLE="documentgpt-documents"
export STEPFUNCTION_ARN="arn:aws:states:us-east-1:995805900737:stateMachine:documentgpt-processing"
export TMPDIR="./tmp_test"
export OPENAI_TEST="true"
export API_KEY="dk-test-key-123"
export TEST_USER_ID="test-suite-user"

# Create temp directory
mkdir -p "$TMPDIR"