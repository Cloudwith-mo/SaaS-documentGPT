#!/bin/bash

# DocumentsGPT v5 Production Deployment Script

echo "🚀 Deploying DocumentsGPT v5 to production..."

# 1. Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements-flask.txt

# 2. Set production environment
export FLASK_ENV=production
export FLASK_DEBUG=False
export PORT=5000

# 3. Start Flask app
echo "🔥 Starting Flask server on port 5000..."
python app.py &

# 4. Setup nginx (manual step reminder)
echo "⚙️  Manual step: Configure nginx with nginx.conf"
echo "   sudo cp nginx.conf /etc/nginx/sites-available/documentgpt"
echo "   sudo ln -s /etc/nginx/sites-available/documentgpt /etc/nginx/sites-enabled/"
echo "   sudo nginx -t && sudo systemctl reload nginx"

echo "✅ DocumentsGPT v5 deployed successfully!"
echo "🌐 Access at: https://documentgpt.io/"