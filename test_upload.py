#!/usr/bin/env python3
import requests
import json

# Test complete upload flow
def test_upload_flow():
    print("🧪 Testing complete upload flow...")
    
    # Step 1: Get presigned URL
    presign_response = requests.post(
        'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/presign',
        json={'filename': 'test_doc.pdf', 'contentType': 'application/pdf'}
    )
    
    if presign_response.status_code == 200:
        data = presign_response.json()
        print(f"✅ Got presigned URL: {data['key']}")
        
        # Step 2: Create test file content
        test_content = b"This is a test PDF document for DocumentsGPT v5 testing."
        
        # Step 3: Upload to S3
        upload_response = requests.put(
            data['uploadUrl'],
            data=test_content,
            headers={'Content-Type': 'application/pdf'}
        )
        
        if upload_response.status_code == 200:
            print("✅ File uploaded to S3")
            
            # Step 4: Trigger processing
            doc_id = f"test_doc_{int(__import__('time').time())}"
            ingest_response = requests.post(
                'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/ingest',
                json={
                    'docId': doc_id,
                    'docName': 'test_doc.pdf',
                    'bucket': 'documentgpt-uploads-1757887191',
                    'key': data['key']
                }
            )
            
            if ingest_response.status_code == 200:
                print(f"✅ Document processing started: {doc_id}")
                
                # Step 5: Test RAG query after processing
                import time
                time.sleep(5)  # Wait for processing
                
                rag_response = requests.post(
                    'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/rag',
                    json={'question': 'What is this document about?', 'docId': doc_id}
                )
                
                if rag_response.status_code == 200:
                    result = rag_response.json()
                    print(f"✅ RAG Response: {result.get('answer', 'No answer')}")
                    return doc_id
                else:
                    print(f"❌ RAG failed: {rag_response.status_code}")
            else:
                print(f"❌ Ingest failed: {ingest_response.status_code}")
        else:
            print(f"❌ Upload failed: {upload_response.status_code}")
    else:
        print(f"❌ Presign failed: {presign_response.status_code}")
    
    return None

if __name__ == "__main__":
    test_upload_flow()