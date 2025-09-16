#!/usr/bin/env python3
"""Mini Test 1: Health Endpoint Fix"""

import requests

def test_health_endpoint():
    print("🧪 Mini Test 1: Health Endpoint")
    
    endpoints = [
        'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/health',
        'https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/health'
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            print(f"  {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"    ✅ SUCCESS: {response.json()}")
                return True
            else:
                print(f"    ❌ FAIL: {response.text[:100]}")
        except Exception as e:
            print(f"    ❌ ERROR: {str(e)}")
    
    return False

if __name__ == "__main__":
    test_health_endpoint()