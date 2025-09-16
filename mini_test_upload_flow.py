#!/usr/bin/env python3
import requests
import json

def test_full_upload_flow():
    print("🔍 Mini Test 2: Full Upload Flow")
    print("=" * 40)
    
    # Step 1: Get presigned URL
    presign_url = "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/presign"
    headers = {
        'Origin': 'https://documentgpt.io',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "filename": "test.pdf",
        "contentType": "application/pdf"
    }
    
    try:
        response = requests.post(presign_url, headers=headers, json=payload)
        print(f"1. POST /presign: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            upload_url = data.get('uploadUrl')
            print(f"2. Got upload URL: {upload_url[:50]}...")
            
            # Step 2: Test S3 upload with dummy data
            test_content = b"Test PDF content"
            upload_headers = {'Content-Type': 'application/pdf'}
            
            try:
                upload_response = requests.put(upload_url, data=test_content, headers=upload_headers)
                print(f"3. PUT to S3: {upload_response.status_code}")
                
                if upload_response.status_code == 200:
                    print("✅ Upload flow working!")
                else:
                    print(f"❌ S3 upload failed: {upload_response.text}")
            except Exception as e:
                print(f"❌ S3 upload error: {e}")
        else:
            print(f"❌ Presign failed: {response.text}")
    except Exception as e:
        print(f"❌ Presign error: {e}")

if __name__ == "__main__":
    test_full_upload_flow()