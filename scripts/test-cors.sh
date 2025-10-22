#!/bin/bash

echo "🧪 Testing CORS and API functionality..."
echo ""

# Test OPTIONS (preflight)
echo "1️⃣ Testing OPTIONS preflight request:"
curl -s -X OPTIONS https://i1dy8i3692.execute-api.us-east-1.amazonaws.com/prod/chat \
  -H "Origin: https://documentgpt.io" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  -I | grep -i "access-control"

echo ""
echo "2️⃣ Testing POST request (guest user):"
curl -s -X POST https://i1dy8i3692.execute-api.us-east-1.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -H "Origin: https://documentgpt.io" \
  -d '{"user_id":"guest_test123","messages":[{"role":"user","content":"Hello"}]}' \
  | jq -r '.response // .error' | head -c 100

echo ""
echo ""
echo "✅ If you see CORS headers and a response above, the API is working!"
echo "🌐 Test in browser: https://documentgpt.io/backup.html"
