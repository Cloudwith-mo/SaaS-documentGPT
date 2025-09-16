#!/usr/bin/env python3
import requests
import json

def test_rag_endpoint():
    print("🔍 Mini Test 4: Verify RAG Endpoint")
    print("=" * 50)
    
    rag_url = "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/rag"
    
    print("1. Testing OPTIONS preflight:")
    try:
        response = requests.options(rag_url, headers={
            'Origin': 'https://documentgpt.io',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        })
        print(f"   Status: {response.status_code}")
        cors_headers = {k:v for k,v in response.headers.items() if 'access-control' in k.lower()}
        print(f"   CORS Headers: {cors_headers}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n2. Testing POST request:")
    try:
        response = requests.post(rag_url, 
            headers={
                'Origin': 'https://documentgpt.io',
                'Content-Type': 'application/json'
            },
            json={
                'question': 'What is this document about?',
                'docId': 'test_doc'
            }
        )
        print(f"   Status: {response.status_code}")
        cors_headers = {k:v for k,v in response.headers.items() if 'access-control' in k.lower()}
        print(f"   CORS Headers: {cors_headers}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n3. Result:")
    if response.status_code == 200:
        print("   ✅ RAG endpoint working with CORS!")
    else:
        print("   ❌ RAG endpoint has issues")

if __name__ == "__main__":
    test_rag_endpoint()