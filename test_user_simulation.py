#!/usr/bin/env python3
"""
Real User Simulation Test for DocumentGPT
Tests all features end-to-end like a real user would
"""

import requests
import json
import base64
import time

API_BASE = 'https://i1dy8i3692.execute-api.us-east-1.amazonaws.com/prod'

def test_journal_mode():
    """Test 1: Journal Mode - Live AI Assistant"""
    print("🧪 TEST 1: Journal Mode - Live AI Assistant")
    
    # Simulate user typing in journal
    journal_content = "Today I'm feeling overwhelmed with work. I have three big projects due this week and I'm not sure how to prioritize them. Maybe I should start with the most urgent one?"
    
    # Test live assistant
    response = requests.post(f'{API_BASE}/live-assist', json={
        'content': journal_content,
        'user_id': 'test-user'
    })
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Live Assistant Response:")
        for i, suggestion in enumerate(result.get('suggestions', []), 1):
            print(f"   {i}. {suggestion}")
    else:
        print(f"❌ Live Assistant Failed: {response.status_code} - {response.text}")
    
    # Test journal chat
    response = requests.post(f'{API_BASE}/chat', json={
        'messages': [{'role': 'user', 'content': f'[JOURNAL CONTEXT: {journal_content}] How can I better prioritize my work?'}],
        'user_email': 'test@documentgpt.io'
    })
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Journal Chat Response:")
        print(f"   {result['response'][:200]}...")
    else:
        print(f"❌ Journal Chat Failed: {response.status_code} - {response.text}")

def test_document_upload():
    """Test 2: Document Upload & Analysis"""
    print("\n🧪 TEST 2: Document Upload & Analysis")
    
    # Create a test document
    test_doc = """
    QUARTERLY BUSINESS REPORT - Q3 2024
    
    Revenue: $125,000
    Expenses: $87,500
    Net Profit: $37,500
    
    Key Achievements:
    - Launched new product line
    - Increased customer base by 25%
    - Improved operational efficiency
    
    Next Quarter Goals:
    - Expand to new markets
    - Hire 3 new team members
    - Launch marketing campaign
    """
    
    # Encode document
    encoded_content = base64.b64encode(test_doc.encode()).decode()
    
    # Upload document
    response = requests.post(f'{API_BASE}/upload', json={
        'filename': 'Q3_Report.txt',
        'file_content': encoded_content,
        'user_id': 'test-user'
    })
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Document Upload Success")
        vector_store_id = result.get('vector_store_id')
        
        # Test document chat
        time.sleep(2)  # Wait for processing
        
        response = requests.post(f'{API_BASE}/chat', json={
            'messages': [{'role': 'user', 'content': 'What was the net profit this quarter?'}],
            'vector_store_id': vector_store_id,
            'user_email': 'test@documentgpt.io'
        })
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Document Chat Response:")
            print(f"   {result['response'][:200]}...")
        else:
            print(f"❌ Document Chat Failed: {response.status_code} - {response.text}")
            
        return vector_store_id
    else:
        print(f"❌ Document Upload Failed: {response.status_code} - {response.text}")
        return None

def test_ai_agents(content):
    """Test 3: AI Agents"""
    print("\n🧪 TEST 3: AI Agents")
    
    agents = ['email', 'summary', 'sheets', 'calendar']
    
    for agent in agents:
        print(f"   Testing {agent} agent...")
        response = requests.post(f'{API_BASE}/agent', json={
            'agent_type': agent,
            'content': content,
            'user_email': 'test@documentgpt.io'
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ {agent.title()} Agent: {result['result'][:100]}...")
        else:
            print(f"   ❌ {agent.title()} Agent Failed: {response.status_code}")

def test_user_management():
    """Test 4: User Management"""
    print("\n🧪 TEST 4: User Management")
    
    # Get user profile
    response = requests.post(f'{API_BASE}/user', json={
        'action': 'get_profile',
        'user_id': 'test-user'
    })
    
    if response.status_code == 200:
        result = response.json()
        print("✅ User Profile Retrieved")
        print(f"   User ID: {result.get('user_id')}")
    else:
        print(f"❌ User Profile Failed: {response.status_code} - {response.text}")

def test_caching():
    """Test 5: Response Caching"""
    print("\n🧪 TEST 5: Response Caching")
    
    # Make same request twice
    message = "What is the meaning of productivity?"
    
    # First request
    start_time = time.time()
    response1 = requests.post(f'{API_BASE}/chat', json={
        'messages': [{'role': 'user', 'content': message}],
        'user_email': 'test@documentgpt.io'
    })
    time1 = time.time() - start_time
    
    # Second request (should be cached)
    start_time = time.time()
    response2 = requests.post(f'{API_BASE}/chat', json={
        'messages': [{'role': 'user', 'content': message}],
        'user_email': 'test@documentgpt.io'
    })
    time2 = time.time() - start_time
    
    if response1.status_code == 200 and response2.status_code == 200:
        result1 = response1.json()
        result2 = response2.json()
        
        if result2.get('cached'):
            print(f"✅ Caching Works! First: {time1:.2f}s, Cached: {time2:.2f}s")
        else:
            print(f"⚠️  Caching may not be working. Times: {time1:.2f}s, {time2:.2f}s")
    else:
        print("❌ Caching test failed")

def main():
    """Run all tests"""
    print("🚀 DocumentGPT End-to-End User Simulation")
    print("=" * 50)
    
    # Test 1: Journal Mode
    test_journal_mode()
    
    # Test 2: Document Upload
    vector_store_id = test_document_upload()
    
    # Test 3: AI Agents
    test_content = "I need to schedule a meeting with the team next Tuesday at 2 PM to discuss the Q3 results. Please send an email to team@company.com with the agenda."
    test_ai_agents(test_content)
    
    # Test 4: User Management
    test_user_management()
    
    # Test 5: Caching
    test_caching()
    
    print("\n" + "=" * 50)
    print("🏁 Test Suite Complete!")
    print("\nNext: Check https://documentgpt.io/backup.html to test UI")

if __name__ == "__main__":
    main()