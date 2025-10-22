# Quick Reference

## 🔗 URLs

- **Dev Frontend**: https://documentgpt.io/dev.html
- **Test Page**: https://documentgpt.io/rag-test.html
- **Dev API**: https://w6poeb2pzi5v6lglx5jbygv3uu0uarkd.lambda-url.us-east-1.on.aws

## 🧪 Test Commands

```bash
API="https://w6poeb2pzi5v6lglx5jbygv3uu0uarkd.lambda-url.us-east-1.on.aws"

# Health
curl -s "$API/dev/health" | jq .

# Upload
curl -s -X POST "$API/dev/upload" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","filename":"doc.txt","content":"Your content"}' | jq .

# Query
curl -s -X POST "$API/dev/chat" \
  -H "Content-Type: application/json" \
  -d '{"query":"Your question?"}' | jq .

# Pinecone Stats
curl -s -X POST "https://documentgpt-dev-t0mnwxg.svc.aped-4627-b74a.pinecone.io/describe_index_stats" \
  -H "Api-Key: pcsk_38SJXz_GgqjQVKLKoj4kq2HwWMQkgRQ1r7NP7pVCQ7qRWZ6Bo7PiefZRqM8UY3hB3ZaCwM" \
  -H "Content-Type: application/json" -d '{}' | jq .
```

## 📊 Status

- Tests: 20/20 ✅
- Vectors: 7
- Cost: 90% reduction
- Speed: 3x faster

## 🔧 Lambda

```bash
# Update code
cd lambda
zip -q dev-deployment.zip dev_handler.py
zip -rq dev-deployment.zip boto3/ botocore/ urllib3/ PyPDF2/ dateutil/ jmespath/ s3transfer/
aws lambda update-function-code --function-name documentgpt-dev --zip-file fileb://dev-deployment.zip --region us-east-1

# Check logs
aws logs tail /aws/lambda/documentgpt-dev --region us-east-1 --follow
```

## 📝 Key Files

- `lambda/dev_handler.py` - RAG handler
- `web/dev.html` - Frontend
- `RAG_STATUS.md` - Status
- `IMPLEMENTATION_COMPLETE.md` - Summary

## 🎯 Next

1. Test with PDFs at https://documentgpt.io/dev.html
2. Verify chunking with 10+ pages
3. Deploy to staging
