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
TABLE = os.getenv("DOCS_TABLE","Documents")

def resp(code, body): return {"statusCode": code, "headers": CORS, "body": json.dumps(body)}

def lambda_handler(event, _):
    if (event.get("requestContext",{}).get("http",{}) or {}).get("method") == "OPTIONS":
        return {"statusCode": 204, "headers": CORS}

    q = event.get("queryStringParameters") or {}
    doc_id = q.get("docId")
    if not doc_id: return resp(400, {"error":"docId is required"})

    try:
        item = DDB.get_item(TableName=TABLE, Key={"docId":{"S":doc_id}}).get("Item")
    except ClientError as e:
        print("ddb:", e)
        return resp(202, {"docId": doc_id, "status":"processing"})

    if not item:
        return resp(202, {"docId": doc_id, "status":"processing"})

    status = item["status"]["S"]
    out = {"docId": doc_id, "status": status}
    if "pages" in item: out["pages"] = int(item["pages"]["N"])
    if "error" in item: out["error"] = item["error"]["S"]

    if status == "ready":   return resp(200, out)
    if status == "failed":  return resp(409, out)
    return resp(202, out)  # pending/processing