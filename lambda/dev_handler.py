"""
DocumentGPT Dev Handler - LangGraph Orchestration + MCP-style Tooling
"""
import base64
import json
import mimetypes
import os
import traceback
from datetime import datetime
from decimal import Decimal
from typing import Optional

import boto3

import requests
from boto3.dynamodb.conditions import Key
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import Tool
from langchain_core.messages import HumanMessage, SystemMessage

from agents import DEFAULT_RESEARCH_SYSTEM_PROMPT, build_langgraph_agent, web_search
from config import get_settings, make_cors_headers
from knowledge_graph import (
    entities_to_document_payload,
    format_document_entities,
    format_entity_detail,
    format_user_entities,
    run_entity_extraction,
)

# Environment
settings = get_settings()
OPENAI_API_KEY = settings.openai_api_key
PINECONE_API_KEY = settings.pinecone_api_key
PINECONE_INDEX_NAME = settings.pinecone_index or 'documentgpt-dev'
PINECONE_INDEX_HOST = settings.pinecone_index_host
DOC_TABLE = settings.doc_table
MEDIA_BUCKET = settings.media_bucket
MEDIA_QUEUE_URL = settings.media_queue_url

# Ensure Pinecone cache can write inside Lambda /tmp filesystem
os.environ["HOME"] = "/tmp"
os.environ["PINECONE_CACHE_DIR"] = "/tmp/pinecone"
os.environ["XDG_CACHE_HOME"] = "/tmp/.cache"
os.environ["XDG_CONFIG_HOME"] = "/tmp/.config"
os.makedirs("/tmp/.cache", exist_ok=True)
os.makedirs("/tmp/.config", exist_ok=True)
os.makedirs(os.environ["PINECONE_CACHE_DIR"], exist_ok=True)

# AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
sqs = boto3.client('sqs')

# LangChain setup
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, openai_api_key=OPENAI_API_KEY)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)

# Pinecone REST helpers
def pinecone_request(path, payload):
    if not PINECONE_INDEX_HOST:
        raise RuntimeError("PINECONE_INDEX_HOST not configured")

    url = f"https://{PINECONE_INDEX_HOST}{path}"
    headers = {
        "Content-Type": "application/json",
        "Api-Key": PINECONE_API_KEY,
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
    except requests.RequestException as request_error:
        raise RuntimeError(f"Pinecone request failed: {request_error}") from request_error

    if not response.ok:
        raise RuntimeError(
            f"Pinecone request failed ({response.status_code}): {response.text[:300]}"
        )
    return response.json()


def pinecone_upsert(vectors):
    if not vectors:
        return

    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = {"vectors": vectors[i : i + batch_size]}
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
            if obj == obj.to_integral_value():
                return int(obj)
            return float(obj)
        return super().default(obj)

def make_headers(content_type='application/json', request_headers=None):
    return make_cors_headers(
        settings,
        request_headers=request_headers,
        content_type=content_type,
        add_origin_header=True,
    )

# MCP-style Tools
def pinecone_retrieve(query: str, doc_id: str = None) -> str:
    """Retrieve relevant document chunks from Pinecone vector database"""
    try:
        query_embedding = embeddings.embed_query(query)
        results = pinecone_query(query_embedding, doc_id=doc_id, top_k=5)

        if not results:
            return "No relevant passages found in documents."

        passages = []
        for idx, match in enumerate(results):
            metadata = match.get("metadata") or {}
            text = metadata.get("text") or ""
            if not text:
                continue
            passages.append(f"[{idx + 1}] {text}")

        if not passages:
            return "No relevant passages found in documents."

        context = "\n\n".join(passages)
        return f"RELEVANT PASSAGES:\n{context}"
    except Exception as e:
        print(f"⚠️ Pinecone retrieve error: {e}")
        traceback.print_exc()
        return "Error retrieving from vector database."

# Define tools (mutable list so we can swap document filter per-request)
tools = [
    Tool(
        name="document_search",
        func=lambda q: pinecone_retrieve(q),
        description="Search user's uploaded documents for relevant information. Use this FIRST for any question about documents.",
    ),
    Tool(
        name="web_search",
        func=web_search,
        description="Search the web for current information or facts not in documents. Use ONLY if document_search returns no results.",
    ),
]

RESEARCH_SYSTEM_PROMPT = DEFAULT_RESEARCH_SYSTEM_PROMPT

research_agent = build_langgraph_agent(llm, RESEARCH_SYSTEM_PROMPT, tools)

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


def _prepare_doc_entities(raw_entities):
    """Convert entity payload ready for DynamoDB storage."""
    doc_entities = []
    for entity in raw_entities:
        doc_entities.append(
            {
                'entity_id': entity['entity_id'],
                'name': entity['name'],
                'type': entity['type'],
                'salience': Decimal(str(entity['salience'])),
                'mentions': entity.get('mentions', []),
            }
        )
    return doc_entities


def _upsert_knowledge_graph(table, user_id, doc_id, doc_entities):
    """Persist entity aggregates and document edges for the knowledge graph."""
    if not doc_entities:
        return

    now_iso = datetime.now().isoformat()
    for entity in doc_entities:
        user_pk = f'USER#{user_id}'
        entity_sk = f'ENTITY#{entity["entity_id"]}'
        key = {'pk': user_pk, 'sk': entity_sk}

        existing_resp = table.get_item(Key=key)
        existing = existing_resp.get('Item') if isinstance(existing_resp, dict) else None
        doc_ids = set(existing.get('doc_ids', [])) if existing else set()
        doc_ids.add(doc_id)

        mentions = existing.get('mentions', []) if existing else []
        for mention in entity.get('mentions', []):
            if mention and mention not in mentions and len(mentions) < 10:
                mentions.append(mention)

        created_at = existing.get('created_at') if existing else now_iso

        table.put_item(Item={
            'pk': user_pk,
            'sk': entity_sk,
            'entity_id': entity['entity_id'],
            'entity_name': entity['name'],
            'entity_type': entity['type'],
            'doc_ids': sorted(doc_ids),
            'doc_count': Decimal(str(len(doc_ids))),
            'mentions': mentions,
            'salience': entity['salience'],
            'created_at': created_at,
            'updated_at': now_iso,
            'last_seen_doc_id': doc_id,
        })

        table.put_item(Item={
            'pk': f'DOC#{doc_id}',
            'sk': f'ENTITY#{entity["entity_id"]}',
            'doc_id': doc_id,
            'entity_id': entity['entity_id'],
            'entity_name': entity['name'],
            'entity_type': entity['type'],
            'salience': entity['salience'],
            'mentions': entity.get('mentions', []),
            'user_id': user_id,
            'updated_at': now_iso,
        })


def _list_user_entities(table, user_id):
    resp = table.query(
        KeyConditionExpression=Key('pk').eq(f'USER#{user_id}') & Key('sk').begins_with('ENTITY#')
    )
    return format_user_entities(resp.get('Items', []))


def _get_document_entities(table, doc_id):
    resp = table.query(
        KeyConditionExpression=Key('pk').eq(f'DOC#{doc_id}') & Key('sk').begins_with('ENTITY#')
    )
    return format_document_entities(resp.get('Items', []))


def _fetch_document_metadata(table, user_id, doc_ids):
    doc_items = []
    for doc_id in doc_ids:
        response = table.get_item(Key={'pk': f'USER#{user_id}', 'sk': f'DOC#{doc_id}'})
        item = response.get('Item') if isinstance(response, dict) else None
        if item:
            doc_items.append(item)
    return doc_items


def _get_entity_detail_payload(table, user_id, entity_id):
    response = table.get_item(Key={'pk': f'USER#{user_id}', 'sk': f'ENTITY#{entity_id}'})
    entity_item = response.get('Item') if isinstance(response, dict) else None
    if not entity_item:
        return None

    doc_ids = entity_item.get('doc_ids', []) or []
    doc_items = _fetch_document_metadata(table, user_id, doc_ids)
    return format_entity_detail(entity_item, doc_items)

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
        
        query_params = event.get('queryStringParameters') or {}

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

        if path == '/dev/knowledge-graph/entities' and method == 'GET':
            user_id = query_params.get('user_id') or query_params.get('userId')
            if not user_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing user_id'})
                }

            docs_table = dynamodb.Table(DOC_TABLE)
            try:
                entities = _list_user_entities(docs_table, user_id)
            except Exception as graph_error:  # noqa: BLE001
                print(f"⚠️ Knowledge graph list failed: {graph_error}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to load knowledge graph'})
                }

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'user_id': user_id, 'entities': entities}, cls=DecimalEncoder)
            }

        if path.startswith('/dev/knowledge-graph/entities/') and method == 'GET':
            user_id = query_params.get('user_id') or query_params.get('userId')
            if not user_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing user_id'})
                }

            parts = path.rstrip('/').split('/')
            if len(parts) < 5:
                return {'statusCode': 404, 'headers': headers, 'body': json.dumps({'error': 'Entity not found'})}
            entity_id = parts[4]

            docs_table = dynamodb.Table(DOC_TABLE)
            try:
                detail = _get_entity_detail_payload(docs_table, user_id, entity_id)
            except Exception as graph_error:  # noqa: BLE001
                print(f"⚠️ Entity detail load failed: {graph_error}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to load entity detail'})
                }

            if not detail:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': 'Entity not found'})
                }

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(detail, cls=DecimalEncoder)
            }

        if path.startswith('/dev/knowledge-graph/docs/') and method == 'GET':
            parts = path.rstrip('/').split('/')
            if len(parts) < 5:
                return {'statusCode': 404, 'headers': headers, 'body': json.dumps({'error': 'Document not found'})}
            doc_id = parts[4]

            docs_table = dynamodb.Table(DOC_TABLE)
            try:
                entities = _get_document_entities(docs_table, doc_id)
            except Exception as graph_error:  # noqa: BLE001
                print(f"⚠️ Document entity load failed: {graph_error}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to load document entities'})
                }

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'doc_id': doc_id, 'entities': entities}, cls=DecimalEncoder)
            }

        # Upload endpoint
        if path in ('/dev/upload', '/upload') and method == 'POST':
            body = json.loads(event['body'])
            user_id = body.get('user_id', 'guest_dev')
            filename = body.get('filename')
            content = body.get('content')
            content_base64 = body.get('content_base64')
            media_type = body.get('media_type')

            if not filename:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing filename'})
                }

            if not content and not content_base64:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing content'})
                }

            doc_id = f"doc_{int(datetime.now().timestamp())}"
            print(f"📄 Processing: {filename}")

            extension = os.path.splitext(filename)[1].lower()
            guessed_type, _ = mimetypes.guess_type(filename)
            media_type = media_type or guessed_type or 'application/octet-stream'

            is_text_like = media_type.startswith('text/') or extension in {'.txt', '.md', '.markdown', '.csv'}
            is_pdf = extension == '.pdf' or media_type == 'application/pdf'

            binary_payload: Optional[bytes] = None

            if content_base64:
                try:
                    binary_payload = base64.b64decode(content_base64)
                except Exception:
                    return {
                        'statusCode': 400,
                        'headers': headers,
                        'body': json.dumps({'error': 'Invalid base64 payload'})
                    }

            if binary_payload and not (is_text_like or is_pdf):
                if not MEDIA_BUCKET or not MEDIA_QUEUE_URL:
                    return {
                        'statusCode': 500,
                        'headers': headers,
                        'body': json.dumps({'error': 'Media processing not configured'})
                    }

                s3_key = f"uploads/{user_id}/{doc_id}/{filename}"
                s3.put_object(
                    Bucket=MEDIA_BUCKET,
                    Key=s3_key,
                    Body=binary_payload,
                    ContentType=media_type,
                )
                print(f"☁️  Stored media in S3 at {s3_key}")

                docs_table = dynamodb.Table(DOC_TABLE)
                docs_table.put_item(Item={
                    'pk': f'USER#{user_id}',
                    'sk': f'DOC#{doc_id}',
                    'doc_id': doc_id,
                    'filename': filename,
                    'media_type': media_type,
                    'processing_status': 'processing',
                    'created_at': datetime.now().isoformat()
                })

                job_payload = {
                    'user_id': user_id,
                    'doc_id': doc_id,
                    'bucket': MEDIA_BUCKET,
                    'key': s3_key,
                    'media_type': media_type,
                    'metadata': body.get('metadata') or {},
                    'segments': body.get('segments') or [],
                }
                sqs.send_message(QueueUrl=MEDIA_QUEUE_URL, MessageBody=json.dumps(job_payload))
                print(f"📬 Enqueued media processing job for {doc_id}")

                return {
                    'statusCode': 202,
                    'headers': headers,
                    'body': json.dumps({
                        'message': 'Media received and queued for processing',
                        'doc_id': doc_id,
                        'processing_status': 'processing'
                    })
                }

            if binary_payload and (is_text_like or is_pdf):
                if is_pdf:
                    content = extract_pdf_text(binary_payload)
                else:
                    content = binary_payload.decode('utf-8', errors='ignore')

            if is_pdf and not binary_payload:
                content = extract_pdf_text(content)

            if not content:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Unable to process document content'})
                }

            chunks = text_splitter.split_text(content)
            print(f"✂️  Split into {len(chunks)} chunks")

            print("🔧 Preparing Pinecone payload", flush=True)
            try:
                embeddings_list = embeddings.embed_documents(chunks)
            except Exception as embed_error:
                print(f"❌ Embedding error: {embed_error!r}")
                traceback.print_exc()
                raise

            print("📌 Upserting embeddings to Pinecone", flush=True)
            vectors = []
            for idx, (chunk, vector) in enumerate(zip(chunks, embeddings_list)):
                vectors.append(
                    {
                        "id": f"{doc_id}-{idx}",
                        "values": vector,
                        "metadata": {
                            "doc_id": doc_id,
                            "doc_name": filename,
                            "chunk": idx,
                            "text": chunk,
                            "user_id": user_id,
                        },
                    }
                )

            try:
                pinecone_upsert(vectors)
            except Exception as pinecone_error:
                print(f"❌ Pinecone upsert error: {pinecone_error!r}")
                traceback.print_exc()
                raise
            print("✅ Vectorized and stored in Pinecone")

            print("🧠 Generating summary", flush=True)
            summary = generate_summary(content, filename)
            print("🧠 Summary generated", flush=True)

            print("🕸️ Extracting entities for knowledge graph", flush=True)
            doc_entities = []
            try:
                extracted_entities = run_entity_extraction(content, llm)
                entity_payload = entities_to_document_payload(extracted_entities)
                doc_entities = _prepare_doc_entities(entity_payload)
                print(f"🕸️ Identified {len(doc_entities)} entities", flush=True)
            except Exception as entity_error:  # noqa: BLE001
                print(f"⚠️ Entity extraction failed: {entity_error}")
                doc_entities = []

            questions = [
                f"What are the main topics in {filename}?",
                "Can you summarize the key findings?",
                "What are the most important points?"
            ]

            docs_table = dynamodb.Table(DOC_TABLE)
            print("🗄️  Writing document metadata to DynamoDB", flush=True)
            docs_table.put_item(Item={
                'pk': f'USER#{user_id}',
                'sk': f'DOC#{doc_id}',
                'doc_id': doc_id,
                'filename': filename,
                'media_type': media_type,
                'content': content[:50000],
                'summary': summary,
                'questions': questions,
                'processing_status': 'ready',
                'created_at': datetime.now().isoformat(),
                'entities': doc_entities,
                'knowledge_graph_state': 'indexed' if doc_entities else 'no_entities',
            })
            print("🗄️  DynamoDB write complete", flush=True)

            try:
                _upsert_knowledge_graph(docs_table, user_id, doc_id, doc_entities)
            except Exception as kg_error:  # noqa: BLE001
                print(f"⚠️ Knowledge graph persistence failed: {kg_error}")

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
            original_func = tools[0].func
            if doc_id:
                tools[0].func = lambda q, doc_id=doc_id: pinecone_retrieve(q, doc_id)
            
            # Run agent
            try:
                response_text, citations, tool_traces = research_agent(query)
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'response': response_text,
                        'citations': citations,
                        'tool_traces': tool_traces
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
            finally:
                tools[0].func = original_func

        if path == '/dev/autocomplete' and method == 'POST':
            try:
                body = json.loads(event.get('body') or '{}')
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Invalid JSON body'})
                }

            context = (body.get('context') or '').strip()
            max_tokens = int(body.get('max_tokens', 30))
            style = (body.get('style') or '').lower().strip()

            if len(context) < 20:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Context too short'})
                }

            max_tokens = max(10, min(max_tokens, 80))

            style_instructions = {
                'hemingway': "Write with short, vivid sentences and concrete imagery, reminiscent of Ernest Hemingway.",
                'academic': "Adopt a formal, academic tone with precise language and clear argumentation.",
                'casual': "Use a relaxed, conversational tone as if speaking with a friend.",
                'storyteller': "Continue with descriptive, narrative prose that builds atmosphere and emotion.",
                'poetic': "Respond with lyrical, poetic language that leans on metaphor and rhythm.",
            }

            system_prompt = (
                "You are DocumentGPT's AI co-writer. Continue the user's draft naturally, matching their tense, "
                "perspective, and voice. Output only the continuation—no preamble, no closing quotes."
            )
            if style in style_instructions:
                system_prompt += f" {style_instructions[style]}"

            context_window = context[-8000:]
            desired_words = max_tokens // 2
            human_prompt = (
                "Draft continuation request:\n"
                "---------------------------\n"
                f"{context_window}\n\n"
                f"Continue in the same format with roughly {desired_words}-{desired_words + 3} words."
            )

            try:
                response = llm.invoke(
                    [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=human_prompt),
                    ],
                    max_tokens=max_tokens,
                )
                completion = (response.content or "").strip().strip('"').strip("'")

                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({'completion': completion})
                }
            except Exception as err:
                print(f"❌ Autocomplete error: {err}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({
                        'error': 'Failed to generate completion',
                        'detail': str(err)
                    })
                }

        # Documents endpoint
        if path == '/documents' and method == 'GET':
            user_id = query_params.get('user_id')
            if not user_id:
                return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'Missing user_id'})}

            docs_table = dynamodb.Table(DOC_TABLE)
            resp = docs_table.query(
                KeyConditionExpression=Key('pk').eq(f'USER#{user_id}') & Key('sk').begins_with('DOC#')
            )
            
            documents = [{
                'doc_id': item.get('doc_id'),
                'filename': item.get('filename'),
                'summary': item.get('summary', ''),
                'questions': item.get('questions', []),
                'created_at': item.get('created_at'),
                'entities': item.get('entities', []),
                'knowledge_graph_state': item.get('knowledge_graph_state', 'unknown'),
            } for item in resp.get('Items', [])]
            
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'documents': documents}, cls=DecimalEncoder)}
        
        # Usage endpoint
        if path == '/usage' and method == 'GET':
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'plan': 'premium', 'chats_used': 0, 'limit': -1})}
        
        return {'statusCode': 404, 'headers': headers, 'body': json.dumps({'error': 'Not found'})}
    
    except Exception as e:
        print(f"❌ Error: {e!r}")
        traceback.print_exc()
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
