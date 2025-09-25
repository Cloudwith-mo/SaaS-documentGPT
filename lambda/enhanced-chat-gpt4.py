import json, os, base64, boto3
from openai import OpenAI

ORIGIN = "https://documentgpt.io"
CORS = {
    "Access-Control-Allow-Origin": ORIGIN,
    "Access-Control-Allow-Methods": "OPTIONS,POST",
    "Access-Control-Allow-Headers": "Content-Type,x-api-key,x-user-id",
    "Vary": "Origin",
}

def _resp(s,b=None): 
    return {"statusCode": s, "headers": CORS, "body": json.dumps(b or {})}

def _method(e): 
    return (e.get("requestContext",{}).get("http",{}) or {}).get("method") or e.get("httpMethod")

def _json(e):
    b = e.get("body") or "{}"
    if e.get("isBase64Encoded"): 
        b = base64.b64decode(b).decode("utf-8","ignore")
    try: 
        return json.loads(b)
    except: 
        return {}

def get_openai_key():
    try:
        secrets = boto3.client('secretsmanager', region_name='us-east-1')
        response = secrets.get_secret_value(SecretId='openai-api-key')
        return json.loads(response['SecretString'])['api_key']
    except:
        return os.environ.get('OPENAI_API_KEY')

def get_document_context(doc_id):
    # Mock document retrieval - replace with actual RAG/vector search
    if doc_id == "test-doc":
        return "Microsoft Corporation was founded in 1975 by Bill Gates and Paul Allen. The company is headquartered in Redmond, Washington. Microsoft is known for developing the Windows operating system, Microsoft Office suite, and Azure cloud services. The company went public in 1986 and became one of the most valuable companies in the world."
    return None

def chat_with_gpt4(question, context=None):
    client = OpenAI(api_key=get_openai_key())
    
    if context:
        prompt = f"Based on this document: {context}\n\nQuestion: {question}\n\nAnswer based on the document content. If the document doesn't contain enough information, supplement with general knowledge and clearly indicate what comes from the document vs general knowledge."
    else:
        prompt = f"Question: {question}\n\nProvide a helpful answer using your general knowledge."
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.7
    )
    
    return response.choices[0].message.content

def lambda_handler(event, ctx):
    if _method(event) == "OPTIONS":
        return {"statusCode":204,"headers":CORS}
    
    try:
        data = _json(event)
        question = (data.get("question") or "").strip()
        doc_id = data.get("docId")
        
        if not question:
            return _resp(400, {"error":"question required"})
        
        # Get document context if docId provided
        doc_context = get_document_context(doc_id) if doc_id else None
        
        # Generate response with GPT-4
        answer = chat_with_gpt4(question, doc_context)
        
        response = {
            "answer": answer,
            "source": "document" if doc_context else "general_ai",
            "hasContext": bool(doc_context)
        }
        
        if doc_id:
            response["docId"] = doc_id
            
        return _resp(200, response)
        
    except Exception as e:
        print("chat error:", repr(e))
        return _resp(500, {"error":"internal_error"})