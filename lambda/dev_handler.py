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
from boto3.dynamodb.conditions import Key

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
    """Generate OpenAI embeddings for single text"""
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
    
    if 'error' in result:
        print(f"❌ OpenAI embedding error: {result['error']}")
        raise Exception(f"OpenAI error: {result['error'].get('message', 'Unknown')}")
    
    if 'data' in result and len(result['data']) > 0:
        return result['data'][0]['embedding']
    
    print(f"❌ Unexpected embedding response: {result}")
    raise Exception('Failed to generate embedding')

def call_openai_with_retry(func, max_retries=3):
    """Retry OpenAI calls with exponential backoff"""
    import time
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_str = str(e)
            if attempt == max_retries - 1:
                raise
            # Retry on rate limits (429) or server errors (5xx)
            if '429' in error_str or (len(error_str) > 0 and error_str[0] == '5'):
                wait_time = 2 ** attempt
                print(f"⚠️ Retry {attempt + 1}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)
            else:
                raise

def generate_embeddings_batch(texts):
    """Generate OpenAI embeddings for multiple texts in one call (10x faster)"""
    def _embed():
        url = 'https://api.openai.com/v1/embeddings'
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Truncate each text to 8K chars
        truncated_texts = [t[:8000] for t in texts]
        
        data = {
            'model': 'text-embedding-ada-002',
            'input': truncated_texts
        }
        
        response = http.request('POST', url, body=json.dumps(data), headers=headers)
        result = json.loads(response.data.decode('utf-8'))
        
        if 'error' in result:
            print(f"❌ OpenAI batch embedding error: {result['error']}")
            raise Exception(f"OpenAI error: {result['error'].get('message', 'Unknown')}")
        
        if 'data' in result:
            return [item['embedding'] for item in result['data']]
        
        print(f"❌ Unexpected batch embedding response: {result}")
        raise Exception('Failed to generate batch embeddings')
    
    return call_openai_with_retry(_embed)

def upsert_batch(url, headers, batch):
    """Upsert single batch to Pinecone"""
    data = {'vectors': batch}
    response = http.request('POST', url, body=json.dumps(data), headers=headers)
    return response.status == 200

def store_in_pinecone(doc_id, doc_name, chunks_with_embeddings):
    """Store document chunks and embeddings in Pinecone with parallel upsert"""
    if not PINECONE_API_KEY:
        print("⚠️ Pinecone not configured, skipping vector storage")
        return False
    
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
                'text': chunk_data['text'][:1000],
                'start_pos': chunk_data['start'],
                'end_pos': chunk_data['end']
            }
        })
    
    # Parallel upsert in batches of 100
    import concurrent.futures
    batch_size = 100
    batches = [vectors[i:i+batch_size] for i in range(0, len(vectors), batch_size)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(upsert_batch, url, headers, batch) for batch in batches]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    if all(results):
        print(f"✅ Stored {len(vectors)} chunks in Pinecone (parallel)")
        return True
    print(f"⚠️ Some batches failed")
    return False

def query_pinecone(query_text, doc_id=None, top_k=5):
    """Query Pinecone for relevant document chunks with optional doc filter"""
    if not PINECONE_API_KEY:
        print("⚠️ Pinecone not configured, returning empty results")
        return []
    
    try:
        # Generate embedding for query
        query_embedding = generate_embeddings(query_text)
    except Exception as e:
        print(f"⚠️ Query embedding failed: {e}")
        return []
    
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
    
    # Add doc_id filter if provided (prevents cross-document contamination)
    if doc_id:
        data['filter'] = {'doc_id': {'$eq': doc_id}}
    
    try:
        response = http.request('POST', url, body=json.dumps(data), headers=headers)
        result = json.loads(response.data.decode('utf-8'))
        
        if 'matches' in result:
            return result['matches']
    except Exception as e:
        print(f"⚠️ Pinecone query failed: {e}")
    
    return []

def classify_intent(query):
    """Classify user intent: summary, compare, or qa"""
    import re
    query_lower = query.lower()
    if re.search(r'\b(summar(y|ize|ise)|overview|abstract|gist|tl;?dr)\b', query_lower):
        return 'summary'
    if re.search(r'\b(compare|contrast|difference|similarities)\b', query_lower):
        return 'compare'
    return 'qa'

def generate_summary_and_questions(text, doc_name="Document"):
    """Generate document summary and preview questions - handles large docs"""
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # For large docs: use first 4K + middle 2K + last 2K chars
    if len(text) > 12000:
        sample = text[:4000] + "\n...\n" + text[len(text)//2:len(text)//2+2000] + "\n...\n" + text[-2000:]
    else:
        sample = text[:12000]
    
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [{
            'role': 'system',
            'content': 'Return JSON {"summary":string, "questions":string[]} with 3-5 sentence summary and 3 specific questions.'
        }, {
            'role': 'user',
            'content': f"Document: {doc_name}\n\n{sample}"
        }],
        'temperature': 0,
        'response_format': {'type': 'json_object'}
    }
    
    response = http.request('POST', url, body=json.dumps(data), headers=headers)
    result = json.loads(response.data.decode('utf-8'))
    
    if 'choices' in result:
        return json.loads(result['choices'][0]['message']['content'])
    
    # Fallback: always return something
    return {
        'summary': f'This document ({doc_name}) contains {len(text)} characters. Upload successful - you can now ask questions about the content.',
        'questions': [
            'What are the main topics covered in this document?',
            'Can you summarize the key findings?',
            'What are the most important points?'
        ]
    }

def select_model(query, user_tier='free'):
    """Select optimal model based on query complexity and user tier"""
    if user_tier in ['premium', 'pro', 'business']:
        if len(query) > 100 or any(word in query.lower() for word in ['analyze', 'compare', 'explain', 'detailed']):
            return 'gpt-4-turbo-preview'
    return 'gpt-3.5-turbo'

def openai_chat_with_context(query, context_chunks, stream=False, user_tier='free'):
    """
    Call OpenAI with RAG context - Evidence-first with strict citations
    Supports streaming for real-time token display
    """
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    model = select_model(query, user_tier)
    
    # Build context from chunks (top 5 for precision)
    context_text = ""
    citations = []
    
    for idx, chunk in enumerate(context_chunks[:5], 1):
        metadata = chunk.get('metadata', {})
        text = metadata.get('text', '')[:1200]  # Trim to 1200 chars
        doc_name = metadata.get('doc_name', 'Unknown')
        
        context_text += f"[{idx}] {text}\n\n"
        # Estimate page number (assuming ~3000 chars per page)
        start_pos = metadata.get('start_pos', 0)
        page_num = (start_pos // 3000) + 1
        
        citations.append({
            'n': idx,
            'doc_id': metadata.get('doc_id'),
            'docName': doc_name,
            'page': page_num,
            'text': text[:300],
            'score': chunk.get('score', 0)
        })
    
    # Strict evidence-first prompt
    system_prompt = """Use ONLY EVIDENCE sections. Every factual sentence must end with [n]. If unsupported by evidence, say you can't find it in the document."""
    
    user_prompt = f"""EVIDENCE:
{context_text}

QUESTION: {query}
ANSWER:"""
    
    data = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        'temperature': 0,
        'max_tokens': 500,
        'stream': stream
    }
    
    if stream:
        # Return generator for streaming
        response = http.request('POST', url, body=json.dumps(data), headers=headers, preload_content=False)
        return stream_openai_response(response, citations)
    
    response = http.request('POST', url, body=json.dumps(data), headers=headers)
    result = json.loads(response.data.decode('utf-8'))
    
    if 'error' in result:
        print(f"❌ OpenAI error: {result['error']}")
        return {
            'answer': 'Sorry, I could not process that request.',
            'citations': [],
            'context_used': 0
        }
    
    if 'choices' in result and len(result['choices']) > 0:
        answer = result['choices'][0]['message']['content']
        # Guardrail: ensure citations present
        import re
        if not re.search(r'\[\d+\]', answer):
            answer = "I can't find support for that in the document."
            citations = []
        return {
            'answer': answer,
            'citations': citations,
            'context_used': len(context_chunks)
        }
    
    print(f"❌ Unexpected OpenAI response: {result}")
    return {
        'answer': 'Sorry, I could not process that request.',
        'citations': [],
        'context_used': 0
    }

def stream_openai_response(response, citations):
    """Stream OpenAI response tokens"""
    for line in response.stream(decode_content=True):
        line = line.decode('utf-8').strip()
        if line.startswith('data: '):
            if line == 'data: [DONE]':
                break
            try:
                chunk = json.loads(line[6:])
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        yield {'token': delta['content'], 'citations': citations}
            except:
                continue

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
            
            # Step 1: Generate summary (always succeeds)
            print(f"📄 Processing: {filename} ({len(content)} chars)")
            try:
                summary_data = generate_summary_and_questions(content, filename)
            except Exception as e:
                print(f"⚠️ Summary failed: {e}")
                summary_data = {
                    'summary': f'Document uploaded successfully. You can now ask questions about {filename}.',
                    'questions': [
                        'What is this document about?',
                        'What are the main points?',
                        'Can you summarize the key findings?'
                    ]
                }
            
            # Step 2: Vectorize and store in Pinecone (batched for 10x speed)
            import time
            embed_start = time.time()
            
            chunks = chunk_text(content)
            chunks_with_embeddings = []
            
            # Process in batches of 10 for 10x speedup
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                try:
                    batch_texts = [c['text'] for c in batch]
                    embeddings = generate_embeddings_batch(batch_texts)
                    
                    for j, embedding in enumerate(embeddings):
                        chunks_with_embeddings.append({
                            'text': batch[j]['text'],
                            'start': batch[j]['start'],
                            'end': batch[j]['end'],
                            'embedding': embedding
                        })
                except Exception as e:
                    print(f"⚠️ Batch embedding failed: {e}")
                    break
            
            embed_time = (time.time() - embed_start) * 1000
            print(f"⏱️  Embedding time: {embed_time:.0f}ms for {len(chunks_with_embeddings)} chunks")
            
            if chunks_with_embeddings:
                store_in_pinecone(doc_id, filename, chunks_with_embeddings)
                print(f"✅ Vectorized {len(chunks_with_embeddings)} chunks")
            else:
                print(f"⚠️ No vectors created - answers may not have citations")
                # Ensure questions array exists even without vectorization
                if not summary_data.get('questions'):
                    summary_data['questions'] = [
                        'What is this document about?',
                        'What are the main points?',
                        'Can you summarize the key findings?'
                    ]
            
            # Step 3: Save to DynamoDB
            docs_table = dynamodb.Table('docgpt')
            docs_table.put_item(Item={
                'pk': f'USER#{user_id}',
                'sk': f'DOC#{doc_id}',
                'doc_id': doc_id,
                'filename': filename,
                'content': content[:50000],
                'summary': summary_data.get('summary', ''),
                'questions': summary_data.get('questions', []),
                'created_at': datetime.now().isoformat()
            })
            
            response_data = {
                'message': 'Document uploaded',
                'doc_id': doc_id,
                'artifact': summary_data
            }
            
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
            user_id = event.get('queryStringParameters', {}).get('user_id') if event.get('queryStringParameters') else None
            if not user_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing user_id'})
                }
            docs_table = dynamodb.Table('docgpt')
            try:
                resp = docs_table.query(
                    KeyConditionExpression=Key('pk').eq(f'USER#{user_id}') & Key('sk').begins_with('DOC#'),
                    ProjectionExpression='doc_id, filename, summary, questions, created_at, content, chat_history'
                )
                documents = [{
                    'doc_id': item.get('doc_id'),
                    'id': item.get('doc_id'),
                    'filename': item.get('filename'),
                    'summary': item.get('summary', ''),
                    'questions': item.get('questions', []),
                    'created_at': item.get('created_at'),
                    'content': item.get('content', ''),
                    'chat_history': item.get('chat_history', [])
                } for item in resp.get('Items', [])]
            except Exception as e:
                print(f"⚠️ Dynamo query failed: {e}")
                documents = []
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'documents': documents}, cls=DecimalEncoder)}
        
        elif path == '/documents' and method == 'POST':
            body = json.loads(event.get('body') or '{}')
            user_id = body.get('user_id')
            doc_id = body.get('doc_id')
            if not user_id or not doc_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing user_id or doc_id'})
                }
            docs_table = dynamodb.Table('docgpt')
            try:
                update_expression = 'SET filename=:name, content=:content, summary=:summary, questions=:questions, updated_at=:updated_at'
                expression_values = {
                    ':name': body.get('name', ''),
                    ':content': (body.get('content') or '')[:50000],
                    ':summary': body.get('summary', ''),
                    ':questions': body.get('questions', []),
                    ':updated_at': datetime.now().isoformat()
                }
                if 'chat_history' in body:
                    update_expression += ', chat_history=:chat_history'
                    expression_values[':chat_history'] = body.get('chat_history', [])
                docs_table.update_item(
                    Key={'pk': f'USER#{user_id}', 'sk': f'DOC#{doc_id}'},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values
                )
            except Exception as e:
                print(f"⚠️ Document sync failed: {e}")
                return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': 'Failed to sync document'})}
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'Saved'})}
        
        # Chat endpoint with RAG and intent routing
        elif path == '/dev/chat' and method == 'POST':
            body = json.loads(event['body'])
            query = body.get('query') or body.get('messages', [{}])[-1].get('content', '')
            stream = body.get('stream', False)
            
            if not query:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'No query provided'})
                }
            
            # Intent routing
            intent = classify_intent(query)
            print(f"🎯 Intent: {intent}")
            
            # Summary intent: return stored artifact or generate on-the-fly
            if intent == 'summary':
                # Try to get stored summary from DynamoDB
                doc_preview = body.get('docPreview', '')[:12000]
                if doc_preview:
                    summary_data = generate_summary_and_questions(doc_preview, "This document")
                    return {
                        'statusCode': 200,
                        'headers': headers,
                        'body': json.dumps({
                            'response': summary_data.get('summary', ''),
                            'previewQuestions': summary_data.get('questions', []),
                            'citations': []
                        })
                    }
            
            # QA intent: use RAG
            doc_id = body.get('doc_id') or body.get('documentId')
            print(f"🔍 Searching for: {query[:100]} (doc: {doc_id})")
            matches = query_pinecone(query, doc_id=doc_id, top_k=8)
            print(f"📚 Found {len(matches)} relevant chunks")
            
            if stream:
                # Streaming response
                if matches:
                    stream_headers = {'Content-Type': 'text/event-stream'}
                    def generate():
                        for chunk in openai_chat_with_context(query, matches, stream=True):
                            yield f"data: {json.dumps(chunk)}\n\n"
                        yield "data: [DONE]\n\n"
                    return {
                        'statusCode': 200,
                        'headers': stream_headers,
                        'body': generate()
                    }
            
            # Non-streaming response
            if matches:
                result = openai_chat_with_context(query, matches)
            else:
                result = {
                    'answer': "I couldn't find relevant passages in your documents. The document may not have been vectorized yet.",
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
