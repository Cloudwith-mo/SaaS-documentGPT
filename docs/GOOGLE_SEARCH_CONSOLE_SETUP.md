# Google Search Console Setup Guide

## Step 1: Add Property
1. Go to https://search.google.com/search-console
2. Click "Add Property"
3. Choose "URL prefix" and enter: `https://documentgpt.io`

## Step 2: Verify Ownership
Choose one of these methods:

### Option A: HTML File Upload (Recommended)
1. Download the verification file from Google (e.g., `google1234567890abcdef.html`)
2. Upload to S3:
   ```bash
   aws s3 cp google1234567890abcdef.html s3://documentgpt-website-prod/
   ```
3. Click "Verify" in Google Search Console

### Option B: DNS Verification
1. Add TXT record to your DNS provider
2. Wait for DNS propagation (5-30 minutes)
3. Click "Verify" in Google Search Console

## Step 3: Submit Sitemap
1. In Google Search Console, go to "Sitemaps" (left sidebar)
2. Enter: `https://documentgpt.io/sitemap.xml`
3. Click "Submit"

## Step 4: Monitor Performance
- Check "Performance" tab for search analytics
- Monitor "Coverage" for indexing issues
- Review "Enhancements" for mobile usability

## Expected Timeline
- Verification: Immediate
- First crawl: 1-3 days
- Ranking improvements: 2-4 weeks

## Key Metrics to Track
- Total clicks
- Total impressions
- Average CTR
- Average position
- Top queries: "AI document summarizer", "upload PDF and summarize", "chat with documents"
