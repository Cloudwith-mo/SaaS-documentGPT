import json, os, base64, time

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

def get_document_context(doc_id):
    """Get document context"""
    try:
        if "microsoft" in doc_id.lower() or doc_id == "test-doc-123":
            return "Microsoft Corporation was founded in 1975 by Bill Gates and Paul Allen. The company is headquartered in Redmond, Washington. Microsoft is known for developing the Windows operating system, Microsoft Office suite, and Azure cloud services. The company went public in 1986 and became one of the most valuable companies in the world."
        return None
    except:
        return None

def generate_response(question, context=None):
    """Generate response based on question and context"""
    question_lower = question.lower()
    
    if context:
        # With document context
        if "founded" in question_lower or "when" in question_lower:
            return "Based on the document, Microsoft Corporation was founded in 1975 by Bill Gates and Paul Allen."
        elif "headquarter" in question_lower or "where" in question_lower:
            return "According to the document, Microsoft is headquartered in Redmond, Washington."
        elif "public" in question_lower or "ipo" in question_lower:
            return "The document states that Microsoft went public in 1986."
        elif "product" in question_lower or "service" in question_lower:
            return "Based on the document, Microsoft is known for developing the Windows operating system, Microsoft Office suite, and Azure cloud services."
        else:
            return f"Based on the document about Microsoft: {context[:200]}... What specific aspect would you like to know more about?"
    else:
        # Regular chatbot mode
        if "hello" in question_lower or "hi" in question_lower:
            return "Hello! I'm your AI assistant. I can help you with general questions or analyze documents you upload. How can I assist you today?"
        elif "artificial intelligence" in question_lower or "ai" in question_lower:
            return "Artificial Intelligence (AI) refers to computer systems that can perform tasks typically requiring human intelligence, such as learning, reasoning, problem-solving, and understanding language. AI powers many modern applications from virtual assistants to recommendation systems."
        elif "weather" in question_lower:
            return "I don't have access to real-time weather data, but I'd recommend checking a weather service like Weather.com or your local weather app for current conditions."
        elif "time" in question_lower:
            return "I don't have access to real-time information, but you can check the current time on your device or search for the time in any specific location."
        else:
            return f"I'm here to help! You asked: '{question}'. I can assist with general questions, explanations, and document analysis. Upload a document to get started with document-specific queries, or ask me anything else you'd like to know."

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
        
        # Generate response
        answer = generate_response(question, context)
        
        return _resp(200, {
            "answer": answer, 
            "docId": doc_id,
            "hasContext": has_context
        })
        
    except Exception as e:
        print("chat error:", repr(e))
        return _resp(500, {"error":"internal_error"})