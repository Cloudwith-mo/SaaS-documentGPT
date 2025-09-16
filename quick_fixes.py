#!/usr/bin/env python3
"""
Quick Fixes for Critical Production Issues
Addresses the most urgent problems found in validation
"""

import requests
import json
import time

def test_fix_health_endpoint():
    """Test if health endpoint can be fixed by trying different paths"""
    print("🔧 Testing Health Endpoint Fixes...")
    
    # Try different health endpoint variations
    health_endpoints = [
        'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/health',
        'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/healthz',
        'https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/health',
        'https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/healthz'
    ]
    
    for endpoint in health_endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            status = "✅ WORKING" if response.status_code == 200 else f"❌ {response.status_code}"
            print(f"  {endpoint}: {status}")
            if response.status_code == 200:
                print(f"    Response: {response.text[:100]}...")
        except Exception as e:
            print(f"  {endpoint}: ❌ ERROR - {str(e)}")

def test_upload_url_variations():
    """Test different approaches to upload URL generation"""
    print("\n🔧 Testing Upload URL Fixes...")
    
    endpoints = [
        'https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/upload-url',
        'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/upload-url'
    ]
    
    payloads = [
        {"fileName": "test.pdf", "fileType": "application/pdf"},
        {"filename": "test.pdf", "contentType": "application/pdf"},
        {"name": "test.pdf", "type": "application/pdf"}
    ]
    
    for endpoint in endpoints:
        for payload in payloads:
            try:
                response = requests.post(endpoint, json=payload, timeout=10)
                status = "✅ WORKING" if response.status_code == 200 else f"❌ {response.status_code}"
                print(f"  {endpoint} with {payload}: {status}")
                if response.status_code == 200:
                    print(f"    Response contains uploadUrl: {'uploadUrl' in response.text}")
            except Exception as e:
                print(f"  {endpoint}: ❌ ERROR - {str(e)}")

def test_error_handling_improvements():
    """Test current error handling and suggest improvements"""
    print("\n🔧 Testing Error Handling...")
    
    # Test malformed JSON handling
    endpoints_to_test = [
        'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/rag',
        'https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/upload-url'
    ]
    
    for endpoint in endpoints_to_test:
        try:
            # Test malformed JSON
            response = requests.post(endpoint, 
                                   data="invalid json", 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            
            expected_4xx = 400 <= response.status_code < 500
            status = "✅ GOOD" if expected_4xx else f"❌ BAD ({response.status_code})"
            print(f"  Malformed JSON to {endpoint}: {status}")
            
            # Test empty payload
            response = requests.post(endpoint, json={}, timeout=10)
            expected_4xx = 400 <= response.status_code < 500
            status = "✅ GOOD" if expected_4xx else f"❌ BAD ({response.status_code})"
            print(f"  Empty payload to {endpoint}: {status}")
            
        except Exception as e:
            print(f"  {endpoint}: ❌ ERROR - {str(e)}")

def test_concurrent_performance():
    """Test concurrent request handling"""
    print("\n🔧 Testing Concurrent Performance...")
    
    import concurrent.futures
    
    def make_health_request():
        try:
            response = requests.get('https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/documents', timeout=10)
            return response.status_code == 200
        except:
            return False
    
    # Test with different concurrency levels
    for workers in [2, 5, 10]:
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(make_health_request) for _ in range(workers)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            success_rate = sum(results) / len(results)
            status = "✅ GOOD" if success_rate >= 0.8 else f"❌ POOR ({success_rate:.1%})"
            print(f"  {workers} concurrent requests: {status}")
            
        except Exception as e:
            print(f"  {workers} concurrent requests: ❌ ERROR - {str(e)}")

def generate_fix_recommendations():
    """Generate specific fix recommendations"""
    print("\n💡 Fix Recommendations:")
    print("=" * 50)
    
    print("\n1. Health Endpoint Fix:")
    print("   - Update Lambda function to return proper JSON response")
    print("   - Ensure API Gateway is configured correctly")
    print("   - Example response: {'status': 'healthy', 'timestamp': '...'}")
    
    print("\n2. Upload URL Generation Fix:")
    print("   - Check Lambda execution role has S3 permissions")
    print("   - Verify API Gateway method configuration")
    print("   - Test with correct payload structure")
    
    print("\n3. Error Handling Improvements:")
    print("   - Add input validation middleware")
    print("   - Return 400 for malformed JSON, not 500")
    print("   - Implement proper exception handling in all Lambdas")
    
    print("\n4. Performance Optimization:")
    print("   - Increase Lambda concurrency limits")
    print("   - Add API Gateway throttling")
    print("   - Implement proper connection pooling")
    
    print("\n5. Monitoring Setup:")
    print("   - Add CloudWatch alarms for all critical metrics")
    print("   - Set up SNS notifications for failures")
    print("   - Create dashboard for real-time monitoring")

def main():
    """Run all quick fix tests"""
    print("🚀 Quick Fix Analysis for SaaS-documentGPT")
    print("=" * 50)
    
    test_fix_health_endpoint()
    test_upload_url_variations()
    test_error_handling_improvements()
    test_concurrent_performance()
    generate_fix_recommendations()
    
    print("\n🎯 Next Steps:")
    print("1. Apply the recommended fixes")
    print("2. Re-run production_validation_lite.py")
    print("3. Achieve 90%+ success rate before production deployment")

if __name__ == "__main__":
    main()