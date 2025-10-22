#!/usr/bin/env python3
"""Full app test simulating real user workflow"""
import requests
import json

API = "https://i1dy8i3692.execute-api.us-east-1.amazonaws.com/prod"
USER = "app-test-user"

print("=" * 60)
print("FULL APP TEST - Real User Simulation")
print("=" * 60)
print(f"User: {USER} (testing tier - unlimited)")
print()

# Test 1: Chat
print("1️⃣  Testing Chat...")
r = requests.post(f"{API}/chat", json={
    "user_id": USER,
    "messages": [{"role": "user", "content": "What is AI?"}]
})
print(f"   Status: {r.status_code}")
print(f"   Response: {r.json().get('response', 'ERROR')[:80]}...")
print()

# Test 2: Upload Document
print("2️⃣  Testing Document Upload...")
doc_content = """AAAI 2025 Presidential Panel Report
Artificial Intelligence has made significant progress in recent years.
Key topics include machine learning, neural networks, and ethical AI.
The conference discussed future directions and challenges in AI research."""

r = requests.post(f"{API}/upload", json={
    "user_id": USER,
    "filename": "aaai-report.txt",
    "content": doc_content
})
print(f"   Status: {r.status_code}")
data = r.json()
print(f"   Doc ID: {data.get('doc_id')}")
print(f"   Questions: {len(data.get('questions', []))} generated")
if data.get('questions'):
    print(f"   Sample Q: {data['questions'][0][:60]}...")
print()

# Test 3: Summary Agent
print("3️⃣  Testing Summary Agent...")
r = requests.post(f"{API}/agent", json={
    "user_id": USER,
    "agent_type": "summary",
    "content": doc_content
})
print(f"   Status: {r.status_code}")
result = r.json()
print(f"   Result: {result.get('status')}")
if result.get('summary'):
    print(f"   Summary: {result['summary'][:100]}...")
print()

# Test 4: Export Agent
print("4️⃣  Testing Export Agent...")
r = requests.post(f"{API}/agent", json={
    "user_id": USER,
    "agent_type": "export",
    "content": "Test export content",
    "params": {"format": "txt"}
})
print(f"   Status: {r.status_code}")
result = r.json()
print(f"   Result: {result.get('status')}")
print(f"   URL: {result.get('download_url', 'N/A')[:60]}...")
print()

# Test 5: Calendar Agent
print("5️⃣  Testing Calendar Agent...")
r = requests.post(f"{API}/agent", json={
    "user_id": USER,
    "agent_type": "calendar",
    "params": {
        "title": "AI Conference",
        "date": "20250215",
        "time": "10:00"
    }
})
print(f"   Status: {r.status_code}")
result = r.json()
print(f"   Result: {result.get('status')}")
print(f"   iCal: {'Generated' if result.get('ical_data') else 'Failed'}")
print()

# Test 6: Save Agent
print("6️⃣  Testing Save Agent...")
r = requests.post(f"{API}/agent", json={
    "user_id": USER,
    "agent_type": "save",
    "content": "Document to save",
    "params": {"title": "saved-doc.txt"}
})
print(f"   Status: {r.status_code}")
result = r.json()
print(f"   Result: {result.get('status')}")
print(f"   Doc ID: {result.get('doc_id', 'N/A')}")
print()

# Test 7: Email Agent (will fail without SES)
print("7️⃣  Testing Email Agent...")
r = requests.post(f"{API}/agent", json={
    "user_id": USER,
    "agent_type": "email",
    "params": {
        "to": "test@example.com",
        "subject": "Test",
        "body": "Test email"
    }
})
print(f"   Status: {r.status_code}")
result = r.json()
print(f"   Result: {result.get('status')}")
print(f"   Message: {result.get('message', 'N/A')[:60]}...")
print()

# Test 8: Usage Stats
print("8️⃣  Checking Usage Stats...")
r = requests.get(f"{API}/usage?user_id={USER}")
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   Plan: {data.get('plan')}")
    usage = data.get('usage', {})
    print(f"   Chats: {usage.get('chats_used', 0)}")
    print(f"   Docs: {usage.get('documents_uploaded', 0)}")
    print(f"   Agents: {usage.get('agents_used', 0)}")
print()

print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
