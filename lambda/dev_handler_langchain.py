"""
DocumentGPT Dev Handler - LangChain + MCP Implementation
Serverless RAG with LangGraph orchestration and MCP tool integration
"""
import os
import json
import boto3
from datetime import datetime
from decimal import Decimal

import requests

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool

from agents import web_search
from config import get_settings, make_cors_headers

# Environment
settings = get_settings()
OPENAI_API_KEY = settings.openai_api_key
PINECONE_API_KEY = settings.pinecone_api_key
PINECONE_INDEX_HOST = settings.pinecone_index_host
DOC_TABLE = settings.doc_table

# Fix Pinecone cache permissions in Lambda
os.makedirs('/tmp/pinecone', exist_ok=True)
os.environ['HOME'] = '/tmp'
os.environ['PINECONE_CACHE_DIR'] = '/tmp/pinecone'

# AWS clients
dynamodb = boto3.resource('dynamodb')

# LangChain setup
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, openai_api_key=OPENAI_API_KEY)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)

# Pinecone HTTP helpers (works with legacy API key)
def pinecone_request(path, payload):
    url = f"https://{PINECONE_INDEX_HOST}{path}"
    headers = {
        "Content-Type": "application/json",
        "Api-Key": PINECONE_API_KEY,
    }
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if not response.ok:
        raise RuntimeError(
            f"Pinecone request failed ({response.status_code}): "
            f"{response.text[:300]}"
        )
    return response.json()


def pinecone_upsert(vectors):
    if not vectors:
        return
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = {"vectors": vectors[i:i + batch_size]}
        pinecone_request("/vectors/upsert", batch)


def pinecone_query(vector, doc_id=None, top_k=5):
    body = {
        "vector": vector,
        "topK": top_k,
        "includeMetadata": True,
    }
    if doc_id:
        body["filter"] = {"doc_id": {"$eq": doc_id}}
    data = pinecone_request("/query", body)
    return data.get("matches", [])

# Text splitter
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super().default(obj)

def make_headers(content_type='application/json', request_headers=None):
    return make_cors_headers(
        settings,
        request_headers=request_headers,
        content_type=content_type,
        allow_headers='Content-Type,Authorization',
        allow_methods='GET,POST,OPTIONS',
        vary_origin=True,
        send_wildcard_credentials=False,
    )

# MCP-style Tools
def pinecone_retrieve(query: str, doc_id: str = None) -> str:
    """Retrieve relevant document chunks from Pinecone vector database"""
    try:
        query_embedding = embeddings.embed_query(query)
        results = pinecone_query(query_embedding, doc_id=doc_id, top_k=5)

        if not results:
            return "No relevant passages found in documents."

        context = "\n\n".join(
            [
                f"[{idx + 1}] {match.get('metadata', {}).get('text', '')}"
                for idx, match in enumerate(results)
            ]
        )
        return f"RELEVANT PASSAGES:\n{context}"
    except Exception as e:
        print(f"⚠️ Pinecone retrieve error: {e}")
        return "Error retrieving from vector database."

def past_entries_search(query: str, user_id: str = "guest") -> str:
    """Search user's past journal entries"""
    try:
        query_embedding = embeddings.embed_query(query)
        # Search Pinecone with user_id filter for journals
        body = {
            "vector": query_embedding,
            "topK": 5,
            "includeMetadata": True,
            "filter": {"user_id": {"$eq": user_id}, "type": {"$eq": "journal"}}
        }
        data = pinecone_request("/query", body)
        results = data.get("matches", [])
        
        if not results:
            return "No relevant journal entries found."
        
        entries = "\n\n".join([
            f"[{idx + 1}] {match.get('metadata', {}).get('date', 'Unknown date')}: {match.get('metadata', {}).get('text', '')[:200]}..."
            for idx, match in enumerate(results)
        ])
        return f"PAST JOURNAL ENTRIES:\n{entries}"
    except Exception as e:
        print(f"⚠️ Journal search error: {e}")
        return "Error searching journal entries."

# Define tools
tools = [
    Tool(
        name="document_search",
        func=lambda q: pinecone_retrieve(q),
        description="Search user's uploaded documents for relevant information. Use this FIRST for any question about documents."
    ),
    Tool(
        name="journal_search",
        func=lambda q: past_entries_search(q),
        description="Search user's past journal entries for patterns, memories, or insights. Use when user asks about their past thoughts or feelings."
    ),
    Tool(
        name="web_search",
        func=web_search,
        description="Search the web for current information or facts not in documents. Use ONLY if document_search returns no results."
    )
]

# Create agent using conversational ReAct (better for ChatGPT models)
agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=3
)

def extract_pdf_text(content):
    """Extract text from PDF content"""
    try:
        import PyPDF2
        import io
        pdf_file = io.BytesIO(content.encode('latin-1') if isinstance(content, str) else content)
        reader = PyPDF2.PdfReader(pdf_file)
        return "\n".join([page.extract_text() for page in reader.pages])
    except Exception as e:
        print(f"⚠️ PDF extraction failed: {e}")
        return content

def generate_summary(text, doc_name):
    """Generate document summary using LLM"""
    try:
        prompt = f"Summarize this document in 3-5 sentences:\n\n{text[:8000]}"
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"⚠️ Summary generation failed: {e}")
        return f"Document {doc_name} uploaded successfully."

def lambda_handler(event, context):
    """Main Lambda handler"""
    request_headers = event.get('headers', {})
    headers = make_headers(request_headers=request_headers)
    
    try:
        # Parse request
        if 'requestContext' in event and 'http' in event['requestContext']:
            method = event['requestContext']['http']['method']
            path = event.get('rawPath', '')
        else:
            method = event.get('httpMethod', '')
            path = event.get('path', '')
        
        print(f"📍 {method} {path}")
        
        # OPTIONS
        if method == 'OPTIONS':
            return {'statusCode': 200, 'headers': headers, 'body': ''}
        
        # Health check
        if path == '/dev/health' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'status': 'healthy',
                    'environment': 'dev',
                    'langchain': True,
                    'mcp_enabled': True,
                    'timestamp': datetime.now().isoformat()
                })
            }
        
        # Upload endpoint
        if path == '/dev/upload' and method == 'POST':
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
            
            doc_id = f"doc_{int(datetime.now().timestamp())}"
            print(f"📄 Processing: {filename}")
            
            # Extract text if PDF
            if filename.lower().endswith('.pdf'):
                content = extract_pdf_text(content)
            
            # Split into chunks
            chunks = text_splitter.split_text(content)
            print(f"✂️  Split into {len(chunks)} chunks")
            
            limited_chunks = chunks[:200]
            if len(chunks) > len(limited_chunks):
                print(f"ℹ️ Limiting to {len(limited_chunks)} chunks for embedding to control costs")

            vectors = []
            batch_size = 40
            for offset in range(0, len(limited_chunks), batch_size):
                batch = limited_chunks[offset:offset + batch_size]
                try:
                    batch_embeddings = embeddings.embed_documents(batch)
                except Exception as embedding_error:
                    print(f"❌ Embedding batch failed: {embedding_error}")
                    continue

                for idx, embedding_vector in enumerate(batch_embeddings):
                    chunk_index = offset + idx
                    vectors.append({
                        "id": f"{doc_id}_chunk_{chunk_index}",
                        "values": embedding_vector,
                        "metadata": {
                            "doc_id": doc_id,
                            "doc_name": filename,
                            "chunk_index": chunk_index,
                            "text": batch[idx][:1000],
                        }
                    })

            try:
                pinecone_upsert(vectors)
                print(f"✅ Vectorized and stored {len(vectors)} vectors in Pinecone")
            except Exception as pinecone_error:
                import traceback
                print(f"❌ Pinecone upsert error: {pinecone_error}")
                print(f"📋 Traceback: {traceback.format_exc()}")
                return {
                    'statusCode': 502,
                    'headers': headers,
                    'body': json.dumps({
                        'error': 'Document indexing failed: Pinecone rejected the embeddings.',
                        'details': str(pinecone_error)[:200]
                    })
                }
            
            # Generate summary
            summary = generate_summary(content, filename)
            
            # Generate preview questions
            questions = [
                f"What are the main topics in {filename}?",
                "Can you summarize the key findings?",
                "What are the most important points?"
            ]
            
            # Save to DynamoDB
            docs_table = dynamodb.Table(DOC_TABLE)
            docs_table.put_item(Item={
                'pk': f'USER#{user_id}',
                'sk': f'DOC#{doc_id}',
                'doc_id': doc_id,
                'filename': filename,
                'content': content[:50000],
                'summary': summary,
                'questions': questions,
                'created_at': datetime.now().isoformat()
            })
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Document uploaded',
                    'doc_id': doc_id,
                    'artifact': {
                        'summary': summary,
                        'questions': questions
                    }
                })
            }
        
        # Chat endpoint with LangChain agent
        if path == '/dev/chat' and method == 'POST':
            body = json.loads(event['body'])
            query = body.get('query') or body.get('messages', [{}])[-1].get('content', '')
            doc_id = body.get('doc_id') or body.get('documentId')
            
            if not query:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'No query provided'})
                }
            
            print(f"💬 Query: {query[:100]}")
            
            # Modify pinecone_retrieve to use doc_id if provided
            if doc_id:
                tools[0].func = lambda q: pinecone_retrieve(q, doc_id)
            
            # Run agent
            try:
                result = agent_executor.invoke({"input": query, "chat_history": []})
                response_text = result.get('output', 'I could not process that request.')
                
                # Extract tool traces for citations
                intermediate_steps = result.get('intermediate_steps', [])
                citations = []
                for step in intermediate_steps:
                    if 'document_search' in str(step):
                        citations.append({
                            'tool': 'document_search',
                            'result': str(step)[:200]
                        })
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'response': response_text,
                        'citations': citations,
                        'tool_traces': [str(s) for s in intermediate_steps]
                    })
                }
            except Exception as e:
                print(f"❌ Agent error: {e}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({
                        'response': 'Sorry, I encountered an error processing your request.',
                        'error': str(e)
                    })
                }
        
        # Documents endpoint
        if path == '/documents' and method == 'GET':
            user_id = event.get('queryStringParameters', {}).get('user_id')
            if not user_id:
                return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'Missing user_id'})}
            
            docs_table = dynamodb.Table(DOC_TABLE)
            from boto3.dynamodb.conditions import Key
            resp = docs_table.query(
                KeyConditionExpression=Key('pk').eq(f'USER#{user_id}') & Key('sk').begins_with('DOC#')
            )
            
            documents = [{
                'doc_id': item.get('doc_id'),
                'filename': item.get('filename'),
                'summary': item.get('summary', ''),
                'questions': item.get('questions', []),
                'created_at': item.get('created_at')
            } for item in resp.get('Items', [])]
            
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'documents': documents}, cls=DecimalEncoder)}
        
        # Journal save endpoint
        if path == '/dev/journal' and method == 'POST':
            body = json.loads(event['body'])
            user_id = body.get('user_id', 'guest_dev')
            content = body.get('content', '')
            
            if not content:
                return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'No content'})}
            
            # Save to DynamoDB
            timestamp = int(datetime.now().timestamp())
            docs_table = dynamodb.Table(DOC_TABLE)
            docs_table.put_item(Item={
                'pk': f'USER#{user_id}',
                'sk': f'JOURNAL#{timestamp}',
                'content': content,
                'created_at': datetime.now().isoformat(),
                'type': 'journal'
            })
            
            # Vectorize and store in Pinecone
            try:
                chunks = text_splitter.split_text(content)
                chunk_embeddings = embeddings.embed_documents(chunks[:10])  # Limit to 10 chunks
                
                vectors = []
                for idx, (chunk, embedding) in enumerate(zip(chunks[:10], chunk_embeddings)):
                    vectors.append({
                        "id": f"{user_id}_journal_{timestamp}_{idx}",
                        "values": embedding,
                        "metadata": {
                            "user_id": user_id,
                            "type": "journal",
                            "date": datetime.now().isoformat(),
                            "text": chunk[:1000]
                        }
                    })
                
                pinecone_upsert(vectors)
                print(f"✅ Vectorized {len(vectors)} journal chunks")
            except Exception as e:
                print(f"⚠️ Journal vectorization failed: {e}")
            
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'Journal saved', 'timestamp': timestamp})}
        
        # Get journals endpoint
        if path == '/dev/journals' and method == 'GET':
            user_id = event.get('queryStringParameters', {}).get('user_id', 'guest_dev')
            
            docs_table = dynamodb.Table(DOC_TABLE)
            from boto3.dynamodb.conditions import Key
            resp = docs_table.query(
                KeyConditionExpression=Key('pk').eq(f'USER#{user_id}') & Key('sk').begins_with('JOURNAL#')
            )
            
            journals = [{
                'timestamp': item.get('sk').replace('JOURNAL#', ''),
                'content': item.get('content', ''),
                'created_at': item.get('created_at')
            } for item in resp.get('Items', [])]
            
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'journals': journals}, cls=DecimalEncoder)}
        
        # Usage endpoint
        if path == '/usage' and method == 'GET':
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'plan': 'premium', 'chats_used': 0, 'limit': -1})}
        
        return {'statusCode': 404, 'headers': headers, 'body': json.dumps({'error': 'Not found'})}
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
