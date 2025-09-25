import json, os, base64, time
import boto3

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

def call_openai(question, context=None):
    """Call OpenAI API with or without document context"""
    try:
        import requests
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return "OpenAI API key not configured"
        
        if context:
            # With document context
            system_prompt = f"You are a helpful assistant. Use the following document context to answer questions, but also provide general knowledge when relevant.\n\nDocument Context:\n{context}"
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        else:
            # Regular chatbot mode
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant. Provide accurate and helpful responses."},
                {"role": "user", "content": question}
            ]
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",  # Using GPT-4o-mini for cost efficiency
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            },
            timeout=25
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return f"OpenAI API error: {response.status_code}"
            
    except Exception as e:
        print(f"OpenAI call error: {e}")
        return "Sorry, I'm having trouble processing your request right now."

def get_document_context(doc_id):
    """Get document context from S3 or database"""
    try:
        # For now, return sample context based on docId
        # In production, this would fetch from vector database
        if "microsoft" in doc_id.lower() or doc_id == "test-doc-123":
            return "Microsoft Corporation was founded in 1975 by Bill Gates and Paul Allen. The company is headquartered in Redmond, Washington. Microsoft is known for developing the Windows operating system, Microsoft Office suite, and Azure cloud services. The company went public in 1986 and became one of the most valuable companies in the world."
        return None
    except Exception as e:
        print(f"Context retrieval error: {e}")
        return None

def lambda_handler(event, ctx):
    if _method(event) == "OPTIONS":
        return {"statusCode":204,"headers":CORS}
    try:
        data = _json(event)
        doc_id = data.get("docId")
        question = (data.get("question") or "").strip()
        
        if not question:
            return _resp(400, {"error":"question required"})
        
        # Get document context if docId provided
        context = None
        has_context = False
        if doc_id:
            context = get_document_context(doc_id)
            has_context = bool(context)
        
        # Call OpenAI with or without context
        answer = call_openai(question, context)
        
        return _resp(200, {
            "answer": answer, 
            "docId": doc_id,
            "hasContext": has_context
        })
        
    except Exception as e:
        print("chat error:", repr(e))
        return _resp(500, {"error":"internal_error"})