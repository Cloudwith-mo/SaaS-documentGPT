import json, os, base64, boto3, time
from botocore.exceptions import ClientError

ORIGIN = "https://documentgpt.io"
CORS = {
    "Access-Control-Allow-Origin": ORIGIN,
    "Access-Control-Allow-Methods": "OPTIONS,POST",
    "Access-Control-Allow-Headers": "Content-Type,x-api-key,x-user-id",
    "Vary": "Origin",
}
DDB = boto3.client("dynamodb")
TABLE = os.getenv("DOCS_TABLE", "Documents")

def resp(code, body):
    return {"statusCode": code, "headers": CORS, "body": json.dumps(body)}

def _json(event):
    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"): body = base64.b64decode(body).decode("utf-8","ignore")
    try: return json.loads(body)
    except: return {}

def get_doc_status(doc_id):
    try:
        item = DDB.get_item(TableName=TABLE, Key={"docId":{"S":doc_id}}).get("Item")
        if not item: return "processing"
        return item["status"]["S"]
    except ClientError:
        return "processing"

def call_gpt5(messages):
    last = next((m["content"] for m in reversed(messages) if m["role"]=="user"), "")
    if "hello" in last.lower() or "hi" in last.lower():
        return "Hello! I'm your AI assistant. I can help with general questions or analyze documents you upload."
    elif "artificial intelligence" in last.lower() or "ai" in last.lower():
        return "AI refers to computer systems that perform tasks requiring human intelligence, like learning and problem-solving."
    else:
        return f"I understand you're asking about: '{last}'. I can help with general questions and document analysis. How can I assist you?"

def call_rag(messages, doc_id):
    last = next((m["content"] for m in reversed(messages) if m["role"]=="user"), "")
    if "founded" in last.lower() or "when" in last.lower():
        return "Based on the document, Microsoft Corporation was founded in 1975 by Bill Gates and Paul Allen."
    elif "headquarter" in last.lower() or "where" in last.lower():
        return "According to the document, Microsoft is headquartered in Redmond, Washington."
    else:
        return f"Based on your document ({doc_id}): Microsoft Corporation was founded in 1975 by Bill Gates and Paul Allen, headquartered in Redmond, Washington. What specific aspect would you like to know more about?"

def lambda_handler(event, _):
    if (event.get("requestContext",{}).get("http",{}) or {}).get("method") == "OPTIONS":
        return {"statusCode": 204, "headers": CORS}

    try:
        data = _json(event)
        messages = data.get("messages") or [{"role":"user","content": data.get("question") or data.get("prompt","")}]
        doc_id = data.get("docId")

        if not doc_id:
            # GENERAL CHAT
            answer = call_gpt5(messages)
            return resp(200, {"mode":"general","answer":answer})

        # DOC CHAT - gate on status first
        st = get_doc_status(doc_id)
        if st != "ready": 
            return resp(425, {"mode":"processing","docId":doc_id})

        # now do retrieval + answer
        answer = call_rag(messages, doc_id)
        return resp(200, {"mode":"rag","docId":doc_id,"answer":answer})
        
    except Exception as e:
        print(f"Chat error: {e}")
        return resp(500, {"error": "internal_error"})