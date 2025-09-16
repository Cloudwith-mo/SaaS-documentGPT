#!/usr/bin/env python3
import requests

def test_final_pdf_viewer():
    print("🔍 Final Test: PDF Content Viewer")
    print("=" * 40)
    
    # Test the new PDF content endpoint
    test_docs = ["sample_doc", "sample_bank_statement", "doc_123"]
    
    for doc_id in test_docs:
        try:
            response = requests.get(f"https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/pdf-content/{doc_id}")
            print(f"GET /pdf-content/{doc_id}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content_preview = data.get('content', '')[:100] + '...' if len(data.get('content', '')) > 100 else data.get('content', '')
                print(f"  Content: {content_preview}")
                print(f"  Pages: {data.get('pages', 'Unknown')}")
            else:
                print(f"  Error: {response.text}")
        except Exception as e:
            print(f"GET /pdf-content/{doc_id}: ERROR - {e}")
        print()

if __name__ == "__main__":
    test_final_pdf_viewer()