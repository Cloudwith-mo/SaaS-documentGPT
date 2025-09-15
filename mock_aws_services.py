#!/usr/bin/env python3
"""
Mock AWS Services for testing
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import time

app = Flask(__name__)
CORS(app)

# Mock Lambda functions
@app.route('/aws/lambda/<function_name>')
def lambda_status(function_name):
    return jsonify({
        "Configuration": {
            "FunctionName": function_name,
            "State": "Active",
            "Runtime": "python3.9"
        }
    })

# Mock S3 bucket
@app.route('/aws/s3/documentgpt-uploads')
def s3_bucket():
    return jsonify({
        "Name": "documentgpt-uploads",
        "CreationDate": "2024-01-01T00:00:00Z"
    })

@app.route('/aws/s3/documentgpt-uploads/public-access-block')
def s3_public_access():
    return jsonify({
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True
        }
    })

# Mock DynamoDB
@app.route('/aws/dynamodb/documents')
def dynamodb_table():
    return jsonify({
        "Table": {
            "TableName": "documents",
            "TableStatus": "ACTIVE",
            "SSEDescription": {
                "Status": "ENABLED"
            }
        }
    })

# Mock SNS
@app.route('/aws/sns/topics')
def sns_topics():
    return jsonify({
        "Topics": [
            {"TopicArn": "arn:aws:sns:us-east-1:123456789012:document-processing"}
        ]
    })

# Mock Textract
@app.route('/aws/textract/detect-document-text', methods=['POST'])
def textract_detect():
    return jsonify({
        "Blocks": [
            {"BlockType": "LINE", "Text": "Sample extracted text"}
        ]
    })

# Mock CloudWatch
@app.route('/aws/cloudwatch/log-groups')
def cloudwatch_logs():
    return jsonify({
        "logGroups": [
            {"logGroupName": "/aws/lambda/document-processing"},
            {"logGroupName": "/aws/apigateway/api-gateway"},
            {"logGroupName": "/aws/lambda/lambda-functions"}
        ]
    })

if __name__ == '__main__':
    app.run(port=8081, debug=True)