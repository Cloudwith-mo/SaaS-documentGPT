#!/bin/bash

# Core functions to KEEP (production)
KEEP_FUNCTIONS=(
    "documentgpt-rag-chat"
    "documents-handler" 
    "documentgpt-indexer"
    "documentgpt-presign"
    "documentgpt-process-doc"
)

# Legacy functions to DELETE
DELETE_FUNCTIONS=(
    "documentgpt-status-poll"
    "documentgpt-s3-trigger"
    "documentsgpt-billing-checkout"
    "documentgpt-root"
    "documentgpt-parser"
    "documentsgpt-vector-store-create"
    "documentgpt-upload"
    "parsepilot-documents"
    "documentgpt-v5-api"
    "documentgpt-process-document"
    "documentgpt-chat"
    "documentsgpt-billing-portal"
    "documentgpt-ingest-worker"
    "documentsgpt-billing-webhook"
    "documentsgpt-upload-ingest"
    "documentsgpt-upload-create"
    "documentgpt-process"
    "documentgpt-ingest"
    "documentgpt-rag"
    "documentsgpt-chat-stream"
    "documentgpt-documents"
)

echo "🗑️  Deleting legacy functions..."

for func in "${DELETE_FUNCTIONS[@]}"; do
    echo "Deleting $func..."
    aws lambda delete-function --function-name "$func" 2>/dev/null || echo "  (already deleted or doesn't exist)"
done

echo "✅ Cleanup complete. Kept ${#KEEP_FUNCTIONS[@]} core functions, deleted ${#DELETE_FUNCTIONS[@]} legacy functions."