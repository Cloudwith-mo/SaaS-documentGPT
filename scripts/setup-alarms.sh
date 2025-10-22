#!/bin/bash
# Setup CloudWatch alarms for Lambda errors

set -e

echo "🔔 Setting up CloudWatch Alarms"
echo "==============================="
echo ""

# Get your email for alarm notifications
echo "Enter email for alarm notifications:"
read -r EMAIL

# Create SNS topic for alarms
echo "Creating SNS topic..."
TOPIC_ARN=$(aws sns create-topic --name documentgpt-alarms --region us-east-1 --query 'TopicArn' --output text)
echo "✅ Topic created: $TOPIC_ARN"

# Subscribe email to topic
echo "Subscribing $EMAIL to alarms..."
aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol email \
    --notification-endpoint "$EMAIL" \
    --region us-east-1

echo "⚠️  Check your email and confirm the subscription!"
echo ""
echo "Press Enter after confirming..."
read -r

# Create alarm for Lambda errors
echo "Creating Lambda error alarm..."
aws cloudwatch put-metric-alarm \
    --alarm-name "DocumentGPT-Lambda-Errors" \
    --alarm-description "Alert when Lambda function has errors" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=FunctionName,Value=docgpt-chat \
    --alarm-actions "$TOPIC_ARN" \
    --region us-east-1

echo "✅ Error alarm created (triggers at 5+ errors in 5 minutes)"

# Create alarm for Lambda throttles
echo "Creating Lambda throttle alarm..."
aws cloudwatch put-metric-alarm \
    --alarm-name "DocumentGPT-Lambda-Throttles" \
    --alarm-description "Alert when Lambda function is throttled" \
    --metric-name Throttles \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 1 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=FunctionName,Value=docgpt-chat \
    --alarm-actions "$TOPIC_ARN" \
    --region us-east-1

echo "✅ Throttle alarm created"

# Create alarm for high duration (performance)
echo "Creating Lambda duration alarm..."
aws cloudwatch put-metric-alarm \
    --alarm-name "DocumentGPT-Lambda-SlowResponse" \
    --alarm-description "Alert when Lambda responses are slow" \
    --metric-name Duration \
    --namespace AWS/Lambda \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 10000 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=FunctionName,Value=docgpt-chat \
    --alarm-actions "$TOPIC_ARN" \
    --region us-east-1

echo "✅ Duration alarm created (triggers at >10s average)"

echo ""
echo "🎉 All alarms configured!"
echo ""
echo "You'll receive email alerts for:"
echo "  • Lambda errors (5+ in 5 minutes)"
echo "  • Lambda throttles (any throttling)"
echo "  • Slow responses (>10s average)"
echo ""
echo "View alarms: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:"
