#!/bin/bash

API_ID="9voqzgx3ch"
API_RESOURCE_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region us-east-1 --query 'items[?pathPart==`api`].id' --output text)

STRIPE_RESOURCE_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $API_RESOURCE_ID --path-part stripe --region us-east-1 --query 'id' --output text)
WEBHOOK_RESOURCE_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $STRIPE_RESOURCE_ID --path-part webhook --region us-east-1 --query 'id' --output text)

aws apigateway put-method --rest-api-id $API_ID --resource-id $WEBHOOK_RESOURCE_ID --http-method POST --authorization-type NONE --region us-east-1
aws apigateway put-integration --rest-api-id $API_ID --resource-id $WEBHOOK_RESOURCE_ID --http-method POST --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:995805900737:function:stripe-webhook-handler/invocations" --region us-east-1

aws lambda add-permission --function-name stripe-webhook-handler --statement-id apigateway-stripe --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:995805900737:$API_ID/*/*" --region us-east-1

aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod --region us-east-1

echo "Added Stripe webhook endpoint"