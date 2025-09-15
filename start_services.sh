#!/bin/bash
# Start all required services

echo "Starting API server on port 8080..."
python3 api_server.py &
API_PID=$!

echo "Starting AWS mock services on port 8081..."
python3 mock_aws_services.py &
AWS_PID=$!

echo "Services started:"
echo "API Server PID: $API_PID"
echo "AWS Mock PID: $AWS_PID"

# Wait for services to start
sleep 2

echo "Testing services..."
curl -s http://localhost:8080/api/agents > /dev/null && echo "✅ API Server running"
curl -s http://localhost:8081/aws/lambda/test > /dev/null && echo "✅ AWS Mock running"

echo "Services ready for testing!"
echo "To stop: kill $API_PID $AWS_PID"