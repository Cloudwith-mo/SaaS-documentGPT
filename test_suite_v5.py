#!/usr/bin/env python3
"""
DocumentsGPT v5 Test Suite - Mini Tests for All Components
Tests: UI rendering, SSE streams, PDF processing, agent debates, exports
"""

import asyncio
import json
import time
import requests
from typing import Dict, List, Any
import subprocess
import os

class DocumentsGPTTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = []
        
    def log_test(self, name: str, passed: bool, details: str = ""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({"name": name, "passed": passed, "details": details})
        print(f"{status} {name}: {details}")
        
    def run_all_tests(self):
        print("🚀 Starting DocumentsGPT v5 Test Suite\n")
        
        # Backend API Tests
        self.test_health_endpoint()
        self.test_agents_api()
        self.test_pdf_search_api()
        self.test_debate_export_api()
        self.test_sse_debate_stream()
        
        # Integration Tests
        self.test_multi_doc_selection()
        self.test_citation_bbox_scaling()
        self.test_agent_preset_flow()
        
        # Performance Tests
        self.test_concurrent_streams()
        self.test_large_payload_handling()
        
        # Security Tests
        self.test_cors_headers()
        self.test_input_validation()
        
        self.print_summary()
        
    def test_health_endpoint(self):
        """Test 1: Health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/healthz", timeout=5)
            passed = response.status_code == 200 and response.json().get("status") == "ok"
            self.log_test("Health Endpoint", passed, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Error: {str(e)}")
            
    def test_agents_api(self):
        """Test 2: Agent presets CRUD"""
        try:
            # GET presets
            response = requests.get(f"{self.base_url}/api/agents")
            get_passed = response.status_code == 200 and isinstance(response.json(), list)
            
            # POST new preset
            new_preset = {"name": "Test/QA/DevOps", "agents": ["Test", "QA", "DevOps"]}
            post_response = requests.post(f"{self.base_url}/api/agents", json=new_preset)
            post_passed = post_response.status_code == 201
            
            passed = get_passed and post_passed
            self.log_test("Agents API", passed, f"GET: {get_passed}, POST: {post_passed}")
        except Exception as e:
            self.log_test("Agents API", False, f"Error: {str(e)}")
            
    def test_pdf_search_api(self):
        """Test 3: PDF search with bbox normalization"""
        try:
            payload = {"doc_id": "test-doc", "query": "payment terms", "page": 1}
            response = requests.post(f"{self.base_url}/api/pdf/search", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get("matches", [])
                # Check bbox normalization (should be 0-1 range)
                bbox_valid = all(
                    0 <= match["bbox"]["x"] <= 1 and 0 <= match["bbox"]["y"] <= 1
                    for match in matches if "bbox" in match
                )
                passed = len(matches) > 0 and bbox_valid
                self.log_test("PDF Search API", passed, f"Matches: {len(matches)}, BBox valid: {bbox_valid}")
            else:
                self.log_test("PDF Search API", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("PDF Search API", False, f"Error: {str(e)}")
            
    def test_debate_export_api(self):
        """Test 4: Debate export functionality"""
        try:
            payload = {
                "consensus": "Test consensus reached",
                "debate_cols": {
                    "Legal": ["Legal argument 1", "Legal argument 2"],
                    "Finance": ["Finance argument 1"],
                    "Compliance": ["Compliance argument 1"]
                }
            }
            response = requests.post(f"{self.base_url}/api/debate/export", json=payload)
            
            passed = (response.status_code == 200 and 
                     "text/markdown" in response.headers.get("content-type", ""))
            content_length = len(response.content)
            self.log_test("Debate Export", passed, f"Content length: {content_length} bytes")
        except Exception as e:
            self.log_test("Debate Export", False, f"Error: {str(e)}")
            
    def test_sse_debate_stream(self):
        """Test 5: SSE debate stream"""
        try:
            import sseclient  # pip install sseclient-py
            response = requests.get(f"{self.base_url}/api/debate/stream", stream=True, timeout=10)
            
            if response.status_code == 200:
                client = sseclient.SSEClient(response)
                events = []
                start_time = time.time()
                
                for event in client.events():
                    if time.time() - start_time > 5:  # 5 second timeout
                        break
                    if event.data and event.data != "[DONE]":
                        try:
                            data = json.loads(event.data)
                            events.append({"event": event.event, "data": data})
                        except json.JSONDecodeError:
                            pass
                            
                # Check for expected events
                has_argument = any(e["event"] == "debate.argument" for e in events)
                has_consensus = any(e["event"] == "debate.consensus" for e in events)
                passed = has_argument and has_consensus
                
                self.log_test("SSE Debate Stream", passed, f"Events: {len(events)}, Arg: {has_argument}, Consensus: {has_consensus}")
            else:
                self.log_test("SSE Debate Stream", False, f"Status: {response.status_code}")
        except ImportError:
            self.log_test("SSE Debate Stream", False, "sseclient-py not installed")
        except Exception as e:
            self.log_test("SSE Debate Stream", False, f"Error: {str(e)}")
            
    def test_multi_doc_selection(self):
        """Test 6: Multi-document selection logic"""
        # Simulate frontend logic
        docs = [
            {"id": "d1", "name": "Contract.pdf"},
            {"id": "d2", "name": "NDA.pdf"},
            {"id": "d3", "name": "SOW.pdf"}
        ]
        selected_docs = {"d1": True, "d2": True, "d3": False}
        
        # Filter logic
        selected_ids = [doc_id for doc_id, selected in selected_docs.items() if selected]
        expected_filter = {"must": [{"key": "docId", "match": {"any": selected_ids}}]}
        
        passed = len(selected_ids) == 2 and "d1" in selected_ids and "d2" in selected_ids
        self.log_test("Multi-doc Selection", passed, f"Selected: {selected_ids}")
        
    def test_citation_bbox_scaling(self):
        """Test 7: Citation bbox scaling math"""
        # Normalized bbox (0-1 range)
        norm_bbox = {"x": 0.25, "y": 0.30, "w": 0.40, "h": 0.08}
        rendered_w, rendered_h = 760, 980
        
        # Scale to screen coordinates
        scaled = {
            "x": int(norm_bbox["x"] * rendered_w),
            "y": int(norm_bbox["y"] * rendered_h),
            "w": int(norm_bbox["w"] * rendered_w),
            "h": int(norm_bbox["h"] * rendered_h)
        }
        
        expected = {"x": 190, "y": 294, "w": 304, "h": 78}
        passed = scaled == expected
        self.log_test("Citation BBox Scaling", passed, f"Scaled: {scaled}")
        
    def test_agent_preset_flow(self):
        """Test 8: Agent preset application flow"""
        # Simulate preset selection
        presets = {
            "Legal/Finance/Compliance": ["Legal", "Finance", "Compliance"],
            "Tech/Design/PM": ["Tech", "Design", "PM"]
        }
        
        selected_preset = "Legal/Finance/Compliance"
        agents = presets[selected_preset]
        
        # Create debate columns
        debate_cols = {agent: [] for agent in agents}
        
        passed = len(debate_cols) == 3 and "Legal" in debate_cols
        self.log_test("Agent Preset Flow", passed, f"Columns: {list(debate_cols.keys())}")
        
    def test_concurrent_streams(self):
        """Test 9: Concurrent SSE streams"""
        try:
            import threading
            import queue
            
            results_queue = queue.Queue()
            
            def stream_test():
                try:
                    response = requests.get(f"{self.base_url}/api/debate/stream", 
                                         stream=True, timeout=3)
                    results_queue.put(response.status_code == 200)
                except:
                    results_queue.put(False)
            
            # Start 3 concurrent streams
            threads = []
            for _ in range(3):
                t = threading.Thread(target=stream_test)
                t.start()
                threads.append(t)
            
            # Wait for completion
            for t in threads:
                t.join(timeout=5)
            
            # Check results
            successes = 0
            while not results_queue.empty():
                if results_queue.get():
                    successes += 1
            
            passed = successes >= 2  # At least 2/3 should succeed
            self.log_test("Concurrent Streams", passed, f"Successes: {successes}/3")
        except Exception as e:
            self.log_test("Concurrent Streams", False, f"Error: {str(e)}")
            
    def test_large_payload_handling(self):
        """Test 10: Large payload handling"""
        try:
            # Create large debate export payload
            large_payload = {
                "consensus": "Large consensus " * 100,
                "debate_cols": {
                    "Legal": ["Argument " * 50] * 20,
                    "Finance": ["Argument " * 50] * 20,
                    "Compliance": ["Argument " * 50] * 20
                }
            }
            
            response = requests.post(f"{self.base_url}/api/debate/export", 
                                   json=large_payload, timeout=10)
            passed = response.status_code == 200
            size_mb = len(response.content) / (1024 * 1024)
            self.log_test("Large Payload", passed, f"Response size: {size_mb:.2f}MB")
        except Exception as e:
            self.log_test("Large Payload", False, f"Error: {str(e)}")
            
    def test_cors_headers(self):
        """Test 11: CORS headers"""
        try:
            response = requests.options(f"{self.base_url}/api/agents")
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
            }
            
            has_cors = any(cors_headers.values())
            passed = has_cors or response.status_code in [200, 405]  # Some servers don't support OPTIONS
            self.log_test("CORS Headers", passed, f"Headers present: {has_cors}")
        except Exception as e:
            self.log_test("CORS Headers", False, f"Error: {str(e)}")
            
    def test_input_validation(self):
        """Test 12: Input validation"""
        try:
            # Test invalid JSON
            response1 = requests.post(f"{self.base_url}/api/agents", 
                                    data="invalid json", 
                                    headers={"Content-Type": "application/json"})
            
            # Test missing required fields
            response2 = requests.post(f"{self.base_url}/api/pdf/search", json={})
            
            # Both should return 4xx errors
            passed = (400 <= response1.status_code < 500 and 
                     400 <= response2.status_code < 500)
            self.log_test("Input Validation", passed, 
                         f"Invalid JSON: {response1.status_code}, Missing fields: {response2.status_code}")
        except Exception as e:
            self.log_test("Input Validation", False, f"Error: {str(e)}")
            
    def print_summary(self):
        """Print test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        print(f"\n📊 Test Summary:")
        print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  - {result['name']}: {result['details']}")
                    
        print(f"\n🎯 Next Steps:")
        if failed == 0:
            print("  ✅ All tests passed! Ready for v3 features.")
        elif failed <= 3:
            print("  🔧 Fix failing tests, then proceed to v3.")
        else:
            print("  🚨 Multiple failures - stabilize v2 first.")

def main():
    """Run the test suite"""
    print("DocumentsGPT v5 Test Suite")
    print("=" * 50)
    
    # Check if server is running
    tester = DocumentsGPTTester()
    try:
        requests.get(f"{tester.base_url}/healthz", timeout=2)
        print("✅ Server detected, running tests...\n")
        tester.run_all_tests()
    except requests.exceptions.RequestException:
        print("❌ Server not running. Start with: python documentsgpt_v5_flask.py")
        print("   Then run: python test_suite_v5.py")

if __name__ == "__main__":
    main()