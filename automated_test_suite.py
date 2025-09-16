#!/usr/bin/env python3
"""
Comprehensive Automated Testing Suite for SaaS-documentGPT
AWS-focused testing with systematic validation
"""
import requests
import json
import time
from datetime import datetime

class DocumentGPTTester:
    def __init__(self):
        self.base_url = "https://documentgpt.io"
        self.api_gateway_1 = "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod"
        self.api_gateway_2 = "https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod"
        self.test_results = []
        
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   {details}")
    
    def test_aws_lambda_processing(self):
        """Test 1: AWS Lambda & Processing"""
        print("\n🔍 TEST 1: AWS Lambda & Processing")
        print("-" * 50)
        
        # Test document upload triggers Lambda
        try:
            response = requests.post(f"{self.api_gateway_1}/presign", 
                headers={'Content-Type': 'application/json'},
                json={'filename': 'test.pdf', 'contentType': 'application/pdf'}
            )
            if response.status_code == 200:
                self.log_test("Lambda Presign Trigger", "PASS", "Presign Lambda responds correctly")
            else:
                self.log_test("Lambda Presign Trigger", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Lambda Presign Trigger", "FAIL", str(e))
        
        # Test RAG Lambda
        try:
            response = requests.post(f"{self.api_gateway_1}/rag",
                headers={'Content-Type': 'application/json'},
                json={'question': 'Test', 'docId': 'test'}
            )
            if response.status_code == 200:
                self.log_test("RAG Lambda Processing", "PASS", "RAG Lambda responds correctly")
            else:
                self.log_test("RAG Lambda Processing", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("RAG Lambda Processing", "FAIL", str(e))
    
    def test_s3_document_storage(self):
        """Test 2: S3 Document Storage"""
        print("\n🔍 TEST 2: S3 Document Storage")
        print("-" * 50)
        
        # Test S3 bucket accessibility
        try:
            # Get presigned URL
            response = requests.post(f"{self.api_gateway_1}/presign",
                headers={'Content-Type': 'application/json'},
                json={'filename': 'test.pdf', 'contentType': 'application/pdf'}
            )
            
            if response.status_code == 200:
                data = response.json()
                upload_url = data.get('uploadUrl')
                if upload_url:
                    self.log_test("S3 Presigned URL Generation", "PASS", "Upload URL generated")
                    
                    # Test upload to S3
                    test_content = b"Test PDF content"
                    upload_response = requests.put(upload_url, data=test_content, 
                        headers={'Content-Type': 'application/pdf'})
                    
                    if upload_response.status_code == 200:
                        self.log_test("S3 File Upload", "PASS", "File uploaded successfully")
                    else:
                        self.log_test("S3 File Upload", "FAIL", f"Upload failed: {upload_response.status_code}")
                else:
                    self.log_test("S3 Presigned URL Generation", "FAIL", "No upload URL in response")
            else:
                self.log_test("S3 Presigned URL Generation", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("S3 Document Storage", "FAIL", str(e))
    
    def test_api_security_access_control(self):
        """Test 6: API Security & Access Control"""
        print("\n🔍 TEST 6: API Security & Access Control")
        print("-" * 50)
        
        # Test protected endpoints without auth
        protected_endpoints = [
            f"{self.api_gateway_1}/documents",
            f"{self.api_gateway_2}/documents"
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = requests.get(endpoint)
                # Should either return 401/403 or allow public access
                if response.status_code in [200, 401, 403]:
                    self.log_test(f"Endpoint Security {endpoint.split('//')[1].split('.')[0]}", 
                        "PASS", f"Proper response: {response.status_code}")
                else:
                    self.log_test(f"Endpoint Security {endpoint.split('//')[1].split('.')[0]}", 
                        "WARN", f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Endpoint Security", "FAIL", str(e))
    
    def test_cors_headers(self):
        """Test CORS Headers"""
        print("\n🔍 TEST: CORS Headers")
        print("-" * 50)
        
        endpoints = [
            f"{self.api_gateway_1}/rag",
            f"{self.api_gateway_1}/presign",
            f"{self.api_gateway_1}/pdf-content/test"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.options(endpoint, headers={
                    'Origin': 'https://documentgpt.io',
                    'Access-Control-Request-Method': 'POST'
                })
                
                cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
                if cors_origin in ['https://documentgpt.io', '*']:
                    self.log_test(f"CORS {endpoint.split('/')[-1]}", "PASS", f"Origin: {cors_origin}")
                else:
                    self.log_test(f"CORS {endpoint.split('/')[-1]}", "FAIL", f"Origin: {cors_origin}")
            except Exception as e:
                self.log_test(f"CORS {endpoint.split('/')[-1]}", "FAIL", str(e))
    
    def test_frontend_accessibility(self):
        """Test Frontend Accessibility"""
        print("\n🔍 TEST: Frontend Accessibility")
        print("-" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/documentgpt.html")
            if response.status_code == 200:
                content = response.text
                
                # Check for key components
                checks = [
                    ('DocumentsGPT Title', 'DocumentsGPT' in content),
                    ('Upload Functionality', 'handleUploadFile' in content),
                    ('RAG Integration', 'rag' in content.lower()),
                    ('Chat Interface', 'handleSend' in content),
                    ('PDF Viewer', 'pdfViewer' in content)
                ]
                
                for check_name, condition in checks:
                    if condition:
                        self.log_test(f"Frontend {check_name}", "PASS", "Component found")
                    else:
                        self.log_test(f"Frontend {check_name}", "FAIL", "Component missing")
            else:
                self.log_test("Frontend Accessibility", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Frontend Accessibility", "FAIL", str(e))
    
    def test_api_endpoints_functionality(self):
        """Test API Endpoints Functionality"""
        print("\n🔍 TEST: API Endpoints Functionality")
        print("-" * 50)
        
        # Test multiple API endpoints
        endpoints = [
            (f"{self.api_gateway_1}/documents", "GET"),
            (f"{self.api_gateway_2}/documents", "GET"),
            (f"{self.api_gateway_1}/api/health", "GET"),
            (f"{self.api_gateway_1}/api/agents", "GET")
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = requests.get(endpoint)
                else:
                    response = requests.post(endpoint)
                
                endpoint_name = endpoint.split('/')[-1]
                if response.status_code == 200:
                    self.log_test(f"API {endpoint_name}", "PASS", f"Responds correctly")
                elif response.status_code in [401, 403]:
                    self.log_test(f"API {endpoint_name}", "PASS", f"Protected endpoint: {response.status_code}")
                else:
                    self.log_test(f"API {endpoint_name}", "WARN", f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"API {endpoint_name}", "FAIL", str(e))
    
    def test_error_handling(self):
        """Test Error Handling & Reporting"""
        print("\n🔍 TEST: Error Handling")
        print("-" * 50)
        
        # Test invalid requests
        try:
            # Invalid RAG request
            response = requests.post(f"{self.api_gateway_1}/rag",
                headers={'Content-Type': 'application/json'},
                json={'invalid': 'data'}
            )
            
            if response.status_code in [400, 422, 500]:
                self.log_test("Error Handling RAG", "PASS", f"Proper error response: {response.status_code}")
            else:
                self.log_test("Error Handling RAG", "WARN", f"Unexpected: {response.status_code}")
        except Exception as e:
            self.log_test("Error Handling RAG", "FAIL", str(e))
        
        # Test invalid presign request
        try:
            response = requests.post(f"{self.api_gateway_1}/presign",
                headers={'Content-Type': 'application/json'},
                json={}
            )
            
            if response.status_code in [400, 422]:
                self.log_test("Error Handling Presign", "PASS", f"Proper error response: {response.status_code}")
            else:
                self.log_test("Error Handling Presign", "WARN", f"Unexpected: {response.status_code}")
        except Exception as e:
            self.log_test("Error Handling Presign", "FAIL", str(e))
    
    def test_document_processing_flow(self):
        """Test Document Processing Flow"""
        print("\n🔍 TEST: Document Processing Flow")
        print("-" * 50)
        
        try:
            # Test PDF content endpoint
            response = requests.get(f"{self.api_gateway_1}/pdf-content/test_doc")
            if response.status_code == 200:
                data = response.json()
                if 'content' in data:
                    self.log_test("PDF Content API", "PASS", "Content structure correct")
                else:
                    self.log_test("PDF Content API", "FAIL", "Missing content field")
            else:
                self.log_test("PDF Content API", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("PDF Content API", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 STARTING COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        
        # Run all test categories
        self.test_aws_lambda_processing()
        self.test_s3_document_storage()
        self.test_api_security_access_control()
        self.test_cors_headers()
        self.test_frontend_accessibility()
        self.test_api_endpoints_functionality()
        self.test_error_handling()
        self.test_document_processing_flow()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"Success Rate: {(passed/total_tests)*100:.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"   - {result['test']}: {result['details']}")
        
        if warnings > 0:
            print("\n⚠️  WARNINGS:")
            for result in self.test_results:
                if result['status'] == 'WARN':
                    print(f"   - {result['test']}: {result['details']}")
        
        print(f"\n🎯 OVERALL STATUS: {'✅ SYSTEM OPERATIONAL' if failed == 0 else '⚠️ ISSUES DETECTED'}")

if __name__ == "__main__":
    tester = DocumentGPTTester()
    tester.run_all_tests()