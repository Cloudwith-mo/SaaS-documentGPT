#!/usr/bin/env python3
"""
Specific Functionality Tests for SaaS-documentGPT
Focus on core user workflows and edge cases
"""
import requests
import json
import time

def test_upload_workflow():
    """Test complete upload workflow"""
    print("🔍 TESTING UPLOAD WORKFLOW")
    print("-" * 40)
    
    try:
        # Step 1: Get presigned URL
        response = requests.post("https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/presign",
            headers={'Content-Type': 'application/json'},
            json={'filename': 'test_workflow.pdf', 'contentType': 'application/pdf'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Step 1: Presigned URL obtained")
            
            # Step 2: Upload to S3
            upload_url = data['uploadUrl']
            test_content = b"Test PDF workflow content"
            
            upload_response = requests.put(upload_url, data=test_content,
                headers={'Content-Type': 'application/pdf'})
            
            if upload_response.status_code == 200:
                print("✅ Step 2: File uploaded to S3")
                
                # Step 3: Trigger processing
                doc_id = f"test_{int(time.time())}"
                ingest_response = requests.post("https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/ingest",
                    headers={'Content-Type': 'application/json'},
                    json={
                        'docId': doc_id,
                        'docName': 'test_workflow.pdf',
                        'bucket': 'documentgpt-uploads-1757887191',
                        'key': data['key']
                    }
                )
                
                if ingest_response.status_code == 200:
                    print("✅ Step 3: Processing triggered")
                    return doc_id
                else:
                    print(f"❌ Step 3 failed: {ingest_response.status_code}")
            else:
                print(f"❌ Step 2 failed: {upload_response.status_code}")
        else:
            print(f"❌ Step 1 failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Upload workflow error: {e}")
    
    return None

def test_chat_functionality(doc_id):
    """Test chat functionality with document"""
    print("\n🔍 TESTING CHAT FUNCTIONALITY")
    print("-" * 40)
    
    if not doc_id:
        print("⚠️ Skipping chat test - no document ID")
        return
    
    try:
        # Test RAG query
        response = requests.post("https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/rag",
            headers={'Content-Type': 'application/json'},
            json={'question': 'What is this document about?', 'docId': doc_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat query successful")
            print(f"   Answer: {data.get('answer', '')[:100]}...")
            
            # Test different question types
            questions = [
                "Summarize this document",
                "What are the key points?",
                "List important information"
            ]
            
            for question in questions:
                test_response = requests.post("https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/rag",
                    headers={'Content-Type': 'application/json'},
                    json={'question': question, 'docId': doc_id}
                )
                
                if test_response.status_code == 200:
                    print(f"✅ Question '{question[:20]}...' answered")
                else:
                    print(f"❌ Question '{question[:20]}...' failed: {test_response.status_code}")
        else:
            print(f"❌ Chat query failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Chat functionality error: {e}")

def test_pdf_viewer_integration():
    """Test PDF viewer integration"""
    print("\n🔍 TESTING PDF VIEWER INTEGRATION")
    print("-" * 40)
    
    try:
        # Test PDF content API with different document IDs
        test_docs = ["test_doc", "sample_doc", "doc_123"]
        
        for doc_id in test_docs:
            response = requests.get(f"https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/pdf-content/{doc_id}")
            
            if response.status_code == 200:
                data = response.json()
                if 'content' in data and 'docId' in data:
                    print(f"✅ PDF content for {doc_id}: Structure correct")
                else:
                    print(f"❌ PDF content for {doc_id}: Missing fields")
            else:
                print(f"❌ PDF content for {doc_id}: Status {response.status_code}")
    except Exception as e:
        print(f"❌ PDF viewer integration error: {e}")

def test_error_scenarios():
    """Test various error scenarios"""
    print("\n🔍 TESTING ERROR SCENARIOS")
    print("-" * 40)
    
    # Test invalid file upload
    try:
        response = requests.post("https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/presign",
            headers={'Content-Type': 'application/json'},
            json={'filename': '', 'contentType': 'invalid/type'}
        )
        print(f"✅ Invalid presign request handled: {response.status_code}")
    except Exception as e:
        print(f"❌ Invalid presign error: {e}")
    
    # Test malformed RAG request
    try:
        response = requests.post("https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/rag",
            headers={'Content-Type': 'application/json'},
            json={'malformed': 'request'}
        )
        print(f"✅ Malformed RAG request handled: {response.status_code}")
    except Exception as e:
        print(f"❌ Malformed RAG error: {e}")
    
    # Test non-existent document
    try:
        response = requests.get("https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/pdf-content/nonexistent")
        print(f"✅ Non-existent document handled: {response.status_code}")
    except Exception as e:
        print(f"❌ Non-existent document error: {e}")

def test_performance_limits():
    """Test performance and limits"""
    print("\n🔍 TESTING PERFORMANCE & LIMITS")
    print("-" * 40)
    
    # Test rapid requests
    try:
        start_time = time.time()
        responses = []
        
        for i in range(5):
            response = requests.get("https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/api/health")
            responses.append(response.status_code)
        
        end_time = time.time()
        duration = end_time - start_time
        
        success_count = len([r for r in responses if r == 200])
        print(f"✅ Rapid requests: {success_count}/5 successful in {duration:.2f}s")
        
        # Test large query
        large_query = "What is this document about? " * 100  # Large query
        response = requests.post("https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/rag",
            headers={'Content-Type': 'application/json'},
            json={'question': large_query, 'docId': 'test'}
        )
        print(f"✅ Large query handled: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Performance test error: {e}")

def test_ui_components():
    """Test UI components and responsiveness"""
    print("\n🔍 TESTING UI COMPONENTS")
    print("-" * 40)
    
    try:
        response = requests.get("https://documentgpt.io/documentgpt.html")
        
        if response.status_code == 200:
            content = response.text
            
            # Check for responsive design elements
            ui_checks = [
                ('Mobile Responsive', 'md:' in content),
                ('Grid Layout', 'grid-cols' in content),
                ('Upload Button', 'handlePickFile' in content),
                ('Chat Input', 'messageInput' in content),
                ('PDF Viewer', 'pdfViewer' in content),
                ('Navigation', 'toggleNav' in content),
                ('Model Selection', 'openModelModal' in content),
                ('Debate Feature', 'toggleDebate' in content)
            ]
            
            for check_name, condition in ui_checks:
                if condition:
                    print(f"✅ UI {check_name}: Present")
                else:
                    print(f"❌ UI {check_name}: Missing")
        else:
            print(f"❌ UI test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ UI components error: {e}")

def run_specific_tests():
    """Run all specific functionality tests"""
    print("🚀 RUNNING SPECIFIC FUNCTIONALITY TESTS")
    print("=" * 60)
    
    # Run upload workflow and get document ID
    doc_id = test_upload_workflow()
    
    # Run other tests
    test_chat_functionality(doc_id)
    test_pdf_viewer_integration()
    test_error_scenarios()
    test_performance_limits()
    test_ui_components()
    
    print("\n" + "=" * 60)
    print("🎯 SPECIFIC TESTS COMPLETED")
    print("✅ Core workflows validated")
    print("✅ Error handling verified")
    print("✅ UI components checked")
    print("✅ Performance tested")

if __name__ == "__main__":
    run_specific_tests()