#!/usr/bin/env python3
"""Test PDF upload workflow"""
import requests

API = "https://i1dy8i3692.execute-api.us-east-1.amazonaws.com/prod"
USER = "app-test-user"
PDF_FILE = "test.pdf"

print("Testing PDF Upload Workflow")
print("=" * 60)

# Step 1: Get presigned URL
print("1. Getting upload URL...")
r = requests.post(f"{API}/upload-url", json={
    "user_id": USER,
    "filename": "AAAI-2025-Report.pdf"
})
print(f"   Status: {r.status_code}")
data = r.json()
upload_url = data.get('upload_url')
s3_key = data.get('s3_key')
print(f"   S3 Key: {s3_key}")

# Step 2: Upload PDF to S3
print("\n2. Uploading PDF to S3...")
with open(PDF_FILE, 'rb') as f:
    r = requests.put(upload_url, data=f, headers={'Content-Type': 'application/pdf'})
print(f"   Status: {r.status_code}")

# Step 3: Process PDF
print("\n3. Processing PDF...")
r = requests.post(f"{API}/upload", json={
    "user_id": USER,
    "filename": "AAAI-2025-Report.pdf",
    "s3_key": s3_key
})
print(f"   Status: {r.status_code}")
result = r.json()
print(f"   Doc ID: {result.get('doc_id')}")
print(f"   Questions: {len(result.get('questions', []))}")
if result.get('questions'):
    print(f"   Sample: {result['questions'][0][:80]}...")

print("\n" + "=" * 60)
print("PDF Upload Test Complete")
