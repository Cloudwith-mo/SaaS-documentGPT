#!/bin/bash

# Automated Test Runner for SaaS-documentGPT
# Production-ready testing with AWS focus

set -e

echo "🚀 SaaS-documentGPT Automated Test Suite"
echo "========================================"

# Check dependencies
echo "📋 Checking dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required"
    exit 1
fi

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "⚠️  AWS CLI not found - some tests may fail"
fi

# Install required packages
echo "📦 Installing test dependencies..."
pip3 install -q boto3 requests

# Set AWS region if not set
export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}

# Run the test suite
echo "🧪 Running automated tests..."
python3 automated_test_suite.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Test suite completed successfully"
else
    echo "❌ Test suite failed"
    exit 1
fi

echo "📊 Test results available in test_report_*.json"