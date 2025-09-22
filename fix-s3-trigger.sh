#!/bin/bash

echo "🔧 Fixing S3 trigger for multi-tenant paths"

# Update S3 notification to trigger on users/ prefix instead of doc_ prefix
aws s3api put-bucket-notification-configuration \
  --bucket documentgpt-uploads \
  --region us-east-1 \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [
      {
        "Id": "documentgpt-processing-trigger",
        "LambdaFunctionArn": "arn:aws:lambda:us-east-1:995805900737:function:documentgpt-s3-trigger",
        "Events": ["s3:ObjectCreated:*"],
        "Filter": {
          "Key": {
            "FilterRules": [
              {
                "Name": "Prefix",
                "Value": "users/"
              }
            ]
          }
        }
      }
    ]
  }'

echo "✅ S3 trigger updated to handle users/ prefix"