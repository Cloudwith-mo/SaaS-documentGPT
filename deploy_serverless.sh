#!/bin/bash

# Deploy SaaS-documentGPT v5 to serverless hosting (S3/CloudFront)
echo "🚀 Deploying Serverless SaaS-documentGPT v5"
echo "==========================================="

# Create production build
mkdir -p dist/

# Copy and optimize the main HTML file
cp web-app/public/documentgpt.html dist/index.html

# Update API endpoints to production URLs in the HTML
sed -i '' 's|https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod|https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod|g' dist/index.html

echo "✅ Production build ready in dist/"
echo ""
echo "🌐 Serverless Deployment Options:"
echo ""
echo "1. AWS S3 + CloudFront:"
echo "   aws s3 sync dist/ s3://documentgpt-io --delete"
echo "   aws cloudfront create-invalidation --distribution-id YOUR_ID --paths '/*'"
echo ""
echo "2. Netlify (drag & drop or CLI):"
echo "   netlify deploy --prod --dir=dist"
echo ""
echo "3. Vercel:"
echo "   vercel --prod dist/"
echo ""
echo "4. GitHub Pages:"
echo "   git subtree push --prefix dist origin gh-pages"
echo ""
echo "📁 Files ready for deployment:"
ls -la dist/
echo ""
echo "🔗 API Endpoints configured:"
echo "  ✅ https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod"
echo ""
echo "🎯 Your app will be live at https://documentgpt.io"