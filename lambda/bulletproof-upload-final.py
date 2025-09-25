import json, os, time, base64, boto3

ORIGIN = "https://documentgpt.io"
CORS = {
    "Access-Control-Allow-Origin": ORIGIN,
    "Access-Control-Allow-Methods": "OPTIONS,POST",
    "Access-Control-Allow-Headers": "Content-Type,x-api-key,x-user-id",
    "Vary": "Origin",
}
S3 = boto3.client("s3")
BUCKET = "documentgpt-uploads"

def _resp(status, body=None):
    return {"statusCode": status, "headers": CORS, "body": json.dumps(body or {})}

def _method(event):
    return (event.get("requestContext", {}).get("http", {}) or {}).get("method") or event.get("httpMethod")

def _json_body(event):
    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8", "ignore")
    try:
        return json.loads(body)
    except Exception:
        return {}

def lambda_handler(event, _ctx):
    if _method(event) == "OPTIONS":
        return {"statusCode": 204, "headers": CORS}

    try:
        data = _json_body(event)
        filename = (data.get("filename") or "").strip()
        content_type = (data.get("contentType") or "application/octet-stream").strip()

        if not filename:
            return _resp(400, {"error": "filename required"})
        
        ts = int(time.time() * 1000)
        doc_id = f"doc_{ts}"
        key = f"{doc_id}/{filename}"

        url = S3.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": BUCKET, "Key": key, "ContentType": content_type},
            ExpiresIn=600,
            HttpMethod="PUT",
        )
        
        get_url = S3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": BUCKET, "Key": key},
            ExpiresIn=600,
        )
        
        return _resp(200, {
            "docId": doc_id,
            "key": key,
            "uploadUrl": url,
            "downloadUrl": get_url,
            "filename": filename
        })
    except Exception as e:
        print("presign error:", repr(e))
        return _resp(500, {"error": "internal_error"})