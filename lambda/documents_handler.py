import json, os, boto3
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

def resp(code, body): return {"statusCode": code, "headers": CORS, "body": json.dumps(body)}

def lambda_handler(event, _ctx):
    if (event.get("requestContext",{}).get("http",{}) or {}).get("method") == "OPTIONS":
        return {"statusCode": 204, "headers": CORS}

    doc_id = (event.get("queryStringParameters") or {}).get("docId")
    if not doc_id: return resp(400, {"error":"docId is required"})

    try:
        item = DDB.get_item(TableName=DOCS_TABLE, Key={"docId":{"S":doc_id}}).get("Item")
        if not item:
            # Grace: treat as processing right after upload
            return resp(202, {"docId": doc_id, "status": "processing"})
        status = item["status"]["S"]
        body = {"docId": doc_id, "status": status}
        if "pages" in item: body["pages"] = int(item["pages"]["N"])
        if "error" in item: body["error"] = item["error"]["S"]

        if status == "ready": return resp(200, body)
        if status == "failed": return resp(409, body)
        return resp(202, body) # pending/processing
    except ClientError as e:
        print("ddb error:", e)
        return resp(202, {"docId": doc_id, "status": "processing"})