# 🏗️ DocumentGPT Current Architecture & Infrastructure

## 🌐 **Frontend Layer**
```
https://documentgpt.io/
├── S3 Bucket: documentgpt-website-prod
├── CloudFront Distribution: E3KMXD3DB6KLDF (estimated)
└── Static React-like SPA with Tailwind CSS
```

## 🚪 **API Gateway Layer**
```
API Gateway: documentgpt-api (9voqzgx3ch)
├── Base URL: https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod
├── Endpoints:
│   ├── GET  / (root handler)
│   ├── POST /upload (document upload)
│   ├── POST /rag-chat (AI chat)
│   ├── POST /process-document (processing)
│   ├── GET  /health (health check)
│   └── Various legacy endpoints (v5, stripe, etc.)
```

## ⚡ **Compute Layer (Lambda Functions)**
```
16 Lambda Functions:
├── Core Functions:
│   ├── documentgpt-root (web interface)
│   ├── documentgpt-upload (S3 presigned URLs)
│   ├── documentgpt-rag-chat (OpenAI integration)
│   └── documentgpt-process-doc (document processing)
├── Processing Pipeline:
│   ├── documentgpt-s3-trigger (S3 event handler)
│   ├── documentgpt-parser (document parsing)
│   ├── documentgpt-indexer (vector indexing)
│   └── documentgpt-ingest-worker (data ingestion)
├── Support Functions:
│   ├── documentgpt-presign (URL generation)
│   ├── documentgpt-status-poll (status checking)
│   └── documentgpt-documents (document management)
└── Legacy Functions:
    ├── documentgpt-v5-api
    ├── documentgpt-chat
    ├── documentgpt-ingest
    └── documentgpt-rag
```

## 🗄️ **Storage Layer**
```
S3 Buckets (7 total):
├── documentgpt-uploads (primary upload bucket)
├── documentgpt-website-prod (static website)
├── documentgpt-storage-prod (processed documents)
├── documentgpt-processed-1757813720 (processed files)
├── documentgpt-raw-1757813720 (raw files)
├── documentgpt-uploads-1757887191 (backup uploads)
└── documentgpt-terraform-state (infrastructure state)

DynamoDB Tables (2 total):
├── documentgpt-documents (document metadata)
└── documentgpt-docs (document tracking)
```

## 🔄 **Processing Pipeline**
```
Step Functions State Machine:
└── documentgpt-processing (orchestrates document processing)

Current Pipeline Flow:
1. User uploads document → API Gateway /upload
2. Lambda generates S3 presigned URL
3. Frontend uploads file to S3
4. S3 trigger → documentgpt-s3-trigger
5. Step Functions → documentgpt-processing
6. Document parsing → documentgpt-parser
7. Vector indexing → documentgpt-indexer
8. Status update → DynamoDB
```

## 🤖 **AI Integration**
```
OpenAI Integration:
├── Model: GPT-4o-mini
├── Function: documentgpt-rag-chat
├── Context: Retrieved from processed documents
└── Response: Real-time AI answers
```

## 🔐 **Security & Authentication**
```
API Security:
├── API Keys: Required for upload endpoints
├── User Isolation: Multi-tenant via user-id headers
├── CORS: Enabled for web interface
└── Rate Limiting: Built into Lambda functions

Data Security:
├── S3: Private buckets with presigned URLs
├── DynamoDB: User-scoped data access
└── Lambda: IAM role-based permissions
```

## 📊 **Current Status**
```
✅ Operational Components:
├── Frontend: 100% functional
├── Upload System: Working with S3 integration
├── Chat System: Working with OpenAI
├── API Gateway: All endpoints responding
└── Error Handling: Complete

⚠️ Partial Components:
├── Document Processing: Pipeline exists but not fully triggered
├── Vector Search: Infrastructure present but not active
└── Real-time Processing: Step Functions not consistently firing

🔧 Legacy Components:
├── Multiple duplicate functions (cleanup needed)
├── Unused S3 buckets (optimization opportunity)
└── Old API versions (v5, etc.)
```

## 🎯 **Architecture Strengths**
- **Serverless**: Fully serverless, auto-scaling
- **Multi-tenant**: User isolation built-in
- **Resilient**: Multiple redundant components
- **Fast**: Sub-second API responses
- **Secure**: Proper authentication and authorization

## 🔧 **Optimization Opportunities**
- **Consolidate**: Merge duplicate Lambda functions
- **Cleanup**: Remove unused S3 buckets and functions
- **Processing**: Fix Step Functions triggering
- **Monitoring**: Add CloudWatch dashboards
- **Caching**: Implement response caching