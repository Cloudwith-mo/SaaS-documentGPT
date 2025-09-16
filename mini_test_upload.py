#!/usr/bin/env python3
import requests
import json

def test_presign_endpoint():
    print("🔍 Mini Test 1: Presign Endpoint")
    print("=" * 40)
    
    url = "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/presign"
    headers = {
        'Origin': 'https://documentgpt.io',
        'Content-Type': 'application/json'
    }
    
    # Test OPTIONS first
    try:
        response = requests.options(url, headers=headers)
        print(f"OPTIONS /presign: {response.status_code}")
        cors_headers = {k:v for k,v in response.headers.items() if 'access-control' in k.lower()}
        print(f"CORS: {cors_headers}")
    except Exception as e:
        print(f"OPTIONS error: {e}")
    
    # Test POST with sample data
    payload = {
        "filename": "test.pdf",
        "contentType": "application/pdf"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"POST /presign: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            if 'uploadUrl' in data:
                print(f"Upload URL: {data['uploadUrl'][:50]}...")
            else:
                print(f"Response: {data}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"POST error: {e}")

if __name__ == "__main__":
    test_presign_endpoint()