#!/usr/bin/env python3
import requests

def test_document_content_api():
    print("🔍 Mini Test 3: Document Content API")
    print("=" * 40)
    
    # Test if there's an API to get document content
    api_endpoints = [
        "/documents",
        "/pdf/content",
        "/api/documents",
        "/api/pdf/content"
    ]
    
    base_url = "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod"
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            print(f"GET {endpoint}: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Response keys: {list(data.keys())}")
        except Exception as e:
            print(f"GET {endpoint}: ERROR - {e}")

def test_simple_pdf_viewer():
    print("\n🔍 Mini Test 4: Simple PDF Viewer Options")
    print("=" * 40)
    
    # Test simple alternatives
    print("Option 1: PDF.js embed")
    print("Option 2: Google Docs viewer")
    print("Option 3: Text-based preview")
    print("Option 4: Document summary")

if __name__ == "__main__":
    test_document_content_api()
    test_simple_pdf_viewer()