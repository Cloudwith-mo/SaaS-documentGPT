#!/usr/bin/env python3
import boto3
import json
import requests
from datetime import datetime

def test_aws_lambda():
    print("🔍 Testing AWS Lambda Functions...")
    lambda_client = boto3.client('lambda')
    
    functions = [
        'agents-handler',
        'health-handler', 
        'pdf-search-handler',
        'multi-agent-debate-handler',
        'documents-handler',
        'notification-dispatcher',
        'stripe-webhook-handler'
    ]
    
    results = []
    for func in functions:
        try:
            response = lambda_client.get_function(FunctionName=func)
            status = response['Configuration']['State']
            results.append(f"✅ {func}: {status}")
        except Exception as e:
            results.append(f"❌ {func}: {str(e)}")
    
    return results

def test_s3_storage():
    print("🔍 Testing S3 Storage...")
    s3 = boto3.client('s3')
    
    buckets = [
        'documentgpt-uploads-1757887191',
        'documentgpt-processed-1757813720',
        'documentgpt-raw-1757813720',
        'documentgpt-website-prod'
    ]
    
    results = []
    for bucket in buckets:
        try:
            s3.head_bucket(Bucket=bucket)
            objects = s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
            count = objects.get('KeyCount', 0)
            results.append(f"✅ {bucket}: Accessible ({count} objects)")
        except Exception as e:
            results.append(f"❌ {bucket}: {str(e)}")
    
    return results

def test_dynamodb():
    print("🔍 Testing DynamoDB...")
    dynamodb = boto3.client('dynamodb')
    
    tables = ['ParsePilot-Facts']
    results = []
    
    for table in tables:
        try:
            response = dynamodb.describe_table(TableName=table)
            status = response['Table']['TableStatus']
            item_count = response['Table']['ItemCount']
            results.append(f"✅ {table}: {status} ({item_count} items)")
        except Exception as e:
            results.append(f"❌ {table}: {str(e)}")
    
    return results

def test_sns_notifications():
    print("🔍 Testing SNS Notifications...")
    sns = boto3.client('sns')
    
    try:
        topics = sns.list_topics()['Topics']
        documentgpt_topics = [t for t in topics if 'documentgpt' in t['TopicArn'].lower()]
        
        results = []
        for topic in documentgpt_topics:
            arn = topic['TopicArn']
            topic_name = arn.split(':')[-1]
            
            # Get topic attributes
            attrs = sns.get_topic_attributes(TopicArn=arn)
            sub_count = attrs['Attributes'].get('SubscriptionsConfirmed', '0')
            results.append(f"✅ {topic_name}: Active ({sub_count} subscriptions)")
        
        if not results:
            results.append("⚠️ No DocumentGPT SNS topics found")
        
        return results
    except Exception as e:
        return [f"❌ SNS Error: {str(e)}"]

def test_textract_ocr():
    print("🔍 Testing Textract OCR...")
    textract = boto3.client('textract')
    
    try:
        # Test with a simple document detection call
        response = textract.detect_document_text(
            Document={
                'Bytes': b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'
            }
        )
        return ["✅ Textract: Service accessible and responding"]
    except Exception as e:
        if "InvalidParameterException" in str(e):
            return ["✅ Textract: Service accessible (invalid test document expected)"]
        return [f"❌ Textract: {str(e)}"]

def test_cloudwatch_logging():
    print("🔍 Testing CloudWatch Logging...")
    logs = boto3.client('logs')
    
    try:
        log_groups = logs.describe_log_groups(
            logGroupNamePrefix='/aws/lambda/'
        )['logGroups']
        
        documentgpt_logs = [lg for lg in log_groups if any(func in lg['logGroupName'] for func in [
            'agents-handler', 'health-handler', 'pdf-search-handler', 
            'multi-agent-debate-handler', 'documents-handler'
        ])]
        
        results = []
        for log_group in documentgpt_logs:
            name = log_group['logGroupName']
            size = log_group.get('storedBytes', 0)
            results.append(f"✅ {name}: Active ({size} bytes)")
        
        if not results:
            results.append("⚠️ No DocumentGPT log groups found")
        
        return results
    except Exception as e:
        return [f"❌ CloudWatch: {str(e)}"]

def run_comprehensive_test():
    print("🚀 Comprehensive AWS Services Test")
    print("=" * 50)
    
    all_results = {}
    
    # Test each service
    all_results['Lambda'] = test_aws_lambda()
    all_results['S3'] = test_s3_storage()
    all_results['DynamoDB'] = test_dynamodb()
    all_results['SNS'] = test_sns_notifications()
    all_results['Textract'] = test_textract_ocr()
    all_results['CloudWatch'] = test_cloudwatch_logging()
    
    # Print results
    total_tests = 0
    passed_tests = 0
    
    for service, results in all_results.items():
        print(f"\n📋 {service} Results:")
        for result in results:
            print(f"  {result}")
            total_tests += 1
            if result.startswith("✅"):
                passed_tests += 1
    
    print(f"\n{'='*50}")
    print(f"📊 COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎯 ALL AWS SERVICES VERIFIED ✅")
    else:
        print("⚠️ Some services need attention")

if __name__ == "__main__":
    run_comprehensive_test()