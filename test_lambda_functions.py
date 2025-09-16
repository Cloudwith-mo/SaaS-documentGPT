#!/usr/bin/env python3
"""
Test Lambda functions directly to verify fixes
"""

import json
import sys
import os

# Add handlers to path
sys.path.append('/Users/muhammadadeyemi/documentgpt.io/SaaS-documentGPT/src/handlers')

def test_health_handler():
    """Test health check handler directly"""
    print("🔍 Testing Health Handler...")
    
    try:
        from health_check_handler import lambda_handler
        
        event = {'httpMethod': 'GET'}
        context = {}
        
        result = lambda_handler(event, context)
        
        passed = result['statusCode'] == 200
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} Health Handler: Status {result['statusCode']}")
        
        if passed:
            body = json.loads(result['body'])
            print(f"    Response: {body}")
        
        return passed
        
    except Exception as e:
        print(f"  ❌ FAIL Health Handler: {str(e)}")
        return False

def test_upload_handler():
    """Test upload URL handler directly"""
    print("\n🔍 Testing Upload Handler...")
    
    try:
        from upload_url_handler import lambda_handler
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'fileName': 'test.pdf',
                'fileType': 'application/pdf'
            })
        }
        context = {}
        
        result = lambda_handler(event, context)
        
        passed = result['statusCode'] == 200
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} Upload Handler: Status {result['statusCode']}")
        
        if passed:
            body = json.loads(result['body'])
            print(f"    Has uploadUrl: {'uploadUrl' in body}")
        else:
            print(f"    Error: {result.get('body', 'No error message')}")
        
        return passed
        
    except Exception as e:
        print(f"  ❌ FAIL Upload Handler: {str(e)}")
        return False

def test_rag_handler():
    """Test RAG handler directly"""
    print("\n🔍 Testing RAG Handler...")
    
    try:
        from rag_handler_cors import lambda_handler
        
        # Test valid request
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'query': 'What is this document about?',
                'document_id': 'test-doc'
            })
        }
        context = {}
        
        result = lambda_handler(event, context)
        
        passed = result['statusCode'] in [200, 400]  # 400 OK for missing doc
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} RAG Handler (valid): Status {result['statusCode']}")
        
        # Test malformed JSON
        event_bad = {
            'httpMethod': 'POST',
            'body': 'invalid json'
        }
        
        result_bad = lambda_handler(event_bad, context)
        
        passed_bad = result_bad['statusCode'] == 400
        status_bad = "✅ PASS" if passed_bad else "❌ FAIL"
        print(f"  {status_bad} RAG Handler (malformed JSON): Status {result_bad['statusCode']}")
        
        return passed and passed_bad
        
    except Exception as e:
        print(f"  ❌ FAIL RAG Handler: {str(e)}")
        return False

def main():
    """Run all Lambda function tests"""
    print("🧪 Testing Lambda Functions Directly")
    print("=" * 50)
    
    tests = [
        ("Health Handler", test_health_handler),
        ("Upload Handler", test_upload_handler),
        ("RAG Handler", test_rag_handler)
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append(result)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Lambda Function Test Results:")
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("✅ All Lambda functions working correctly!")
        print("💡 Issue is likely with API Gateway deployment")
    else:
        print("❌ Lambda functions need additional fixes")

if __name__ == "__main__":
    main()