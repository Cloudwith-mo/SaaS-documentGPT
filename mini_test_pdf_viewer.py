#!/usr/bin/env python3
import requests

def test_pdf_access():
    print("🔍 Mini Test 1: PDF Access Methods")
    print("=" * 40)
    
    # Test different ways to access uploaded PDFs
    test_urls = [
        "https://documentgpt-uploads-1757887191.s3.amazonaws.com/uploads/sample_bank_statement.pdf",
        "https://documentgpt.io/sample_bank_statement.pdf",
        "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/pdf/sample_bank_statement.pdf"
    ]
    
    for url in test_urls:
        try:
            response = requests.head(url)
            print(f"HEAD {url}: {response.status_code}")
            if response.status_code == 200:
                print(f"  Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                print(f"  Content-Length: {response.headers.get('Content-Length', 'Unknown')}")
        except Exception as e:
            print(f"HEAD {url}: ERROR - {e}")

def test_pdf_js_libraries():
    print("\n🔍 Mini Test 2: PDF.js Library Test")
    print("=" * 40)
    
    # Test if PDF.js CDN is accessible
    pdf_js_urls = [
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js",
        "https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.min.js"
    ]
    
    for url in pdf_js_urls:
        try:
            response = requests.head(url)
            print(f"HEAD {url}: {response.status_code}")
        except Exception as e:
            print(f"HEAD {url}: ERROR - {e}")

if __name__ == "__main__":
    test_pdf_access()
    test_pdf_js_libraries()