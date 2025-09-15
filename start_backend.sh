#!/bin/bash
echo "🚀 Starting DocumentsGPT v5 Backend..."
cd /Users/muhammadadeyemi/documentgpt.io/SaaS-documentGPT
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors
python3 app_v5.py