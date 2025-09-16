#!/usr/bin/env python3
import requests
import json

# Mini Test 1: Check API Gateway CORS
print("🔍 Mini Test 1: API Gateway CORS Check")
print("=" * 50)

api_base = "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod"
origin = "https://documentgpt.io"

# Test preflight OPTIONS request
try:
    response = requests.options(f"{api_base}/documents", headers={
        'Origin': origin,
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type'
    })
    print(f"OPTIONS /documents: {response.status_code}")
    print(f"CORS Headers: {dict(response.headers)}")
except Exception as e:
    print(f"❌ OPTIONS failed: {e}")

# Test actual GET request
try:
    response = requests.get(f"{api_base}/documents", headers={'Origin': origin})
    print(f"GET /documents: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
except Exception as e:
    print(f"❌ GET failed: {e}")

print("\n🔍 Mini Test 2: Health Check")
print("=" * 50)
try:
    response = requests.get(f"{api_base}/health")
    print(f"GET /health: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Health check failed: {e}")