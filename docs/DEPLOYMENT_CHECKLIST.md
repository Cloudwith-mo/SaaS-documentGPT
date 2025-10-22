# Deployment Checklist - Performance Optimizations

## Pre-Deployment

### 1. Verify Changes
- [ ] Review `web/backup.html` changes
  - [ ] Lumina features removed
  - [ ] Render cache added
  - [ ] No syntax errors
- [ ] Review `lambda/simple_handler.py` changes
  - [ ] DynamoDB cache added
  - [ ] gpt-4o-mini integration
  - [ ] No syntax errors
- [ ] Test locally (if possible)

### 2. Backup Current Version
```bash
# Backup production
aws s3 cp s3://documentgpt-website-prod/index.html ./backups/index-$(date +%Y%m%d).html
aws s3 cp s3://documentgpt-website-prod/backup.html ./backups/backup-$(date +%Y%m%d).html

# Backup Lambda
aws lambda get-function --function-name docgpt-chat --query 'Code.Location' --output text | xargs curl -o ./backups/lambda-$(date +%Y%m%d).zip
```

### 3. Check AWS Resources
- [ ] DynamoDB table `docgpt` exists
- [ ] Lambda function `docgpt-chat` exists
- [ ] S3 bucket `documentgpt-website-prod` exists
- [ ] API Gateway endpoint is live

---

## Deployment Steps

### Option A: Automated (Recommended)
```bash
./deploy-optimized.sh
```

### Option B: Manual

#### Step 1: Deploy Frontend
```bash
# Compress files
gzip -9 -k web/backup.html
gzip -9 -k web/index.html

# Upload with headers
aws s3 cp web/backup.html.gz s3://documentgpt-website-prod/backup.html \
  --content-encoding gzip \
  --content-type "text/html" \
  --cache-control "public, max-age=3600"

aws s3 cp web/index.html.gz s3://documentgpt-website-prod/index.html \
  --content-encoding gzip \
  --content-type "text/html" \
  --cache-control "public, max-age=3600"

# Clean up
rm web/*.gz
```

#### Step 2: Deploy Backend
```bash
cd lambda
zip -r function.zip simple_handler.py
aws lambda update-function-code \
  --function-name docgpt-chat \
  --zip-file fileb://function.zip
rm function.zip
cd ..
```

#### Step 3: Setup CloudFront (First Time Only)
```bash
# Create distribution
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json

# Note the distribution ID and domain name
```

#### Step 4: Invalidate CloudFront Cache
```bash
# Get distribution ID
DIST_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='DocumentGPT CloudFront CDN for static files'].Id" --output text)

# Invalidate cache
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

---

## Post-Deployment Verification

### 1. Test Frontend
- [ ] Visit https://documentgpt.io/backup.html
- [ ] Check browser console for errors
- [ ] Test document creation
- [ ] Test tab switching (should be fast)
- [ ] Test chat functionality

### 2. Test Backend
```bash
# Test chat endpoint
curl -X POST https://i1dy8i3692.execute-api.us-east-1.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","messages":[{"role":"user","content":"hello"}]}'

# Should return response in < 1s
```

### 3. Verify Compression
```bash
# Check gzip encoding
curl -I https://documentgpt.io/backup.html | grep content-encoding

# Should see: content-encoding: gzip
```

### 4. Verify Caching
```bash
# Check cache headers
curl -I https://documentgpt.io/backup.html | grep cache-control

# Should see: cache-control: public, max-age=3600
```

### 5. Check DynamoDB Cache
```bash
# Wait 1 minute, then check cache table
aws dynamodb scan --table-name docgpt \
  --filter-expression "pk = :pk" \
  --expression-attribute-values '{":pk":{"S":"CHAT_CACHE"}}' \
  --select COUNT

# Should see cached items
```

### 6. Monitor CloudWatch
- [ ] Check Lambda duration (should be < 1000ms)
- [ ] Check Lambda errors (should be 0%)
- [ ] Check DynamoDB read/write units
- [ ] Check API Gateway 4xx/5xx errors

---

## Performance Testing

### Load Time Test
```bash
curl -w "@curl-format.txt" -o /dev/null -s https://documentgpt.io/backup.html
```

**Expected Results**:
- `time_total`: < 2.0s (first load)
- `time_total`: < 0.5s (cached)

### API Response Test
```bash
# First call (cache miss)
time curl -X POST https://i1dy8i3692.execute-api.us-east-1.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","messages":[{"role":"user","content":"hello"}]}'

# Second call (cache hit)
time curl -X POST https://i1dy8i3692.execute-api.us-east-1.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","messages":[{"role":"user","content":"hello"}]}'
```

**Expected Results**:
- First call: < 1.0s
- Second call: < 0.3s (cache hit)

### File Size Test
```bash
# Check compressed size
curl -s -H "Accept-Encoding: gzip" https://documentgpt.io/backup.html | wc -c

# Should be ~68KB (vs 245KB uncompressed)
```

---

## Rollback Plan

### If Issues Occur

#### Rollback Frontend
```bash
# Restore from backup
aws s3 cp ./backups/backup-YYYYMMDD.html s3://documentgpt-website-prod/backup.html
```

#### Rollback Backend
```bash
# Restore Lambda from backup
aws lambda update-function-code \
  --function-name docgpt-chat \
  --zip-file fileb://./backups/lambda-YYYYMMDD.zip
```

#### Disable CloudFront (if needed)
```bash
# Get distribution config
aws cloudfront get-distribution-config --id $DIST_ID > dist-config.json

# Disable distribution
# Edit dist-config.json: "Enabled": false
aws cloudfront update-distribution --id $DIST_ID --distribution-config file://dist-config.json
```

---

## Monitoring (First 24 Hours)

### CloudWatch Alarms to Watch
- [ ] Lambda Duration > 2000ms
- [ ] Lambda Errors > 1%
- [ ] API Gateway 5xx > 1%
- [ ] DynamoDB Throttles > 0

### Metrics to Track
- [ ] Average load time (should be < 2s)
- [ ] Average API response time (should be < 1s)
- [ ] Cache hit rate (should be > 40%)
- [ ] Error rate (should be < 1%)

### User Feedback
- [ ] Monitor support emails
- [ ] Check social media mentions
- [ ] Review analytics for drop-offs

---

## Success Criteria

✅ **Deployment Successful If**:
- [ ] Load time < 2.0s (first load)
- [ ] Load time < 0.5s (cached)
- [ ] API response < 1.0s (cache miss)
- [ ] API response < 0.3s (cache hit)
- [ ] No increase in error rate
- [ ] No user complaints
- [ ] CloudWatch metrics healthy

---

## Post-Deployment Tasks

### Immediate (Day 1)
- [ ] Monitor CloudWatch for 2 hours
- [ ] Test all major features
- [ ] Check error logs
- [ ] Verify cache is working

### Short-term (Week 1)
- [ ] Review cost savings
- [ ] Analyze cache hit rate
- [ ] Optimize cache TTL if needed
- [ ] Document any issues

### Long-term (Month 1)
- [ ] Compare costs before/after
- [ ] Review performance metrics
- [ ] Plan next optimizations
- [ ] Update documentation

---

## Notes

- **CloudFront propagation**: Takes 15-30 minutes
- **DynamoDB cache**: Warms up after first few requests
- **Browser cache**: Users may need hard refresh (Cmd+Shift+R)
- **Lambda cold starts**: First request may be slower

---

## Contact

If issues occur:
1. Check CloudWatch logs
2. Review error messages
3. Rollback if critical
4. Document issue for future reference

---

## Checklist Summary

- [ ] Pre-deployment backups complete
- [ ] Frontend deployed with compression
- [ ] Backend deployed with cache
- [ ] CloudFront configured
- [ ] Post-deployment tests passed
- [ ] Performance metrics verified
- [ ] Monitoring enabled
- [ ] Documentation updated

**Status**: Ready for production deployment ✅
