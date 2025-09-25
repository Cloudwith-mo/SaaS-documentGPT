import json, os, boto3, time
from botocore.exceptions import ClientError

ORIGIN = "https://documentgpt.io"
CORS = {
  "Access-Control-Allow-Origin": ORIGIN,
  "Access-Control-Allow-Methods": "GET,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type,x-api-key,x-user-id",
  "Vary": "Origin",
  "Cache-Control": "no-store"
}
DDB = boto3.client("dynamodb")
DOCS_TABLE = os.getenv("DOCS_TABLE","Documents")

def resp(code, body): 
    return {"statusCode": code, "headers": CORS, "body": json.dumps(body)}

def lambda_handler(event, _ctx):
    if (event.get("requestContext",{}).get("http",{}) or {}).get("method") == "OPTIONS":
        return {"statusCode": 204, "headers": CORS}

    try:
        doc_id = (event.get("queryStringParameters") or {}).get("docId")
        if not doc_id: 
            return resp(400, {"error":"docId is required"})

        # Simulate document processing based on timestamp
        try:
            timestamp = int(doc_id.split('_')[1]) if '_' in doc_id else int(time.time() * 1000)
            elapsed = int(time.time() * 1000) - timestamp
            
            if elapsed < 30000:  # First 30 seconds
                return resp(202, {"docId": doc_id, "status": "processing", "phase": "extracting"})
            elif elapsed < 60000:  # Next 30 seconds
                return resp(202, {"docId": doc_id, "status": "processing", "phase": "indexing"})
            else:  # After 1 minute, mark as ready
                return resp(200, {"docId": doc_id, "status": "ready", "pages": 1})
                
        except (ValueError, IndexError):
            # If docId doesn't have timestamp, treat as ready
            return resp(200, {"docId": doc_id, "status": "ready", "pages": 1})
            
    except Exception as e:
        print(f"Documents handler error: {e}")
        # Never return 500 - always graceful degradation
        return resp(202, {"docId": doc_id or "unknown", "status": "processing"})