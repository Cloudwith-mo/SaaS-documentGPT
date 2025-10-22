# Pinecone Setup Guide for DocumentGPT Dev

## 🎯 Quick Setup (5 minutes)

### Step 1: Create Pinecone Account
1. Go to https://www.pinecone.io/
2. Sign up for free account (includes 1 index, 100K vectors free)
3. Verify email

### Step 2: Create Index
1. In Pinecone console, click "Create Index"
2. Settings:
   - **Name**: `documentgpt-dev`
   - **Dimensions**: `1536` (OpenAI ada-002 embedding size)
   - **Metric**: `cosine`
   - **Pod Type**: `s1.x1` (free tier)
   - **Replicas**: `1`
   - **Pods**: `1`
3. Click "Create Index"

### Step 3: Get API Key
1. Go to "API Keys" in Pinecone console
2. Copy your API key (starts with `pcsk_...`)
3. Note your environment (e.g., `us-east-1-aws`)

### Step 4: Configure Lambda
```bash
# Set environment variables in AWS Lambda console
PINECONE_API_KEY=pcsk_xxxxx
PINECONE_INDEX_NAME=documentgpt-dev
PINECONE_ENVIRONMENT=us-east-1-aws
```

Or use AWS CLI:
```bash
aws lambda update-function-configuration \
  --function-name documentgpt-dev \
  --environment Variables="{
    OPENAI_API_KEY=$OPENAI_API_KEY,
    PINECONE_API_KEY=pcsk_xxxxx,
    PINECONE_INDEX_NAME=documentgpt-dev,
    PINECONE_ENVIRONMENT=us-east-1-aws
  }" \
  --region us-east-1
```

## 🧪 Test the Setup

### 1. Health Check
```bash
curl https://YOUR_DEV_API_URL/dev/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "dev",
  "rag_enabled": true,
  "timestamp": "2024-01-15T10:30:00"
}
```

### 2. Upload Test Document
```bash
curl -X POST https://YOUR_DEV_API_URL/dev/upload \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "filename": "test.txt",
    "content": "This is a test document about artificial intelligence and machine learning. AI is transforming how we work and live."
  }'
```

Expected response:
```json
{
  "message": "Document uploaded and indexed",
  "doc_id": "doc_1234567890",
  "chunks": 1,
  "indexed": true
}
```

### 3. Query Test
```bash
curl -X POST https://YOUR_DEV_API_URL/dev/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this document about?"
  }'
```

Expected response:
```json
{
  "response": "This document is about artificial intelligence and machine learning [1]. It discusses how AI is transforming work and daily life [1].",
  "citations": [
    {
      "id": 1,
      "doc_name": "test.txt",
      "text": "This is a test document about artificial intelligence...",
      "score": 0.95
    }
  ],
  "context_used": 1
}
```

## 📊 Pinecone Free Tier Limits
- **Vectors**: 100,000 free
- **Queries**: Unlimited
- **Indexes**: 1 free index
- **Storage**: ~400MB

For DocumentGPT dev:
- Average document: 10-50 chunks
- 100K vectors = ~2,000-10,000 documents
- More than enough for development!

## 🔧 Troubleshooting

### Error: "Index not found"
- Check index name matches exactly: `documentgpt-dev`
- Verify index is created in Pinecone console

### Error: "Invalid API key"
- Check API key is correct (starts with `pcsk_`)
- Verify key is set in Lambda environment variables

### Error: "Dimension mismatch"
- Index must be 1536 dimensions for OpenAI ada-002
- Delete and recreate index with correct dimensions

### No results from queries
- Check documents were uploaded successfully
- Verify `indexed: true` in upload response
- Check Pinecone console for vector count

## 💰 Cost Estimate (Production)
When moving to production with paid Pinecone:

- **Starter**: $70/month (5M vectors, 100K queries/month)
- **Standard**: $0.096/hour per pod (~$70/month)

For 10,000 users with 10 docs each:
- 100K documents × 30 chunks = 3M vectors
- Fits in Starter plan: $70/month

Much cheaper than sending full documents to OpenAI!

## 🚀 Next Steps
1. ✅ Set up Pinecone account
2. ✅ Create dev index
3. ✅ Configure Lambda
4. ✅ Test health endpoint
5. ⏭️ Deploy dev Lambda
6. ⏭️ Test upload flow
7. ⏭️ Test query flow
8. ⏭️ Update dev frontend
