#!/usr/bin/env python3
"""
Mini Test Script - Quick validation of fixed endpoints
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        passed = response.status_code == 200 and response.json().get("status") == "ok"
        print(f"✅ Health: {response.status_code}" if passed else f"❌ Health: {response.status_code}")
        return passed
    except Exception as e:
        print(f"❌ Health: {str(e)}")
        return False

def test_agents():
    """Test agents API"""
    try:
        # GET
        response = requests.get(f"{BASE_URL}/api/agents")
        get_ok = response.status_code == 200 and isinstance(response.json(), list)
        
        # POST
        post_response = requests.post(f"{BASE_URL}/api/agents", json={"name": "Test Agent"})
        post_ok = post_response.status_code == 201
        
        passed = get_ok and post_ok
        print(f"✅ Agents: GET={get_ok}, POST={post_ok}" if passed else f"❌ Agents: GET={get_ok}, POST={post_ok}")
        return passed
    except Exception as e:
        print(f"❌ Agents: {str(e)}")
        return False

def test_pdf_search():
    """Test PDF search"""
    try:
        response = requests.post(f"{BASE_URL}/api/pdf/search", json={"query": "test"})
        data = response.json()
        matches = data.get("matches", [])
        bbox_valid = all(0 <= m["bbox"]["x"] <= 1 for m in matches if "bbox" in m)
        passed = response.status_code == 200 and len(matches) > 0 and bbox_valid
        print(f"✅ PDF Search: {len(matches)} matches, bbox valid" if passed else f"❌ PDF Search: {response.status_code}")
        return passed
    except Exception as e:
        print(f"❌ PDF Search: {str(e)}")
        return False

def test_debate_export():
    """Test debate export"""
    try:
        payload = {
            "consensus": "Test consensus",
            "debate_cols": {"Legal": ["Arg1"], "Finance": ["Arg2"]}
        }
        response = requests.post(f"{BASE_URL}/api/debate/export", json=payload)
        passed = response.status_code == 200 and "text/markdown" in response.headers.get("content-type", "")
        size = len(response.content)
        print(f"✅ Export: {size} bytes" if passed else f"❌ Export: {response.status_code}")
        return passed
    except Exception as e:
        print(f"❌ Export: {str(e)}")
        return False

def test_sse_stream():
    """Test SSE stream"""
    try:
        response = requests.get(f"{BASE_URL}/api/debate/stream", stream=True, timeout=10)
        if response.status_code != 200:
            print(f"❌ SSE: {response.status_code}")
            return False
        
        events = []
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("event:"):
                events.append(line.split(": ")[1])
            if len(events) >= 3:  # Get first few events
                break
        
        has_arg = "debate.argument" in events
        has_consensus = "debate.consensus" in events
        passed = has_arg and has_consensus
        print(f"✅ SSE: {len(events)} events, arg={has_arg}, consensus={has_consensus}" if passed else f"❌ SSE: {len(events)} events")
        return passed
    except Exception as e:
        print(f"❌ SSE: {str(e)}")
        return False

def main():
    print("🧪 Mini Test Suite - Quick Validation")
    print("=" * 40)
    
    tests = [
        ("Health", test_health),
        ("Agents", test_agents), 
        ("PDF Search", test_pdf_search),
        ("Export", test_debate_export),
        ("SSE Stream", test_sse_stream)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n🔍 Testing {name}...")
        result = test_func()
        results.append(result)
        time.sleep(0.5)
    
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Ready for full test suite.")
    else:
        print("🔧 Some tests failed. Check server logs.")

if __name__ == "__main__":
    main()