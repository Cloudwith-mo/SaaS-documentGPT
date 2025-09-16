#!/usr/bin/env python3
"""Mini Test 2: Upload URL Generation"""

import requests
import json

def test_upload_url():
    print("🧪 Mini Test 2: Upload URL Generation")
    
    endpoint = 'https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/upload-url'
    
    payloads = [
        {"fileName": "test.pdf", "fileType": "application/pdf"},
        {"filename": "test.pdf", "contentType": "application/pdf"}
    ]
    
    for payload in payloads:
        try:
            response = requests.post(endpoint, json=payload, timeout=10)
            print(f"  Payload {payload}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                has_url = 'uploadUrl' in data
                print(f"    ✅ SUCCESS: Has uploadUrl: {has_url}")
                return True
            else:
                print(f"    ❌ FAIL: {response.text[:100]}")
        except Exception as e:
            print(f"    ❌ ERROR: {str(e)}")
    
    return False

if __name__ == "__main__":
    test_upload_url()