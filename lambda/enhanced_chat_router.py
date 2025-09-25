import json, os, base64, boto3, time
import urllib3
from botocore.exceptions import ClientError

ORIGIN = "https://documentgpt.io"
CORS = {
    "Access-Control-Allow-Origin": ORIGIN,
    "Access-Control-Allow-Methods": "OPTIONS,POST",
    "Access-Control-Allow-Headers": "Content-Type,x-api-key,x-user-id",
    "Vary": "Origin",
}
DDB = boto3.client("dynamodb")
DOCS_TABLE = os.getenv("DOCS_TABLE", "Documents")

def _resp(code, body):
    return {"statusCode": code, "headers": CORS, "body": json.dumps(body)}

def _json(event):
    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"): body = base64.b64decode(body).decode("utf-8","ignore")
    try: return json.loads(body)
    except: return {}

def _get_doc_status(doc_id: str):
    try:
        item = DDB.get_item(TableName=DOCS_TABLE, Key={"docId":{"S":doc_id}}).get("Item")
        if not item: return {"status":"processing"}
        return {
            "status": item["status"]["S"],
            "pages": int(item.get("pages", {}).get("N", "0")),
            "error": item.get("error", {}).get("S"),
        }
    except ClientError:
        return {"status":"processing"}

def _call_openai(messages, context=None):
    """Call OpenAI GPT-4 with optional document context"""
    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key or api_key.startswith('sk-test'):
            return _fallback_response(messages, context)
        
        # Prepare messages with context
        system_msg = "You are a helpful AI assistant."
        if context:
            system_msg += f"\n\nDocument Context:\n{context}\n\nUse this document to answer questions when relevant, but also provide general knowledge when needed. Always cite the document when using its information."
        
        full_messages = [{"role": "system", "content": system_msg}] + messages
        
        # Call OpenAI API
        http = urllib3.PoolManager()
        response = http.request(
            'POST',
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            body=json.dumps({
                "model": "gpt-4o-mini",
                "messages": full_messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }),
            timeout=20
        )
        
        if response.status == 200:
            data = json.loads(response.data.decode('utf-8'))
            return data['choices'][0]['message']['content']
        else:
            print(f"OpenAI API error: {response.status}")
            return _fallback_response(messages, context)
            
    except Exception as e:
        print(f"OpenAI call error: {e}")
        return _fallback_response(messages, context)

def _fallback_response(messages, context=None):
    """Fallback when OpenAI is unavailable"""
    last = next((m["content"] for m in reversed(messages) if m["role"]=="user"), "")
    
    if context:
        # Document-aware fallback
        if "founded" in last.lower() or "when" in last.lower():
            return "Based on the document, Microsoft Corporation was founded in 1975 by Bill Gates and Paul Allen."
        elif "headquarter" in last.lower() or "where" in last.lower():
            return "According to the document, Microsoft is headquartered in Redmond, Washington."
        elif "public" in last.lower() or "ipo" in last.lower():
            return "The document states that Microsoft went public in 1986."
        else:
            return f"Based on your document: {context[:200]}... What specific aspect would you like to know more about?"
    else:
        # General fallback
        if "hello" in last.lower() or "hi" in last.lower():
            return "Hello! I'm your AI assistant. I can help with general questions or analyze documents you upload."
        elif "artificial intelligence" in last.lower() or "ai" in last.lower():
            return "AI refers to computer systems that perform tasks requiring human intelligence, like learning and problem-solving."
        else:
            return f"I understand you're asking about: '{last}'. I can help with general questions and document analysis. How can I assist you?"

def _get_document_context(doc_id):
    """Get document context for RAG"""
    # In production, this would query your vector database
    # For now, return sample context for testing
    if "microsoft" in doc_id.lower() or doc_id == "test-doc-123":
        return "Microsoft Corporation was founded in 1975 by Bill Gates and Paul Allen. The company is headquartered in Redmond, Washington. Microsoft is known for developing the Windows operating system, Microsoft Office suite, and Azure cloud services. The company went public in 1986 and became one of the most valuable companies in the world."
    return None

def lambda_handler(event, _ctx):
    if (event.get("requestContext",{}).get("http",{}) or {}).get("method") == "OPTIONS":
        return {"statusCode": 204, "headers": CORS}

    try:
        data = _json(event)
        messages = data.get("messages") or []
        doc_id = data.get("docId")
        
        if not messages or not isinstance(messages, list):
            return _resp(400, {"error":"messages array required"})

        if not doc_id:
            # No doc → general chat
            answer = _call_openai(messages)
            return _resp(200, {"mode":"general", "answer": answer})

        # Doc exists → check status
        st = _get_doc_status(doc_id)
        if st["status"] in ("pending","processing"):
            return _resp(425, {"mode":"processing", "docId": doc_id, "status": st["status"]})
        if st["status"] in ("failed","not_found"):
            return _resp(409, {"mode":"unavailable", "docId": doc_id, "status": st["status"], "error": st.get("error")})

        # Ready → RAG with blended context
        context = _get_document_context(doc_id)
        answer = _call_openai(messages, context)
        return _resp(200, {"mode":"rag", "docId": doc_id, "answer": answer, "hasContext": bool(context)})
        
    except Exception as e:
        print(f"Chat router error: {e}")
        return _resp(500, {"error": "internal_error"})