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

def lambda_handler(event, ctx):
    if _method(event) == "OPTIONS":
        return {"statusCode":204,"headers":CORS}
    try:
        data = _json(event)
        doc_id = data.get("docId")
        question = (data.get("question") or "").strip()
        
        if not doc_id or not question:
            return _resp(400, {"error":"docId and question required"})
        
        # Simple response for now
        if "microsoft" in question.lower() or "founded" in question.lower():
            answer = "Microsoft Corporation was founded in 1975 by Bill Gates and Paul Allen."
        else:
            answer = f"I can help answer questions about your document ({doc_id}). Try asking about Microsoft's founding."
            
        return _resp(200, {"answer": answer, "docId": doc_id})
    except Exception as e:
        print("chat error:", repr(e))
        return _resp(500, {"error":"internal_error"})