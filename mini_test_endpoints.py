#!/usr/bin/env python3
import requests

def test_endpoint(method, endpoint, origin="https://documentgpt.io"):
    url = f"https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod{endpoint}"
    headers = {'Origin': origin}
    
    try:
        if method == "OPTIONS":
            headers.update({
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            })
            response = requests.options(url, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        
        print(f"{method} {endpoint}: {response.status_code}")
        cors_headers = {k:v for k,v in response.headers.items() if 'access-control' in k.lower()}
        if cors_headers:
            print(f"  CORS: {cors_headers}")
        else:
            print("  CORS: No headers found")
        return response.status_code
    except Exception as e:
        print(f"{method} {endpoint}: ERROR - {e}")
        return 0

print("🔍 Mini Test: API Endpoints")
print("=" * 40)

endpoints = ["/documents", "/presign", "/api/agents", "/api/health"]
for endpoint in endpoints:
    test_endpoint("OPTIONS", endpoint)
    test_endpoint("GET", endpoint)
    print()