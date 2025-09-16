#!/usr/bin/env python3
"""Mini Test 3: Working Endpoints"""

import requests

def test_working_endpoints():
    print("🧪 Mini Test 3: Working Endpoints")
    
    endpoints = [
        'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/documents',
        'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/rag'
    ]
    
    results = []
    
    # Test documents endpoint
    try:
        response = requests.get(endpoints[0], timeout=10)
        passed = response.status_code == 200
        print(f"  Documents: {response.status_code} {'✅' if passed else '❌'}")
        results.append(passed)
    except Exception as e:
        print(f"  Documents: ERROR {e}")
        results.append(False)
    
    # Test RAG endpoint
    try:
        payload = {"query": "test", "document_id": "test"}
        response = requests.post(endpoints[1], json=payload, timeout=10)
        passed = response.status_code in [200, 400]
        print(f"  RAG: {response.status_code} {'✅' if passed else '❌'}")
        results.append(passed)
    except Exception as e:
        print(f"  RAG: ERROR {e}")
        results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"  Success Rate: {success_rate:.1f}%")
    return success_rate >= 100

if __name__ == "__main__":
    test_working_endpoints()