#!/bin/bash
# Status check workaround using DynamoDB directly
DOC_ID=$1
USER_ID=$2

if [ -z "$DOC_ID" ]; then
    echo '{"error":"docId required"}'
    exit 1
fi

# Check DynamoDB directly
RESULT=$(aws dynamodb get-item --table-name documentgpt-documents --key "{\"docId\":{\"S\":\"$DOC_ID\"}}" --query 'Item' --output json 2>/dev/null)

if [ "$RESULT" = "null" ] || [ -z "$RESULT" ]; then
    echo '{"error":"Document not found"}'
    exit 1
fi

# Extract status and format response
STATUS=$(echo "$RESULT" | jq -r '.status.S // "unknown"')
FILENAME=$(echo "$RESULT" | jq -r '.filename.S // "unknown"')
UPLOADED_AT=$(echo "$RESULT" | jq -r '.uploadedAt.S // ""')

case "$STATUS" in
    "s1.ckpt-01.uploaded")
        echo "{\"docId\":\"$DOC_ID\",\"phase\":\"upload\",\"progress\":33,\"message\":\"Document uploaded\",\"status\":\"$STATUS\",\"filename\":\"$FILENAME\",\"uploadedAt\":\"$UPLOADED_AT\"}"
        ;;
    "s1.ckpt-07.parsing")
        echo "{\"docId\":\"$DOC_ID\",\"phase\":\"parsing\",\"progress\":66,\"message\":\"Processing document\",\"status\":\"$STATUS\",\"filename\":\"$FILENAME\",\"uploadedAt\":\"$UPLOADED_AT\"}"
        ;;
    "s1.ckpt-08.chat")
        echo "{\"docId\":\"$DOC_ID\",\"phase\":\"ready\",\"progress\":100,\"message\":\"Document ready for chat\",\"status\":\"$STATUS\",\"filename\":\"$FILENAME\",\"uploadedAt\":\"$UPLOADED_AT\"}"
        ;;
    *)
        echo "{\"docId\":\"$DOC_ID\",\"phase\":\"processing\",\"progress\":10,\"message\":\"Processing\",\"status\":\"$STATUS\",\"filename\":\"$FILENAME\",\"uploadedAt\":\"$UPLOADED_AT\"}"
        ;;
esac