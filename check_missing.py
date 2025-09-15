#!/usr/bin/env python3
"""
Check what resources are missing
"""

import requests
import boto3
from botocore.exceptions import ClientError

def check_api_endpoints():
    """Check API endpoints"""
    print("🔍 Checking API Endpoints...")
    
    base_url = "https://documentgpt.io"
    endpoints = [
        f"{base_url}/api/agents",
        f"{base_url}/api/pdf/search", 
        f"{base_url}/api/v5/health",
        f"{base_url}/api/v5/documents",
        f"{base_url}/api/v5/chat",
        f"{base_url}/api/v5/multi-agent-debate"
    ]
    
    missing = []
    working = []
    
    for endpoint in endpoints:
        try:
            if 'search' in endpoint or 'chat' in endpoint or 'debate' in endpoint:
                response = requests.post(endpoint, json={"query": "test"}, timeout=5)
            else:
                response = requests.get(endpoint, timeout=5)
                
            if response.status_code in [200, 400, 401]:
                working.append(endpoint)
            else:
                missing.append(f"{endpoint} (Status: {response.status_code})")
        except:
            missing.append(f"{endpoint} (Not accessible)")
    
    print(f"✅ Working: {len(working)}")
    print(f"❌ Missing: {len(missing)}")
    
    for endpoint in missing:
        print(f"  - {endpoint}")
    
    return len(missing) == 0

def check_aws_resources():
    """Check AWS resources"""
    print("\n🔍 Checking AWS Resources...")
    
    try:
        # Check S3 bucket
        s3 = boto3.client('s3')
        try:
            s3.head_bucket(Bucket='documentgpt-uploads')
            print("✅ S3 bucket exists")
        except ClientError:
            print("❌ S3 bucket missing")
        
        # Check DynamoDB table
        dynamodb = boto3.client('dynamodb')
        try:
            dynamodb.describe_table(TableName='documents')
            print("✅ DynamoDB table exists")
        except ClientError:
            print("❌ DynamoDB table missing")
        
        # Check Lambda functions
        lambda_client = boto3.client('lambda')
        functions = [
            'document-processing-lambda',
            'simple-rag-handler',
            'agents-handler',
            'pdf-search-handler'
        ]
        
        for func in functions:
            try:
                lambda_client.get_function(FunctionName=func)
                print(f"✅ Lambda {func} exists")
            except ClientError:
                print(f"❌ Lambda {func} missing")
        
        # Check SNS topics
        sns = boto3.client('sns')
        try:
            topics = sns.list_topics()
            doc_topic = any('document-processing' in topic['TopicArn'] for topic in topics['Topics'])
            if doc_topic:
                print("✅ SNS topic exists")
            else:
                print("❌ SNS topic missing")
        except ClientError:
            print("❌ SNS not accessible")
            
    except Exception as e:
        print(f"❌ AWS check failed: {e}")
        return False
    
    return True

def main():
    """Check all missing resources"""
    print("🎯 Checking Missing Resources")
    print("=" * 40)
    
    api_ok = check_api_endpoints()
    aws_ok = check_aws_resources()
    
    if api_ok and aws_ok:
        print("\n🎉 All resources are available!")
        return True
    else:
        print("\n❌ Some resources are missing and need to be created")
        return False

if __name__ == "__main__":
    main()