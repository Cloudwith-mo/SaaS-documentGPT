# RAG Testing Plan

## 1. Basic Functionality Tests
```bash
# Test document upload
curl -X POST https://your-api.com/process-document \
  -H "Content-Type: application/json" \
  -d '{"docId":"test-1","filename":"test.txt","content":"The capital of France is Paris. It has a population of 2.1 million."}'

# Test RAG chat (with context)
curl -X POST https://your-api.com/rag-chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the population of Paris?","docId":"test-1"}'

# Test regular chat (no context)
curl -X POST https://your-api.com/rag-chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the weather like?"}'
```

## 2. Quality Tests

### Upload Test Document:
"Apple Inc. was founded in 1976 by Steve Jobs, Steve Wozniak, and Ronald Wayne. The company is headquartered in Cupertino, California. Apple's revenue in 2023 was $394.3 billion."

### Test Questions:
1. "When was Apple founded?" → Should return "1976"
2. "Who founded Apple?" → Should return "Steve Jobs, Steve Wozniak, and Ronald Wayne"
3. "What was Apple's 2023 revenue?" → Should return "$394.3 billion"
4. "What is the weather?" → Should work without document context

## 3. Performance Tests
- Upload 10 documents, test response time
- Test with 1000+ word documents
- Test similarity search accuracy

## 4. Integration Tests
- Test full flow: Upload → Process → Chat
- Test error handling (invalid docId, etc.)
- Test concurrent requests

## Success Criteria:
✅ Document uploads and processes successfully  
✅ RAG responses include relevant context  
✅ Non-document questions work normally  
✅ Response time < 3 seconds  
✅ Accurate retrieval of document facts