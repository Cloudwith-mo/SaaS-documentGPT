#!/bin/bash
# DocumentGPT Deployment Workflow

echo "🚀 DocumentGPT Deployment Workflow"
echo "=================================="

case "$1" in
  "dev-to-staging")
    echo "📋 Copying DEV → STAGING..."
    cp ../web/backup.html ../web/staging-v2.html
    gzip -c ../web/staging-v2.html | aws s3 cp - s3://documentgpt-website-prod/staging-v2.html --content-type "text/html" --content-encoding "gzip" --cache-control "max-age=3600"
    echo "✅ Staging updated: https://documentgpt.io/staging-v2.html"
    ;;
  
  "staging-to-prod")
    echo "🎯 Copying STAGING → PROD..."
    cp ../web/staging-v2.html ../web/app.html
    gzip -c ../web/app.html | aws s3 cp - s3://documentgpt-website-prod/app.html --content-type "text/html" --content-encoding "gzip" --cache-control "max-age=3600"
    aws cloudfront create-invalidation --distribution-id E2O361IH9ALLK6 --paths "/app.html" --query 'Invalidation.Id' --output text
    echo "✅ Production updated: https://documentgpt.io/app.html"
    ;;
  
  "dev-to-prod")
    echo "⚡ Direct DEV → PROD (skip staging)..."
    cp ../web/backup.html ../web/app.html
    gzip -c ../web/app.html | aws s3 cp - s3://documentgpt-website-prod/app.html --content-type "text/html" --content-encoding "gzip" --cache-control "max-age=3600"
    aws cloudfront create-invalidation --distribution-id E2O361IH9ALLK6 --paths "/app.html" --query 'Invalidation.Id' --output text
    echo "✅ Production updated: https://documentgpt.io/app.html"
    ;;
  
  "sync-all")
    echo "🔄 Syncing DEV → STAGING → PROD..."
    cp ../web/backup.html ../web/staging-v2.html
    cp ../web/backup.html ../web/app.html
    gzip -c ../web/staging-v2.html | aws s3 cp - s3://documentgpt-website-prod/staging-v2.html --content-type "text/html" --content-encoding "gzip" --cache-control "max-age=3600"
    gzip -c ../web/app.html | aws s3 cp - s3://documentgpt-website-prod/app.html --content-type "text/html" --content-encoding "gzip" --cache-control "max-age=3600"
    aws cloudfront create-invalidation --distribution-id E2O361IH9ALLK6 --paths "/staging-v2.html" "/app.html" --query 'Invalidation.Id' --output text
    echo "✅ All environments synced!"
    ;;
  
  *)
    echo "Usage: ./deploy-workflow.sh [command]"
    echo ""
    echo "Commands:"
    echo "  dev-to-staging   Copy backup.html → staging-v2.html"
    echo "  staging-to-prod  Copy staging-v2.html → app.html"
    echo "  dev-to-prod      Copy backup.html → app.html (skip staging)"
    echo "  sync-all         Sync all environments to match dev"
    echo ""
    echo "URLs:"
    echo "  Dev:     https://documentgpt.io/backup.html"
    echo "  Staging: https://documentgpt.io/staging-v2.html"
    echo "  Prod:    https://documentgpt.io/app.html"
    ;;
esac