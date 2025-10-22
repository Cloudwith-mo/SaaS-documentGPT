"""
DocumentGPT Dev Handler - RAG Implementation with Vector Search
This is the development version with Pinecone vector database integration
"""
import json
import urllib3
import os
import boto3
from datetime import datetime
from decimal import Decimal

# Initialize clients
http = urllib3.PoolManager()
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY', '')
PINECONE_INDEX_HOST = os.environ.get('PINECONE_INDEX_HOST', 'documentgpt-dev-t0mnwxg.svc.aped-4627-b74a.pinecone.io')

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Import PyPDF2 for PDF processing
try:
    import PyPDF2
    import io
except:
    PyPDF2 = None

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)

def chunk_text(text, chunk_size=500, overlap=50):
    """
    Split text into overlapping chunks for embedding
    chunk_size: approximate tokens per chunk (1 token ≈ 4 chars)
    overlap: tokens to overlap between chunks
    """
    # Convert tokens to characters (rough estimate)
    chars_per_chunk = chunk_size * 4
    chars_overlap = overlap * 4
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chars_per_chunk
        chunk = text[start:end]
        
        if chunk.strip():
            chunks.append({
                'text': chunk,
                'start': start,
                'end': end
            })
        
        start = end - chars_overlap
    
    return chunks

def generate_embeddings(text):
    """Generate OpenAI embeddings for text"""
    url = 'https://api.openai.com/v1/embeddings'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'text-embedding-ada-002',
        'input': text[:8000]  # Limit to 8K chars (~2K tokens)
    }
    
    response = http.request('POST', url, body=json.dumps(data), headers=headers)
    result = json.loads(response.data.decode('utf-8'))
    
    if 'data' in result and len(result['data']) > 0:
        return result['data'][0]['embedding']
    
    raise Exception('Failed to generate embedding')

def store_in_pinecone(doc_id, doc_name, chunks_with_embeddings):
    """Store document chunks and embeddings in Pinecone"""
    if not PINECONE_API_KEY:
        print("⚠️ Pinecone not configured, skipping vector storage")
        return False
    
    # Pinecone data plane endpoint
    url = f'https://{PINECONE_INDEX_HOST}/vectors/upsert'
    headers = {
        'Api-Key': PINECONE_API_KEY,
        'Content-Type': 'application/json'
    }
    
    vectors = []
    for idx, chunk_data in enumerate(chunks_with_embeddings):
        vectors.append({
            'id': f"{doc_id}_chunk_{idx}",
            'values': chunk_data['embedding'],
            'metadata': {
                'doc_id': doc_id,
                'doc_name': doc_name,
                'chunk_index': idx,
                'text': chunk_data['text'][:1000],  # Limit metadata size
                'start_pos': chunk_data['start'],
                'end_pos': chunk_data['end']
            }
        })
    
    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        data = {'vectors': batch}
        
        response = http.request('POST', url, body=json.dumps(data), headers=headers)
        result = json.loads(response.data.decode('utf-8'))
        
        if response.status != 200:
            print(f"❌ Pinecone upsert failed: {result}")
            return False
    
    print(f"✅ Stored {len(vectors)} chunks in Pinecone")
    return True

def query_pinecone(query_text, top_k=5):
    """Query Pinecone for relevant document chunks"""
    if not PINECONE_API_KEY:
        print("⚠️ Pinecone not configured, returning empty results")
        return []
    
    # Generate embedding for query
    query_embedding = generate_embeddings(query_text)
    
    # Pinecone data plane endpoint
    url = f'https://{PINECONE_INDEX_HOST}/query'
    headers = {
        'Api-Key': PINECONE_API_KEY,
        'Content-Type': 'application/json'
    }
    
    data = {
        'vector': query_embedding,
        'topK': top_k,
        'includeMetadata': True
    }
    
    response = http.request('POST', url, body=json.dumps(data), headers=headers)
    result = json.loads(response.data.decode('utf-8'))
    
    if 'matches' in result:
        return result['matches']
    
    return []

def generate_summary_and_questions(text):
    """Generate document summary and preview questions"""
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    prompt = f"""Summarize in 3 sentences and suggest 3 questions:\n\n{text[:2000]}\n\nJSON format: {{"summary": "...", "questions": ["...", "...", "..."]}}"""
    
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.7,
        'max_tokens': 250,
        'response_format': {'type': 'json_object'}
    }
    
    response = http.request('POST', url, body=json.dumps(data), headers=headers)
    result = json.loads(response.data.decode('utf-8'))
    
    if 'choices' in result and len(result['choices']) > 0:
        content = result['choices'][0]['message']['content']
        return json.loads(content)
    
    return {'summary': '', 'questions': []}

def openai_chat_with_context(query, context_chunks, stream=False):
    """
    Call OpenAI with RAG context
    Uses GPT-4-turbo-preview for best quality
    """
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Build context from chunks
    context_text = ""
    citations = []
    
    for idx, chunk in enumerate(context_chunks, 1):
        metadata = chunk.get('metadata', {})
        text = metadata.get('text', '')
        doc_name = metadata.get('doc_name', 'Unknown')
        
        context_text += f"[{idx}] {text}\n(Source: {doc_name})\n\n"
        # Estimate page number (assuming ~3000 chars per page)
        start_pos = metadata.get('start_pos', 0)
        page_num = (start_pos // 3000) + 1
        
        citations.append({
            'id': idx,
            'doc_id': metadata.get('doc_id'),
            'doc_name': doc_name,
            'page': page_num,
            'text': text[:200],
            'score': chunk.get('score', 0)
        })
    
    # Build prompt with citations
    system_prompt = """You are a helpful AI assistant that answers questions based on provided document context.

IMPORTANT: Always cite your sources using [1], [2], etc. when referencing information from the context.

If the context doesn't contain enough information to answer the question, say so clearly."""
    
    user_prompt = f"""Context from documents:
{context_text}

Question: {query}

Answer the question using the context above. Include citations [1], [2], etc. when referencing specific information."""
    
    data = {
        'model': 'gpt-3.5-turbo',  # 3x faster than GPT-4
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        'temperature': 0.7,
        'max_tokens': 500,
        'stream': stream
    }
    
    response = http.request('POST', url, body=json.dumps(data), headers=headers)
    result = json.loads(response.data.decode('utf-8'))
    
    if 'choices' in result and len(result['choices']) > 0:
        answer = result['choices'][0]['message']['content']
        return {
            'answer': answer,
            'citations': citations,
            'context_used': len(context_chunks)
        }
    
    return {
        'answer': 'Sorry, I could not process that request.',
        'citations': [],
        'context_used': 0
    }

def lambda_handler(event, context):
    """Main Lambda handler for dev environment"""
    headers = {'Content-Type': 'application/json'}
    
    try:
        # Support both API Gateway v1/v2 and Lambda URL formats
        if 'requestContext' in event and 'http' in event['requestContext']:
            # Lambda URL or API Gateway v2
            method = event['requestContext']['http']['method']
            path = event.get('rawPath', event['requestContext']['http'].get('path', ''))
        else:
            # API Gateway v1
            method = event.get('httpMethod', '')
            path = event.get('path', '')
        
        print(f"Path: {path}, Method: {method}")  # Debug
        
        if method == 'OPTIONS':
            return {'statusCode': 200, 'headers': headers, 'body': ''}
        
        # Health check endpoint
        if path == '/dev/health' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'status': 'healthy',
                    'environment': 'dev',
                    'rag_enabled': bool(PINECONE_API_KEY),
                    'timestamp': datetime.now().isoformat()
                })
            }
        
        # Upload endpoint with RAG processing
        elif path == '/dev/upload' and method == 'POST':
            body = json.loads(event['body'])
            user_id = body.get('user_id', 'guest_dev')
            filename = body.get('filename')
            content = body.get('content')
            
            if not content or not filename:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing filename or content'})
                }
            
            # Generate document ID
            doc_id = f"doc_{int(datetime.now().timestamp())}"
            
            # Step 1: Chunk the document
            print(f"📄 Chunking document: {filename}")
            chunks = chunk_text(content)
            print(f"✂️ Created {len(chunks)} chunks")
            
            # Step 2: Generate embeddings for each chunk
            print(f"🔢 Generating embeddings...")
            chunks_with_embeddings = []
            
            for chunk in chunks[:50]:  # Limit to 50 chunks for dev testing
                try:
                    embedding = generate_embeddings(chunk['text'])
                    chunks_with_embeddings.append({
                        'text': chunk['text'],
                        'start': chunk['start'],
                        'end': chunk['end'],
                        'embedding': embedding
                    })
                except Exception as e:
                    print(f"⚠️ Embedding failed for chunk: {e}")
            
            print(f"✅ Generated {len(chunks_with_embeddings)} embeddings")
            
            # Step 3: Store in Pinecone
            if chunks_with_embeddings:
                stored = store_in_pinecone(doc_id, filename, chunks_with_embeddings)
                if stored:
                    print(f"✅ Stored in Pinecone")
            
            # Step 4: Generate auto-summary (optional, async)
            summary_data = None
            generate_summary = body.get('generate_summary', False)
            if content and generate_summary:
                try:
                    summary_data = generate_summary_and_questions(content[:2000])
                    print(f"✅ Generated summary and {len(summary_data.get('questions', []))} questions")
                except Exception as e:
                    print(f"⚠️ Summary generation failed: {e}")
            
            # Step 5: Save metadata to DynamoDB
            docs_table = dynamodb.Table('docgpt')
            item = {
                'pk': f'USER#{user_id}',
                'sk': f'DOC#{doc_id}',
                'doc_id': doc_id,
                'filename': filename,
                'content': content[:50000],
                'indexed': bool(chunks_with_embeddings),
                'chunk_count': len(chunks_with_embeddings),
                'created_at': datetime.now().isoformat()
            }
            if summary_data:
                item['summary'] = summary_data.get('summary', '')
                item['questions'] = summary_data.get('questions', [])
            
            docs_table.put_item(Item=item)
            
            response_data = {
                'message': 'Document uploaded and indexed',
                'doc_id': doc_id,
                'chunks': len(chunks_with_embeddings),
                'indexed': bool(chunks_with_embeddings)
            }
            if summary_data:
                response_data['summary'] = summary_data.get('summary')
                response_data['questions'] = summary_data.get('questions')
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response_data)
            }
        
        # Usage endpoint
        elif path == '/usage' and method == 'GET':
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'plan': 'premium', 'chats_used': 0, 'limit': -1})}
        
        # Documents endpoint
        elif path == '/documents' and method == 'GET':
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'documents': []})}
        
        elif path == '/documents' and method == 'POST':
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'Saved'})}
        
        # Chat endpoint with RAG
        elif path == '/dev/chat' and method == 'POST':
            body = json.loads(event['body'])
            query = body.get('query') or body.get('messages', [{}])[-1].get('content', '')
            
            if not query:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'No query provided'})
                }
            
            # Step 1: Query Pinecone for relevant chunks
            print(f"🔍 Searching for: {query[:100]}")
            matches = query_pinecone(query, top_k=5)
            print(f"📚 Found {len(matches)} relevant chunks")
            
            # Step 2: Generate answer with context
            if matches:
                result = openai_chat_with_context(query, matches)
            else:
                # Fallback to direct OpenAI if no context
                result = {
                    'answer': 'No relevant documents found. Please upload documents first.',
                    'citations': [],
                    'context_used': 0
                }
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'response': result['answer'],
                    'citations': result['citations'],
                    'context_used': result['context_used']
                })
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
