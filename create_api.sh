#!/bin/bash

API_ID=$(aws apigateway create-rest-api --name documentgpt-api --region us-east-1 --query 'id' --output text)
echo "API ID: $API_ID"

ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region us-east-1 --query 'items[0].id' --output text)
echo "Root ID: $ROOT_ID"

API_RESOURCE_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_ID --path-part api --region us-east-1 --query 'id' --output text)

AGENTS_RESOURCE_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $API_RESOURCE_ID --path-part agents --region us-east-1 --query 'id' --output text)
aws apigateway put-method --rest-api-id $API_ID --resource-id $AGENTS_RESOURCE_ID --http-method GET --authorization-type NONE --region us-east-1
aws apigateway put-integration --rest-api-id $API_ID --resource-id $AGENTS_RESOURCE_ID --http-method GET --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:995805900737:function:agents-handler/invocations" --region us-east-1
aws lambda add-permission --function-name agents-handler --statement-id apigateway-agents --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:995805900737:$API_ID/*/*" --region us-east-1

V5_RESOURCE_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $API_RESOURCE_ID --path-part v5 --region us-east-1 --query 'id' --output text)
HEALTH_RESOURCE_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $V5_RESOURCE_ID --path-part health --region us-east-1 --query 'id' --output text)
aws apigateway put-method --rest-api-id $API_ID --resource-id $HEALTH_RESOURCE_ID --http-method GET --authorization-type NONE --region us-east-1
aws apigateway put-integration --rest-api-id $API_ID --resource-id $HEALTH_RESOURCE_ID --http-method GET --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:995805900737:function:health-handler/invocations" --region us-east-1
aws lambda add-permission --function-name health-handler --statement-id apigateway-health --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:995805900737:$API_ID/*/*" --region us-east-1

aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod --region us-east-1

echo "API Gateway URL: https://$API_ID.execute-api.us-east-1.amazonaws.com/prod"