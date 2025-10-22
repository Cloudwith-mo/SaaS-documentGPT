# RAG Architecture for DocumentGPT

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     DocumentGPT RAG System                   │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │      │    Lambda    │      │   Pinecone   │
│ (Dev HTML)   │◄────►│  (Dev RAG)   │◄────►│  (Vectors)   │
└──────────────┘      └──────────────┘      └──────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │   DynamoDB   │
                      │  (Metadata)  │
                      └──────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │   OpenAI     │
                      │ (Embeddings  │
                      │  & GPT-4)    │
                      └──────────────┘
```

## 📤 Document Upload Flow

```
User uploads PDF → Extract Text → Chunk (500 tokens) → 
Generate Embeddings → Store in Pinecone → Save Metadata → Done
```

## 💬 Query Flow (RAG)

```
User Question → Embed Query → Search Pinecone (top 5) → 
Build Context → GPT-4 with Citations → Return Answer
```

## 🔄 Comparison: Old vs New

### Old: Send full doc (10K tokens) → $0.30/query, 5-10s
### New: Send 5 chunks (2.5K tokens) → $0.03/query, 1-2s

**90% cost savings, 3x faster!**

---

**Status**: ✅ Ready for implementation
