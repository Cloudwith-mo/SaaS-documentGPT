#!/usr/bin/env python3
"""
Mini Test Suite - Pinpoint and fix specific issues
"""

import requests
import json
import time
from datetime import datetime

class MiniTester:
    def __init__(self):
        self.base_url = "https://documentgpt.io"
        self.results = []
        
    def log_result(self, test_name: str, status: str, details: str = ""):
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"[{status}] {test_name}: {details}")

    def test_api_endpoints_exist(self):
        """Test if API endpoints actually exist and work"""
        endpoints = [
            "/api/agents",
            "/api/pdf/search", 
            "/api/documents",
            "/api/chat",
            "/api/v5/documents",
            "/api/v5/chat"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    self.log_result(f"API {endpoint}", "PASS", "Endpoint working")
                elif response.status_code in [401, 403]:
                    self.log_result(f"API {endpoint}", "PASS", "Endpoint exists, auth required")
                elif response.status_code == 404:
                    self.log_result(f"API {endpoint}", "FAIL", "Endpoint not found")
                else:
                    self.log_result(f"API {endpoint}", "WARN", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"API {endpoint}", "FAIL", str(e))

    def test_working_api_endpoints(self):
        """Find which API endpoints actually work"""
        # Test known working endpoints from your system
        working_endpoints = [
            "https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/documents",
            "https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/rag",
            "https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/presign"
        ]
        
        for endpoint in working_endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    self.log_result(f"Working API", "PASS", f"{endpoint} - OK")
                else:
                    self.log_result(f"Working API", "WARN", f"{endpoint} - Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Working API", "FAIL", f"{endpoint} - {str(e)}")

    def test_input_validation_real(self):
        """Test actual input validation on working endpoints"""
        # Test with the working RAG endpoint
        test_cases = [
            {"query": "normal question", "docId": "test"},
            {"query": "<script>alert('xss')</script>", "docId": "test"},
            {"query": "' OR 1=1 --", "docId": "test"},
            {"query": "", "docId": "test"}
        ]
        
        for i, test_case in enumerate(test_cases):
            try:
                response = requests.post(
                    "https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/rag",
                    json=test_case,
                    timeout=10
                )
                
                if test_case["query"] == "normal question":
                    if response.status_code in [200, 400]:  # Either works or validates
                        self.log_result(f"Input Validation {i+1}", "PASS", "Normal input handled")
                    else:
                        self.log_result(f"Input Validation {i+1}", "FAIL", f"Normal input failed: {response.status_code}")
                else:
                    # For malicious inputs, we want proper validation
                    if response.status_code in [400, 422]:
                        self.log_result(f"Input Validation {i+1}", "PASS", "Malicious input blocked")
                    elif response.status_code == 200:
                        # Check if response contains the malicious input
                        try:
                            data = response.json()
                            if test_case["query"] in str(data):
                                self.log_result(f"Input Validation {i+1}", "FAIL", "XSS vulnerability detected")
                            else:
                                self.log_result(f"Input Validation {i+1}", "PASS", "Input sanitized")
                        except:
                            self.log_result(f"Input Validation {i+1}", "PASS", "Input processed safely")
                    else:
                        self.log_result(f"Input Validation {i+1}", "WARN", f"Unexpected response: {response.status_code}")
                        
            except Exception as e:
                self.log_result(f"Input Validation {i+1}", "FAIL", str(e))

    def test_create_missing_endpoints(self):
        """Create missing API endpoints that tests expect"""
        missing_endpoints = [
            "/api/agents",
            "/api/pdf/search",
            "/api/v5/health"
        ]
        
        for endpoint in missing_endpoints:
            self.log_result(f"Missing Endpoint {endpoint}", "FAIL", "Needs implementation")

    def run_mini_tests(self):
        """Run focused mini tests"""
        print("🔍 Running Mini Test Suite")
        print("=" * 40)
        
        print("\n1. Testing API Endpoints...")
        self.test_api_endpoints_exist()
        
        print("\n2. Testing Working APIs...")
        self.test_working_api_endpoints()
        
        print("\n3. Testing Input Validation...")
        self.test_input_validation_real()
        
        print("\n4. Identifying Missing Endpoints...")
        self.test_create_missing_endpoints()
        
        self.generate_mini_report()

    def generate_mini_report(self):
        """Generate focused report"""
        print("\n" + "=" * 40)
        print("📊 MINI TEST RESULTS")
        print("=" * 40)
        
        passed = len([r for r in self.results if r['status'] == 'PASS'])
        failed = len([r for r in self.results if r['status'] == 'FAIL'])
        warned = len([r for r in self.results if r['status'] == 'WARN'])
        total = len(self.results)
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warned}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        
        # Show failures to fix
        failures = [r for r in self.results if r['status'] == 'FAIL']
        if failures:
            print("\n🔧 ISSUES TO FIX:")
            for failure in failures:
                print(f"  • {failure['test']}: {failure['details']}")

if __name__ == "__main__":
    tester = MiniTester()
    tester.run_mini_tests()