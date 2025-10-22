#!/bin/bash
# Production deployment script

set -e

echo "🚀 DocumentGPT Production Deployment"
echo "===================================="
echo ""

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "📝 Uncommitted changes detected. Creating commit..."
    echo ""
    echo "What changed? (brief description):"
    read -r COMMIT_MSG
    
    git add .
    git commit -m "$COMMIT_MSG"
    echo "✅ Changes committed"
    echo ""
else
    echo "✅ No uncommitted changes"
    echo ""
fi

echo "📦 Deploying to PRODUCTION..."
aws s3 cp ../web/app.html s3://documentgpt-website-prod/app.html --content-type text/html --cache-control "max-age=0, no-cache"
aws cloudfront create-invalidation --distribution-id E2O361IH9ALLK6 --paths "/app.html"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🧪 MANUAL TEST CHECKLIST:"
echo "========================"
echo "1. Open: https://documentgpt.io/app.html"
echo "2. Upload a PDF document"
echo "3. Ask: 'What are the key points?'"
echo "4. Verify: AI responds with document summary"
echo ""
echo "Did the test pass? (y/n):"
read -r TEST_RESULT

if [[ $TEST_RESULT == "y" ]]; then
    echo "✅ Test passed! Deployment successful 🎉"
    git tag "deploy-$(date +%Y%m%d-%H%M%S)"
    echo "📌 Tagged deployment"
else
    echo "⚠️  Test failed! Consider rolling back"
    echo "Rollback command: git revert HEAD"
fi
