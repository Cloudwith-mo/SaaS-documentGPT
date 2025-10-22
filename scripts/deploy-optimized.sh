#!/bin/bash

# Deploy optimized DocumentGPT with compression and caching

echo "🚀 Deploying optimized DocumentGPT..."

# 1. Compress HTML/CSS/JS with gzip
echo "📦 Compressing files..."
gzip -9 -k ../web/backup.html
gzip -9 -k ../web/index.html
gzip -9 -k ../web/landing-page.html

# 2. Upload to S3 with compression and caching headers
echo "☁️  Uploading to S3 with cache headers..."

# HTML files - 1 hour cache
aws s3 cp ../web/backup.html.gz s3://documentgpt-website-prod/backup.html \
  --content-encoding gzip \
  --content-type "text/html" \
  --cache-control "public, max-age=3600" \
  --metadata-directive REPLACE

aws s3 cp ../web/index.html.gz s3://documentgpt-website-prod/index.html \
  --content-encoding gzip \
  --content-type "text/html" \
  --cache-control "public, max-age=3600" \
  --metadata-directive REPLACE

aws s3 cp ../web/landing-page.html.gz s3://documentgpt-website-prod/landing-page.html \
  --content-encoding gzip \
  --content-type "text/html" \
  --cache-control "public, max-age=3600" \
  --metadata-directive REPLACE

# 3. Clean up gzip files
rm ../web/*.gz

# 4. Deploy Lambda function
echo "⚡ Deploying Lambda function..."
cd lambda
zip -r function.zip simple_handler.py
aws lambda update-function-code \
  --function-name docgpt-chat \
  --zip-file fileb://function.zip
rm function.zip
cd ..

# 5. Create CloudFront distribution (if not exists)
echo "🌐 Setting up CloudFront CDN..."
DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='DocumentGPT CloudFront CDN for static files'].Id" --output text)

if [ -z "$DISTRIBUTION_ID" ]; then
  echo "Creating new CloudFront distribution..."
  aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
  echo "✅ CloudFront distribution created! Update DNS to point to CloudFront domain."
else
  echo "✅ CloudFront distribution exists: $DISTRIBUTION_ID"
  echo "Invalidating cache..."
  aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Performance optimizations applied:"
echo "  ✓ Removed unused Lumina features (focus horizon, active block)"
echo "  ✓ Added render() caching - skips if doc unchanged"
echo "  ✓ DynamoDB cache for chat responses (1 hour TTL)"
echo "  ✓ Using gpt-4o-mini for faster responses"
echo "  ✓ Gzip compression enabled (HTML/CSS/JS)"
echo "  ✓ Browser caching headers set (1 hour HTML, 7 days assets)"
echo "  ✓ CloudFront CDN for global edge caching"
echo ""
echo "🔗 Production: https://documentgpt.io/"
echo "🔗 Development: https://documentgpt.io/backup.html"
