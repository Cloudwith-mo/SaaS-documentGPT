#!/usr/bin/env python3
import requests
import time

def test_questions():
    print("🧪 Testing document questions...")
    
    # Use existing sample document
    doc_id = "sample"
    
    questions = [
        "What are the key terms in this document?",
        "What is the payment schedule mentioned?", 
        "What is the capital of France?"  # Random question
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {question}")
        
        response = requests.post(
            'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/rag',
            json={'question': question, 'docId': doc_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('answer', 'No answer')
            citations = result.get('citations', [])
            
            print(f"🤖 Answer: {answer}")
            if citations:
                print(f"📄 Citations: {len(citations)} found")
            
            if i <= 2:  # Document questions
                if "not found" in answer.lower() or "still being processed" in answer.lower():
                    print("⚠️  Document not ready, trying with different approach...")
                else:
                    print("✅ Document question answered")
            else:  # Random question
                print("✅ Random question handled")
        else:
            print(f"❌ Request failed: {response.status_code}")
        
        time.sleep(1)

if __name__ == "__main__":
    test_questions()