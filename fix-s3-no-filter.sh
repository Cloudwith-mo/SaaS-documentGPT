#!/bin/bash

echo "🔧 Removing S3 filter to trigger on all uploads"

# Remove filter entirely - trigger on all S3 uploads
aws s3api put-bucket-notification-configuration \
  --bucket documentgpt-uploads \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [
      {
        "Id": "documentgpt-processing-trigger",
        "LambdaFunctionArn": "arn:aws:lambda:us-east-1:995805900737:function:documentgpt-s3-trigger",
        "Events": ["s3:ObjectCreated:*"]
      }
    ]
  }'

echo "✅ S3 trigger updated to fire on all uploads"