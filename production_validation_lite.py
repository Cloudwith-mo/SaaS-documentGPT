#!/usr/bin/env python3
"""
Production Validation Script for SaaS-documentGPT (Lite Version)
Comprehensive automated testing for production readiness
"""

import requests
import json
import time
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Any

class ProductionValidator:
    def __init__(self):
        self.results = []
        self.endpoints = {
            'health': 'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/health',
            'documents': 'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/documents',
            'rag': 'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/rag',
            'upload_url': 'https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/upload-url',
            'pdf_content': 'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/pdf-content'
        }
        
    def log_result(self, category: str, test: str, passed: bool, details: str = "", critical: bool = False):
        status = "✅ PASS" if passed else ("🚨 CRITICAL FAIL" if critical else "❌ FAIL")
        result = {
            "category": category,
            "test": test,
            "passed": passed,
            "critical": critical,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"{status} [{category}] {test}: {details}")
        
    def test_health_endpoints(self):
        """Test all health check endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        try:
            response = requests.get(self.endpoints['health'], timeout=10)
            passed = response.status_code == 200
            self.log_result("Health", "Main Health Check", passed, 
                          f"Status: {response.status_code}", critical=True)
        except Exception as e:
            self.log_result("Health", "Main Health Check", False, 
                          f"Error: {str(e)}", critical=True)
        
        # Test response time
        try:
            start = time.time()
            response = requests.get(self.endpoints['health'], timeout=5)
            duration = time.time() - start
            passed = duration < 2.0
            self.log_result("Performance", "Health Response Time", passed,
                          f"{duration:.2f}s (target: <2s)")
        except Exception as e:
            self.log_result("Performance", "Health Response Time", False, str(e))
    
    def test_api_security(self):
        """Test API security and authentication"""
        print("\n🔒 Testing API Security...")
        
        # Test CORS headers
        try:
            response = requests.options(self.endpoints['documents'])
            has_cors = 'Access-Control-Allow-Origin' in response.headers
            self.log_result("Security", "CORS Headers", has_cors,
                          f"CORS configured: {has_cors}")
        except Exception as e:
            self.log_result("Security", "CORS Headers", False, str(e))
        
        # Test input validation
        try:
            xss_payload = {"query": "<script>alert('xss')</script>"}
            response = requests.post(self.endpoints['rag'], json=xss_payload, timeout=10)
            passed = response.status_code < 500
            self.log_result("Security", "XSS Input Validation", passed,
                          f"Handled XSS payload: {response.status_code}")
        except Exception as e:
            self.log_result("Security", "XSS Input Validation", False, str(e))
    
    def test_document_workflow(self):
        """Test document upload and processing workflow"""
        print("\n📄 Testing Document Workflow...")
        
        # Test upload URL generation
        try:
            payload = {"fileName": "test.pdf", "fileType": "application/pdf"}
            response = requests.post(self.endpoints['upload_url'], 
                                   json=payload, timeout=10)
            has_upload_url = response.status_code == 200 and 'uploadUrl' in response.text
            self.log_result("Documents", "Upload URL Generation", has_upload_url,
                          f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Documents", "Upload URL Generation", False, str(e))
        
        # Test document listing
        try:
            response = requests.get(self.endpoints['documents'], timeout=10)
            passed = response.status_code == 200
            self.log_result("Documents", "Document Listing", passed,
                          f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Documents", "Document Listing", False, str(e))
    
    def test_ai_functionality(self):
        """Test AI and RAG functionality"""
        print("\n🤖 Testing AI Functionality...")
        
        # Test RAG endpoint
        try:
            payload = {"query": "What is this document about?", "document_id": "test"}
            response = requests.post(self.endpoints['rag'], 
                                   json=payload, timeout=30)
            passed = response.status_code in [200, 400]
            self.log_result("AI", "RAG Query Processing", passed,
                          f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("AI", "RAG Query Processing", False, str(e))
    
    def test_error_handling(self):
        """Test error handling and resilience"""
        print("\n⚠️ Testing Error Handling...")
        
        # Test malformed JSON
        try:
            response = requests.post(self.endpoints['rag'], 
                                   data="invalid json", 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            passed = 400 <= response.status_code < 500
            self.log_result("Error Handling", "Malformed JSON", passed,
                          f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Error Handling", "Malformed JSON", False, str(e))
    
    def test_performance_limits(self):
        """Test performance under load"""
        print("\n⚡ Testing Performance Limits...")
        
        def make_request():
            try:
                response = requests.get(self.endpoints['health'], timeout=5)
                return response.status_code == 200
            except:
                return False
        
        # Test concurrent requests
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            success_rate = sum(results) / len(results)
            passed = success_rate >= 0.8
            self.log_result("Performance", "Concurrent Requests", passed,
                          f"Success rate: {success_rate:.1%}")
        except Exception as e:
            self.log_result("Performance", "Concurrent Requests", False, str(e))
    
    def test_frontend_accessibility(self):
        """Test frontend accessibility"""
        print("\n🌐 Testing Frontend Accessibility...")
        
        # Test external dependencies
        try:
            response = requests.get('https://unpkg.com/lucide@latest/dist/umd/lucide.js', timeout=10)
            passed = response.status_code == 200
            self.log_result("Frontend", "External Dependencies", passed,
                          f"Lucide icons: {response.status_code}")
        except Exception as e:
            self.log_result("Frontend", "External Dependencies", False, str(e))
    
    def run_validation(self):
        """Run all validation tests"""
        print("🚀 Starting Production Validation for SaaS-documentGPT")
        print("=" * 60)
        
        self.test_health_endpoints()
        self.test_api_security()
        self.test_document_workflow()
        self.test_ai_functionality()
        self.test_error_handling()
        self.test_performance_limits()
        self.test_frontend_accessibility()
        
        self.generate_summary()
    
    def generate_summary(self):
        """Generate validation summary"""
        print("\n" + "=" * 60)
        print("📊 PRODUCTION VALIDATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        critical_failures = sum(1 for r in self.results if not r["passed"] and r["critical"])
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Critical Failures: {critical_failures}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Category breakdown
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0}
            categories[cat]["total"] += 1
            if result["passed"]:
                categories[cat]["passed"] += 1
        
        print(f"\n📈 Results by Category:")
        for cat, stats in categories.items():
            rate = (stats["passed"] / stats["total"]) * 100
            print(f"  {cat}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        
        # Failed tests
        failed_tests = [r for r in self.results if not r["passed"]]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                status = "🚨 CRITICAL" if test["critical"] else "⚠️ "
                print(f"  {status} [{test['category']}] {test['test']}: {test['details']}")
        
        # Production readiness
        print(f"\n🎯 Production Readiness Assessment:")
        if critical_failures > 0:
            print("🚨 NOT READY - Critical failures must be resolved")
        elif success_rate >= 90:
            print("✅ READY - System meets production standards")
        elif success_rate >= 80:
            print("⚠️ MOSTLY READY - Minor issues should be addressed")
        else:
            print("❌ NOT READY - Multiple issues need resolution")
        
        # Save report
        report = {
            "validation_date": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "critical_failures": critical_failures,
                "success_rate": success_rate
            },
            "results": self.results
        }
        
        with open('production_validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: production_validation_report.json")

def main():
    validator = ProductionValidator()
    validator.run_validation()

if __name__ == "__main__":
    main()