#!/usr/bin/env python3
import requests

def test_cors_diagnosis():
    print("🔍 Mini Test 1: CORS Diagnosis")
    print("=" * 50)
    
    # Test the problematic RAG endpoint
    rag_url = "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/rag"
    
    print("1. Testing OPTIONS preflight request:")
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
                'question': 'test',
                'docId': 'test'
            }
        )
        print(f"   Status: {response.status_code}")
        cors_headers = {k:v for k,v in response.headers.items() if 'access-control' in k.lower()}
        print(f"   CORS Headers: {cors_headers}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n3. Diagnosis:")
    print("   Issue: RAG endpoint missing CORS headers")
    print("   Solution: Add OPTIONS method and CORS to RAG endpoint")

if __name__ == "__main__":
    test_cors_diagnosis()