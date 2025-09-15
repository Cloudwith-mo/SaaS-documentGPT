#!/bin/bash

# DocumentGPT Setup Script
# This script automates the creation of AWS Cognito User Pool, domain, S3 bucket, and updates the HTML

set -e

echo "🚀 DocumentGPT Setup Script"
echo "=========================="

# Configuration
REGION="us-east-1"
USER_POOL_NAME="DocumentGPT-Users"
APP_CLIENT_NAME="DocumentGPT-Web"
DOMAIN_PREFIX="documentgpt-$(date +%s)"
BUCKET_NAME="documentgpt-uploads-$(date +%s)"
REDIRECT_URI="https://documentgpt.io/"
API_BASE_URL="https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod"

echo "📋 Configuration:"
echo "  Region: $REGION"
echo "  User Pool: $USER_POOL_NAME"
echo "  Domain Prefix: $DOMAIN_PREFIX"
echo "  Bucket: $BUCKET_NAME"
echo "  Redirect URI: $REDIRECT_URI"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI configured"

# Create User Pool
echo "🔐 Creating Cognito User Pool..."
USER_POOL_ID=$(aws cognito-idp create-user-pool \
    --pool-name "$USER_POOL_NAME" \
    --region "$REGION" \
    --policies '{
        "PasswordPolicy": {
            "MinimumLength": 8,
            "RequireUppercase": false,
            "RequireLowercase": false,
            "RequireNumbers": false,
            "RequireSymbols": false
        }
    }' \
    --auto-verified-attributes email \
    --username-attributes email \
    --query 'UserPool.Id' \
    --output text)

echo "✅ User Pool created: $USER_POOL_ID"

# Create App Client
echo "📱 Creating App Client..."
CLIENT_ID=$(aws cognito-idp create-user-pool-client \
    --user-pool-id "$USER_POOL_ID" \
    --client-name "$APP_CLIENT_NAME" \
    --region "$REGION" \
    --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH ALLOW_USER_SRP_AUTH \
    --supported-identity-providers COGNITO \
    --callback-urls "$REDIRECT_URI" \
    --logout-urls "$REDIRECT_URI" \
    --allowed-o-auth-flows code implicit \
    --allowed-o-auth-scopes openid email profile \
    --allowed-o-auth-flows-user-pool-client \
    --query 'UserPoolClient.ClientId' \
    --output text)

echo "✅ App Client created: $CLIENT_ID"

# Create Hosted UI Domain
echo "🌐 Creating Hosted UI Domain..."
aws cognito-idp create-user-pool-domain \
    --user-pool-id "$USER_POOL_ID" \
    --domain "$DOMAIN_PREFIX" \
    --region "$REGION" > /dev/null

COGNITO_DOMAIN="https://$DOMAIN_PREFIX.auth.$REGION.amazoncognito.com"
echo "✅ Hosted UI Domain created: $COGNITO_DOMAIN"

# Create S3 Bucket
echo "🪣 Creating S3 Bucket..."
aws s3 mb "s3://$BUCKET_NAME" --region "$REGION"

# Configure S3 Bucket CORS
echo "🔧 Configuring S3 CORS..."
cat > /tmp/cors-config.json << CORS_EOF
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
            "AllowedOrigins": ["*"],
            "ExposeHeaders": ["ETag"],
            "MaxAgeSeconds": 3000
        }
    ]
}
CORS_EOF

aws s3api put-bucket-cors \
    --bucket "$BUCKET_NAME" \
    --cors-configuration file:///tmp/cors-config.json

echo "✅ S3 Bucket created and configured: $BUCKET_NAME"

# Update HTML file
echo "📝 Updating HTML configuration..."
HTML_FILE="web-app/public/documentgpt.html"

if [ -f "$HTML_FILE" ]; then
    # Create backup
    cp "$HTML_FILE" "$HTML_FILE.backup"
    
    # Replace placeholders
    sed -i.tmp "s|COGNITO_DOMAIN_PLACEHOLDER|$COGNITO_DOMAIN|g" "$HTML_FILE"
    sed -i.tmp "s|COGNITO_CLIENT_ID_PLACEHOLDER|$CLIENT_ID|g" "$HTML_FILE"
    sed -i.tmp "s|COGNITO_REDIRECT_URI_PLACEHOLDER|$REDIRECT_URI|g" "$HTML_FILE"
    sed -i.tmp "s|API_BASE_URL_PLACEHOLDER|$API_BASE_URL|g" "$HTML_FILE"
    
    # Clean up temp file
    rm "$HTML_FILE.tmp"
    
    echo "✅ HTML file updated"
else
    echo "❌ HTML file not found: $HTML_FILE"
    exit 1
fi

# Test Cognito domain
echo "🧪 Testing Cognito domain..."
sleep 5  # Wait for domain to propagate

if curl -s "$COGNITO_DOMAIN/.well-known/openid-configuration" > /dev/null; then
    echo "✅ Cognito domain is accessible"
else
    echo "⚠️  Cognito domain may take a few minutes to become accessible"
fi

# Create environment file
echo "📄 Creating environment file..."
cat > .env.documentgpt << ENV_EOF
# DocumentGPT Environment Configuration
COGNITO_USER_POOL_ID=$USER_POOL_ID
COGNITO_CLIENT_ID=$CLIENT_ID
COGNITO_DOMAIN=$COGNITO_DOMAIN
COGNITO_REDIRECT_URI=$REDIRECT_URI
S3_BUCKET=$BUCKET_NAME
API_BASE_URL=$API_BASE_URL
AWS_REGION=$REGION
ENV_EOF

echo "✅ Environment file created: .env.documentgpt"

# Output summary
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Resources Created:"
echo "  • Cognito User Pool: $USER_POOL_ID"
echo "  • App Client: $CLIENT_ID"
echo "  • Hosted UI Domain: $COGNITO_DOMAIN"
echo "  • S3 Bucket: $BUCKET_NAME"
echo ""
echo "🔧 Next Steps:"
echo "  1. Update your API Gateway URL in the HTML file"
echo "  2. Deploy your Lambda functions with the new environment variables"
echo "  3. Test the application by opening web-app/public/documentgpt.html"
echo ""
echo "🌐 Test URLs:"
echo "  • Cognito Config: $COGNITO_DOMAIN/.well-known/openid-configuration"
echo "  • Login URL: $COGNITO_DOMAIN/login?client_id=$CLIENT_ID&response_type=code&scope=openid+profile+email&redirect_uri=$REDIRECT_URI"
echo ""
echo "📁 Configuration saved to: .env.documentgpt"
echo ""
echo "⚠️  Important: Update your Lambda functions to use these environment variables!"

# Clean up temp files
rm -f /tmp/cors-config.json

echo "✨ Setup script completed successfully!"