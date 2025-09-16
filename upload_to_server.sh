#!/bin/bash

# Upload to documentgpt.io server
echo "🌐 Uploading to documentgpt.io server..."

# Check if dist directory exists
if [ ! -d "dist" ]; then
    echo "❌ dist/ directory not found. Run ./deploy_to_production.sh first"
    exit 1
fi

# Create deployment archive
echo "📦 Creating deployment archive..."
cd dist/
tar -czf ../documentgpt-v5-production.tar.gz *
cd ..

echo "✅ Created documentgpt-v5-production.tar.gz"
echo ""
echo "📋 Manual deployment steps for documentgpt.io:"
echo ""
echo "1. Upload the archive to your server:"
echo "   scp documentgpt-v5-production.tar.gz user@documentgpt.io:/var/www/"
echo ""
echo "2. Extract on server:"
echo "   ssh user@documentgpt.io"
echo "   cd /var/www/html"
echo "   tar -xzf ../documentgpt-v5-production.tar.gz"
echo ""
echo "3. Set permissions:"
echo "   chmod -R 644 *"
echo "   chmod 755 ."
echo ""
echo "4. Restart web server (if needed):"
echo "   sudo systemctl restart apache2  # or nginx"
echo ""
echo "🔧 Alternative: Use your hosting provider's file manager"
echo "   - Upload all files from dist/ directory"
echo "   - Ensure index.html is in the root directory"
echo ""
echo "🚀 Your SaaS-documentGPT v5 will be live at https://documentgpt.io"