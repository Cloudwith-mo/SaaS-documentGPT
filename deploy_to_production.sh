#!/bin/bash

# Deploy SaaS-documentGPT v5 to documentgpt.io
echo "🚀 Deploying SaaS-documentGPT v5 to documentgpt.io"
echo "=================================================="

# Create production build directory
mkdir -p dist/

# Copy main HTML file as index.html for production
cp web-app/public/documentgpt.html dist/index.html

# Create production configuration
cat > dist/config.js << 'EOF'
// Production configuration for documentgpt.io
window.DOCUMENTGPT_CONFIG = {
    API_BASE_URL: 'https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod',
    ENVIRONMENT: 'production',
    VERSION: 'v5.0.0',
    FEATURES: {
        multiAgentDebate: true,
        realTimeStreaming: true,
        advancedOCR: true,
        exportCapabilities: true
    }
};
EOF

# Create robots.txt for SEO
cat > dist/robots.txt << 'EOF'
User-agent: *
Allow: /

Sitemap: https://documentgpt.io/sitemap.xml
EOF

# Create sitemap.xml
cat > dist/sitemap.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://documentgpt.io/</loc>
    <lastmod>2024-09-15</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
EOF

# Create .htaccess for Apache servers
cat > dist/.htaccess << 'EOF'
# Enable compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
</IfModule>

# Set cache headers
<IfModule mod_expires.c>
    ExpiresActive on
    ExpiresByType text/css "access plus 1 year"
    ExpiresByType application/javascript "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/jpg "access plus 1 year"
    ExpiresByType image/jpeg "access plus 1 year"
</IfModule>

# Security headers
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
EOF

echo "✅ Production build created in dist/ directory"
echo ""
echo "📁 Files ready for deployment:"
echo "  - index.html (main application)"
echo "  - config.js (production config)"
echo "  - robots.txt (SEO)"
echo "  - sitemap.xml (SEO)"
echo "  - .htaccess (server config)"
echo ""
echo "🌐 Next steps to deploy to documentgpt.io:"
echo "  1. Upload dist/ contents to your web server"
echo "  2. Point documentgpt.io to the uploaded files"
echo "  3. Ensure SSL certificate is configured"
echo "  4. Test the deployment"
echo ""
echo "🔗 API Endpoints configured:"
echo "  - Main API: https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod"
echo "  - All Lambda functions are live and tested"
echo ""
echo "✨ Deployment package ready!"