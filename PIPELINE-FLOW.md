# 🔄 DocumentGPT Pipeline Flow

## 📤 **Upload Pipeline**
```
User (Browser)
    ↓ POST /upload
API Gateway (9voqzgx3ch)
    ↓ invoke
Lambda: documentgpt-upload
    ↓ generate presigned URL
S3: documentgpt-uploads
    ↓ file uploaded
S3 Event Trigger
    ↓ invoke
Lambda: documentgpt-s3-trigger
    ↓ start execution
Step Functions: documentgpt-processing
    ↓ orchestrate
[Parser → Indexer → Status Update]
    ↓ store metadata
DynamoDB: documentgpt-documents
```

## 💬 **Chat Pipeline**
```
User (Browser)
    ↓ POST /rag-chat
API Gateway (9voqzgx3ch)
    ↓ invoke
Lambda: documentgpt-rag-chat
    ↓ retrieve context (if available)
DynamoDB: documentgpt-documents
    ↓ query OpenAI with context
OpenAI API (GPT-4o-mini)
    ↓ return response
User (Browser)
```

## 🌐 **Web Interface Pipeline**
```
User Browser
    ↓ GET https://documentgpt.io/
CloudFront Distribution
    ↓ serve from
S3: documentgpt-website-prod
    ↓ load SPA
React-like Interface
    ↓ API calls to
API Gateway: 9voqzgx3ch.execute-api.us-east-1.amazonaws.com
```

## 🔄 **Current Working Flow**
1. **Frontend**: ✅ Loads from S3/CloudFront
2. **Upload**: ✅ Generates S3 URLs via Lambda
3. **File Storage**: ✅ Files stored in S3
4. **Chat**: ✅ Works with pre-processed documents
5. **Processing**: ⚠️ Pipeline exists but not fully active

## 🎯 **Active Components**
- **documentgpt-upload**: Generating presigned URLs
- **documentgpt-rag-chat**: Handling AI conversations
- **documentgpt-root**: Serving web interface
- **S3 buckets**: Storing files and website
- **DynamoDB**: Tracking document metadata
- **API Gateway**: Routing all requests

## 🔧 **Inactive/Partial Components**
- **Step Functions**: Not consistently triggering
- **Document Processing**: Pipeline not completing
- **Vector Search**: Infrastructure present but unused
- **Real-time Processing**: Needs activation