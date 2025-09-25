import json
import boto3
import uuid
import time

ORIGIN = "https://documentgpt.io"
CORS = {
    "Access-Control-Allow-Origin": ORIGIN,
    "Access-Control-Allow-Methods": "OPTIONS,POST",
    "Access-Control-Allow-Headers": "Content-Type,x-api-key,x-user-id",
    "Vary": "Origin",
}

def resp(status, body=None):
    return {"statusCode": status, "headers": CORS, "body": json.dumps(body or {})}

def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return resp(204)
    
    try:
        s3_client = boto3.client('s3')
        body = json.loads(event.get("body") or "{}")
        filename = body.get("filename", "document.txt")
        content_type = body.get("contentType", "text/plain")
        
        doc_id = f"doc_{int(time.time() * 1000)}_{uuid.uuid4().hex[:12]}"
        file_key = f"{doc_id}/{filename}"
        
        upload_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': 'documentgpt-uploads', 'Key': file_key, 'ContentType': content_type},
            ExpiresIn=300
        )
        
        return resp(200, {
            "docId": doc_id,
            "uploadUrl": upload_url,
            "key": file_key,
            "filename": filename
        })
        
    except Exception as e:
        print("presign error:", repr(e))
        return resp(500, {"message": "internal error"})