"""
DocumentGPT Dev Handler - LangGraph Orchestration + MCP-style Tooling
"""
import os
import json
import boto3
from datetime import datetime
from decimal import Decimal
from typing import Annotated, List, Optional, TypedDict
import operator

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import Tool
from pinecone import Pinecone
from duckduckgo_search import DDGS

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

# Environment
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
PINECONE_API_KEY = os.environ['PINECONE_API_KEY']
PINECONE_INDEX_NAME = os.environ.get('PINECONE_INDEX', 'documentgpt-dev')
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get('ALLOWED_ORIGINS', 'https://documentgpt.io').split(',')]
DEFAULT_ORIGIN = ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else '*'

# AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# LangChain setup
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, openai_api_key=OPENAI_API_KEY)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)

# Pinecone - lazy init
vector_store = None

def get_vector_store():
    global vector_store
    if vector_store is None:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
        vector_store = PineconeVectorStore(index=index, embedding=embeddings, text_key="text")
    return vector_store

# Text splitter
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super().default(obj)

def make_headers(content_type='application/json', request_headers=None):
    req_headers = request_headers or {}
    request_origin = req_headers.get('origin') or req_headers.get('Origin')
    cors_origin = request_origin if request_origin in ALLOWED_ORIGINS else DEFAULT_ORIGIN
    return {
        'Content-Type': content_type,
        'Access-Control-Allow-Origin': cors_origin,
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Access-Control-Allow-Credentials': 'true' if cors_origin != '*' else 'false'
    }

# MCP-style Tools
def pinecone_retrieve(query: str, doc_id: str = None) -> str:
    """Retrieve relevant document chunks from Pinecone vector database"""
    try:
        vs = get_vector_store()
        filter_dict = {"doc_id": doc_id} if doc_id else None
        results = vs.similarity_search(query, k=5, filter=filter_dict)
        
        if not results:
            return "No relevant passages found in documents."
        
        context = "\n\n".join([f"[{i+1}] {doc.page_content}" for i, doc in enumerate(results)])
        return f"RELEVANT PASSAGES:\n{context}"
    except Exception as e:
        print(f"⚠️ Pinecone retrieve error: {e}")
        return "Error retrieving from vector database."

def web_search(query: str) -> str:
    """Search the web for supplemental information"""
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No web results found."
        
        snippets = [f"• {r['title']}: {r['body'][:200]}... (source: {r['href']})" for r in results]
        return "WEB RESULTS:\n" + "\n".join(snippets)
    except Exception as e:
        print(f"⚠️ Web search error: {e}")
        return "Web search unavailable."

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


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]


RESEARCH_SYSTEM_PROMPT = (
    "You are DocumentGPT, an AI assistant that helps users understand their documents.\n"
    "IMPORTANT RULES:\n"
    "1. ALWAYS use document_search FIRST for any question about the user's documents.\n"
    "2. Only use web_search if document_search returns no results or the user requests up-to-date context.\n"
    "3. Cite sources with [1], [2], etc. when quoting documents. Cite the most relevant passage.\n"
    "4. If you can't find information, say so clearly and suggest next steps.\n"
    "5. Keep answers concise but informative, focusing on evidence from the documents."
)


def build_langgraph_agent(system_prompt: str, toolset: List[Tool]):
    """Compile a LangGraph agent with ReAct-style tool usage."""
    bound_llm = llm.bind_tools(toolset)
    tool_node = ToolNode(toolset)

    def call_model(state: AgentState):
        response = bound_llm.invoke(state["messages"])
        return {"messages": [response]}

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")
    compiled_app = workflow.compile()

    def run(query: str, chat_history: Optional[List[BaseMessage]] = None):
        messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
        if chat_history:
            messages.extend(chat_history)
        messages.append(HumanMessage(content=query))
        result_state = compiled_app.invoke({"messages": messages})
        message_history = result_state["messages"]

        # Extract final assistant response
        ai_messages = [m for m in message_history if isinstance(m, AIMessage)]
        response_text = ai_messages[-1].content if ai_messages else ""

        # Gather tool traces for citations/debugging
        citations = []
        tool_traces = []
        for m in message_history:
            if isinstance(m, ToolMessage):
                content_str = m.content if isinstance(m.content, str) else json.dumps(m.content)
                citations.append({
                    "tool": m.name or "tool",
                    "result": content_str[:200],
                })
                tool_traces.append(content_str)

        return response_text, citations, tool_traces

    return run


research_agent = build_langgraph_agent(RESEARCH_SYSTEM_PROMPT, tools)

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
            
            # Create metadata for each chunk
            metadatas = [{"doc_id": doc_id, "doc_name": filename, "chunk": i} for i in range(len(chunks))]
            
            # Upsert to Pinecone
            vs = get_vector_store()
            vs.add_texts(texts=chunks, metadatas=metadatas)
            print(f"✅ Vectorized and stored in Pinecone")
            
            # Generate summary
            summary = generate_summary(content, filename)
            
            # Generate preview questions
            questions = [
                f"What are the main topics in {filename}?",
                "Can you summarize the key findings?",
                "What are the most important points?"
            ]
            
            # Save to DynamoDB
            docs_table = dynamodb.Table('docgpt')
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
            user_id = event.get('queryStringParameters', {}).get('user_id')
            if not user_id:
                return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'Missing user_id'})}
            
            docs_table = dynamodb.Table('docgpt')
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
        
        # Usage endpoint
        if path == '/usage' and method == 'GET':
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'plan': 'premium', 'chats_used': 0, 'limit': -1})}
        
        return {'statusCode': 404, 'headers': headers, 'body': json.dumps({'error': 'Not found'})}
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
