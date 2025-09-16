#!/usr/bin/env python3
"""
Final Production Validation - Comprehensive System Check
"""

import requests
import json
import time
from datetime import datetime

class FinalValidator:
    def __init__(self):
        self.results = []
        self.endpoints = {
            'health': 'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/health',
            'documents': 'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/documents',
            'rag': 'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/rag',
            'upload_url': 'https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/upload-url'
        }
        
    def log_result(self, test: str, passed: bool, details: str = "", critical: bool = False):
        status = "✅ PASS" if passed else ("🚨 CRITICAL" if critical else "❌ FAIL")
        self.results.append({
            "test": test,
            "passed": passed,
            "critical": critical,
            "details": details
        })
        print(f"{status} {test}: {details}")
        
    def test_comprehensive_health(self):
        """Comprehensive health check testing"""
        print("🔍 Testing System Health...")
        
        # Test main health endpoint
        try:
            response = requests.get(self.endpoints['health'], timeout=10)
            self.log_result("Health Endpoint", response.status_code == 200, 
                          f"Status: {response.status_code}", critical=True)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    has_required_fields = all(key in data for key in ['status', 'service'])
                    self.log_result("Health Response Format", has_required_fields,
                                  f"Contains required fields: {has_required_fields}")
                except:
                    self.log_result("Health Response Format", False, "Invalid JSON response")
                    
        except Exception as e:
            self.log_result("Health Endpoint", False, f"Error: {str(e)}", critical=True)
    
    def test_api_functionality(self):
        """Test core API functionality"""
        print("\n🔍 Testing API Functionality...")
        
        # Test document listing
        try:
            response = requests.get(self.endpoints['documents'], timeout=10)
            self.log_result("Document Listing", response.status_code == 200,
                          f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Document Listing", False, f"Error: {str(e)}")
        
        # Test RAG with proper validation
        try:
            payload = {"query": "Test query", "document_id": "test"}
            response = requests.post(self.endpoints['rag'], json=payload, timeout=15)
            # 400 is acceptable for missing document
            passed = response.status_code in [200, 400]
            self.log_result("RAG Processing", passed, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("RAG Processing", False, f"Error: {str(e)}")
        
        # Test upload URL generation
        try:
            payload = {"fileName": "test.pdf", "fileType": "application/pdf"}
            response = requests.post(self.endpoints['upload_url'], json=payload, timeout=10)
            passed = response.status_code == 200
            self.log_result("Upload URL Generation", passed, f"Status: {response.status_code}")
            
            if passed:
                try:
                    data = response.json()
                    has_upload_url = 'uploadUrl' in data
                    self.log_result("Upload URL Format", has_upload_url,
                                  f"Contains uploadUrl: {has_upload_url}")
                except:
                    self.log_result("Upload URL Format", False, "Invalid JSON response")
                    
        except Exception as e:
            self.log_result("Upload URL Generation", False, f"Error: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling improvements"""
        print("\n🔍 Testing Error Handling...")
        
        # Test malformed JSON handling
        try:
            response = requests.post(self.endpoints['rag'], 
                                   data="invalid json",
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            passed = 400 <= response.status_code < 500
            self.log_result("Malformed JSON Handling", passed,
                          f"Status: {response.status_code} (expected 4xx)")
        except Exception as e:
            self.log_result("Malformed JSON Handling", False, f"Error: {str(e)}")
        
        # Test missing required fields
        try:
            response = requests.post(self.endpoints['rag'], json={}, timeout=10)
            passed = response.status_code == 400
            self.log_result("Missing Fields Validation", passed,
                          f"Status: {response.status_code} (expected 400)")
        except Exception as e:
            self.log_result("Missing Fields Validation", False, f"Error: {str(e)}")
        
        # Test XSS protection
        try:
            payload = {"query": "<script>alert('xss')</script>", "document_id": "test"}
            response = requests.post(self.endpoints['rag'], json=payload, timeout=10)
            passed = response.status_code == 400
            self.log_result("XSS Protection", passed,
                          f"Status: {response.status_code} (expected 400)")
        except Exception as e:
            self.log_result("XSS Protection", False, f"Error: {str(e)}")
    
    def test_performance(self):
        """Test system performance"""
        print("\n🔍 Testing Performance...")
        
        # Test response times
        try:
            start = time.time()
            response = requests.get(self.endpoints['health'], timeout=5)
            duration = time.time() - start
            passed = duration < 2.0 and response.status_code == 200
            self.log_result("Response Time", passed, f"{duration:.2f}s (target: <2s)")
        except Exception as e:
            self.log_result("Response Time", False, f"Error: {str(e)}")
        
        # Test basic concurrency
        import concurrent.futures
        
        def make_request():
            try:
                response = requests.get(self.endpoints['documents'], timeout=10)
                return response.status_code == 200
            except:
                return False
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(make_request) for _ in range(5)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            success_rate = sum(results) / len(results)
            passed = success_rate >= 0.6  # 60% success rate
            self.log_result("Concurrent Requests", passed,
                          f"Success rate: {success_rate:.1%}")
        except Exception as e:
            self.log_result("Concurrent Requests", False, f"Error: {str(e)}")
    
    def test_security(self):
        """Test security measures"""
        print("\n🔍 Testing Security...")
        
        # Test CORS headers
        try:
            response = requests.options(self.endpoints['documents'])
            has_cors = 'Access-Control-Allow-Origin' in response.headers
            self.log_result("CORS Configuration", has_cors,
                          f"CORS headers present: {has_cors}")
        except Exception as e:
            self.log_result("CORS Configuration", False, f"Error: {str(e)}")
        
        # Test input validation
        try:
            # Test oversized payload
            large_query = "x" * 6000  # Over 5000 char limit
            payload = {"query": large_query, "document_id": "test"}
            response = requests.post(self.endpoints['rag'], json=payload, timeout=10)
            passed = response.status_code == 400
            self.log_result("Input Size Validation", passed,
                          f"Status: {response.status_code} (expected 400)")
        except Exception as e:
            self.log_result("Input Size Validation", False, f"Error: {str(e)}")
    
    def run_validation(self):
        """Run complete validation suite"""
        print("🚀 Final Production Validation for SaaS-documentGPT")
        print("=" * 60)
        
        self.test_comprehensive_health()
        self.test_api_functionality()
        self.test_error_handling()
        self.test_performance()
        self.test_security()
        
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generate final production readiness report"""
        print("\n" + "=" * 60)
        print("📊 FINAL PRODUCTION READINESS REPORT")
        print("=" * 60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        critical_failures = sum(1 for r in self.results if not r["passed"] and r["critical"])
        
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Critical Failures: {critical_failures}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Failed tests
        failed_tests = [r for r in self.results if not r["passed"]]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                status = "🚨 CRITICAL" if test["critical"] else "⚠️ "
                print(f"  {status} {test['test']}: {test['details']}")
        
        # Production readiness assessment
        print(f"\n🎯 Production Readiness Assessment:")
        if critical_failures > 0:
            print("🚨 NOT READY FOR PRODUCTION")
            print("   Critical health endpoint failures must be resolved")
        elif success_rate >= 90:
            print("✅ READY FOR PRODUCTION")
            print("   System meets production standards")
        elif success_rate >= 80:
            print("⚠️ MOSTLY READY FOR PRODUCTION")
            print("   Minor issues should be addressed but not blocking")
        else:
            print("❌ NOT READY FOR PRODUCTION")
            print("   Multiple issues need resolution")
        
        # Next steps
        print(f"\n💡 Immediate Next Steps:")
        if critical_failures > 0:
            print("1. Deploy updated Lambda functions to AWS")
            print("2. Verify API Gateway integration")
            print("3. Re-run validation")
        else:
            print("1. Monitor system performance in production")
            print("2. Set up automated health checks")
            print("3. Implement comprehensive logging")
        
        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total,
                "passed_tests": passed,
                "success_rate": success_rate,
                "critical_failures": critical_failures
            },
            "results": self.results
        }
        
        with open('final_validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: final_validation_report.json")

def main():
    validator = FinalValidator()
    validator.run_validation()

if __name__ == "__main__":
    main()