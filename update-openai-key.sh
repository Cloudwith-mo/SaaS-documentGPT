#!/bin/bash
# Update OpenAI API Key in AWS Secrets Manager
# Usage: ./update-openai-key.sh "sk-proj-NEW_KEY_HERE"

if [ -z "$1" ]; then
    echo "Usage: $0 <new-openai-api-key>"
    echo "Example: $0 sk-proj-abc123..."
    exit 1
fi

NEW_KEY="$1"

echo "Updating OpenAI API key in AWS Secrets Manager..."
aws secretsmanager update-secret --secret-id OPENAI_API_KEY --secret-string "$NEW_KEY"

echo "✅ OpenAI API key updated successfully"
echo "Processing should work within 1-2 minutes"