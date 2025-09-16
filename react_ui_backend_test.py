#!/usr/bin/env python3
"""
React UI Backend Integration Test
Tests all backend endpoints with the new React-style UI
"""

import requests
import json
import time
from datetime import datetime

class ReactUIBackendTest:
    def __init__(self):
        self.api_base = 'https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod'
        self.rag_api = 'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod'
        self.results = []
        
    def log_result(self, test_name, success, details=""):
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({
            'test': test_name,
            'status': status,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        print(f"{status} {test_name}: {details}")

    def test_health_endpoints(self):
        """Test health check endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test main health endpoint
        try:
            response = requests.get(f"{self.api_base}/health", timeout=10)
            if response.status_code == 200:
                self.log_result("Health Check", True, f"Status: {response.status_code}")
            else:
                self.log_result("Health Check", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Health Check", False, f"Error: {str(e)}")
        
        # Test v5 health endpoint
        try:
            response = requests.get(f"{self.api_base}/api/v5/health", timeout=10)
            if response.status_code == 200:
                self.log_result("V5 Health Check", True, f"Status: {response.status_code}")
            else:
                self.log_result("V5 Health Check", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("V5 Health Check", False, f"Error: {str(e)}")

    def test_document_endpoints(self):
        """Test document management endpoints"""
        print("\n📄 Testing Document Endpoints...")
        
        # Test documents list
        try:
            response = requests.get(f"{self.rag_api}/documents", timeout=10)
            if response.status_code == 200:
                data = response.json()
                doc_count = len(data.get('documents', []))
                self.log_result("Documents List", True, f"Found {doc_count} documents")
            else:
                self.log_result("Documents List", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Documents List", False, f"Error: {str(e)}")
        
        # Test presign URL generation
        try:
            payload = {
                "filename": "test-document.pdf",
                "contentType": "application/pdf"
            }
            response = requests.post(f"{self.api_base}/presign", 
                                   json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                has_upload_url = 'uploadUrl' in data
                self.log_result("Presign URL", has_upload_url, 
                              f"Upload URL generated: {has_upload_url}")
            else:
                self.log_result("Presign URL", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Presign URL", False, f"Error: {str(e)}")

    def test_rag_endpoint(self):
        """Test RAG chat endpoint"""
        print("\n🤖 Testing RAG Endpoint...")
        
        try:
            payload = {
                "question": "What is this document about?",
                "docId": "sample"
            }
            response = requests.post(f"{self.rag_api}/rag", 
                                   json=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                has_answer = 'answer' in data and len(data['answer']) > 0
                self.log_result("RAG Query", has_answer, 
                              f"Answer received: {has_answer}")
            else:
                self.log_result("RAG Query", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("RAG Query", False, f"Error: {str(e)}")

    def test_pdf_content_endpoint(self):
        """Test PDF content retrieval"""
        print("\n📖 Testing PDF Content Endpoint...")
        
        try:
            response = requests.get(f"{self.api_base}/pdf-content/sample", timeout=10)
            if response.status_code == 200:
                data = response.json()
                has_content = 'content' in data and len(data['content']) > 0
                self.log_result("PDF Content", has_content, 
                              f"Content retrieved: {has_content}")
            else:
                self.log_result("PDF Content", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("PDF Content", False, f"Error: {str(e)}")

    def test_agents_endpoint(self):
        """Test agents configuration endpoint"""
        print("\n👥 Testing Agents Endpoint...")
        
        try:
            response = requests.get(f"{self.api_base}/api/agents", timeout=10)
            if response.status_code == 200:
                data = response.json()
                has_agents = isinstance(data, dict) and len(data) > 0
                self.log_result("Agents Config", has_agents, 
                              f"Agents available: {has_agents}")
            else:
                self.log_result("Agents Config", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Agents Config", False, f"Error: {str(e)}")

    def test_multi_agent_debate(self):
        """Test multi-agent debate endpoint"""
        print("\n🗣️ Testing Multi-Agent Debate...")
        
        try:
            payload = {
                "question": "Analyze the key risks in this contract",
                "docId": "sample",
                "agents": ["Legal", "Finance", "Compliance"]
            }
            response = requests.post(f"{self.api_base}/api/v5/multi-agent-debate", 
                                   json=payload, timeout=20)
            if response.status_code == 200:
                data = response.json()
                has_debate = 'debate' in data or 'consensus' in data
                self.log_result("Multi-Agent Debate", has_debate, 
                              f"Debate response: {has_debate}")
            else:
                self.log_result("Multi-Agent Debate", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Multi-Agent Debate", False, f"Error: {str(e)}")

    def test_cors_headers(self):
        """Test CORS headers for frontend integration"""
        print("\n🌐 Testing CORS Headers...")
        
        endpoints = [
            f"{self.api_base}/health",
            f"{self.rag_api}/rag",
            f"{self.api_base}/api/agents"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.options(endpoint, timeout=10)
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                has_cors = any(cors_headers.values())
                endpoint_name = endpoint.split('/')[-1]
                self.log_result(f"CORS - {endpoint_name}", has_cors, 
                              f"CORS headers present: {has_cors}")
            except Exception as e:
                endpoint_name = endpoint.split('/')[-1]
                self.log_result(f"CORS - {endpoint_name}", False, f"Error: {str(e)}")

    def test_ui_integration(self):
        """Test UI integration points"""
        print("\n🎨 Testing UI Integration...")
        
        # Test if UI file exists and is accessible
        try:
            import os
            ui_path = "/Users/muhammadadeyemi/documentgpt.io/SaaS-documentGPT/web-app/public/documentgpt.html"
            if os.path.exists(ui_path):
                with open(ui_path, 'r') as f:
                    content = f.read()
                    
                # Check for React-style components
                react_features = [
                    'gradient-btn',
                    'panel',
                    'Multi‑Agent Debate',
                    'sendMessage()',
                    'toggleDebate()',
                    'handleUploadFile'
                ]
                
                features_found = sum(1 for feature in react_features if feature in content)
                success = features_found >= len(react_features) * 0.8
                
                self.log_result("UI React Features", success, 
                              f"Found {features_found}/{len(react_features)} features")
                
                # Check API endpoint configuration
                api_endpoints = [
                    self.api_base,
                    self.rag_api
                ]
                
                endpoints_configured = sum(1 for endpoint in api_endpoints if endpoint in content)
                api_success = endpoints_configured >= len(api_endpoints)
                
                self.log_result("UI API Configuration", api_success, 
                              f"Configured {endpoints_configured}/{len(api_endpoints)} endpoints")
            else:
                self.log_result("UI File Access", False, "UI file not found")
        except Exception as e:
            self.log_result("UI Integration", False, f"Error: {str(e)}")

    def test_performance(self):
        """Test performance of key endpoints"""
        print("\n⚡ Testing Performance...")
        
        endpoints = [
            (f"{self.api_base}/health", "Health Check"),
            (f"{self.rag_api}/documents", "Documents List"),
            (f"{self.api_base}/api/agents", "Agents Config")
        ]
        
        for endpoint, name in endpoints:
            try:
                start_time = time.time()
                response = requests.get(endpoint, timeout=10)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to ms
                success = response.status_code == 200 and response_time < 3000  # Under 3 seconds
                
                self.log_result(f"Performance - {name}", success, 
                              f"{response_time:.0f}ms (Status: {response.status_code})")
            except Exception as e:
                self.log_result(f"Performance - {name}", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🚀 Starting React UI Backend Integration Tests")
        print("=" * 60)
        
        # Run all test suites
        self.test_health_endpoints()
        self.test_document_endpoints()
        self.test_rag_endpoint()
        self.test_pdf_content_endpoint()
        self.test_agents_endpoint()
        self.test_multi_agent_debate()
        self.test_cors_headers()
        self.test_ui_integration()
        self.test_performance()
        
        # Generate summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        # Save detailed results
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': success_rate
            },
            'results': self.results
        }
        
        with open('react_ui_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: react_ui_test_report.json")
        
        return success_rate >= 80  # Consider success if 80% or more tests pass

if __name__ == "__main__":
    tester = ReactUIBackendTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 React UI Backend Integration: SUCCESS!")
        exit(0)
    else:
        print("\n⚠️ React UI Backend Integration: NEEDS ATTENTION")
        exit(1)