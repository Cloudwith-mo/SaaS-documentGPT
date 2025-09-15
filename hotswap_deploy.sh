#!/bin/bash
# Hot-swap deployment - replace running version with light theme UI

echo "🔄 Hot-swapping DocumentsGPT to light theme..."

# Stop current process
pkill -f "python.*app.py" || echo "No existing process found"

# Get latest code
git pull origin main

# Install/update dependencies
pip install -r requirements-flask.txt

# Start new version in background
nohup python app.py > app.log 2>&1 &

echo "✅ Hot-swap complete! Light theme now live at https://documentgpt.io/"
echo "📋 Check logs: tail -f app.log"