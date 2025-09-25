import json, os, base64

ORIGIN = "https://documentgpt.io"
CORS = {
    "Access-Control-Allow-Origin": ORIGIN,
    "Access-Control-Allow-Methods": "OPTIONS,GET",
    "Access-Control-Allow-Headers": "Content-Type,x-api-key,x-user-id",
    "Vary": "Origin",
}

def _resp(s,b=None): 
    return {"statusCode": s, "headers": CORS, "body": json.dumps(b or {})}

def _method(e): 
    return (e.get("requestContext",{}).get("http",{}) or {}).get("method") or e.get("httpMethod")

def lambda_handler(event, ctx):
    if _method(event) == "OPTIONS":
        return {"statusCode":204,"headers":CORS}
    
    try:
        # Get docId from query parameters
        doc_id = event.get("queryStringParameters", {}).get("docId") if event.get("queryStringParameters") else None
        
        if not doc_id:
            return _resp(400, {"error": "docId parameter required"})
        
        # Simulate document processing status
        # In production, this would check actual processing status
        return _resp(200, {
            "documents": [{"id": doc_id, "status": "ready"}],
            "phase": "ready",
            "message": "Document processed successfully"
        })
        
    except Exception as e:
        print("documents error:", repr(e))
        return _resp(500, {"error": "internal_error"})