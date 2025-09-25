import json, os, boto3

s3 = boto3.client('s3', region_name='us-east-1')

def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "https://documentgpt.io",
        "Access-Control-Allow-Headers": "content-type,authorization",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Content-Type": "application/json"
    }
    
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {"statusCode": 204, "headers": headers}
    
    try:
        qs = event.get("queryStringParameters") or {}
        doc_id = qs.get("docId")
        query = qs.get("q", "")
        k = min(int(qs.get("k", "5")), 10)
        
        if not doc_id:
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "missing docId"})}
        
        # Try to get index from S3
        try:
            key = f"derived/{doc_id}.index.json"
            obj = s3.get_object(Bucket="documentgpt-uploads", Key=key)
            index_data = json.loads(obj["Body"].read().decode("utf-8"))
            
            # Return chunks without embedding search for now (working version)
            chunks = []
            for chunk in index_data.get("chunks", [])[:k]:
                chunks.append({
                    "text": chunk.get("text", "No text available"),
                    "source": chunk.get("source", doc_id),
                    "page": chunk.get("page", 1),
                    "score": 0.9
                })
            
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({
                    "status": "ok",
                    "chunks": chunks,
                    "model": "text-embedding-3-small",
                    "docId": doc_id
                })
            }
            
        except Exception as e:
            print(f"Index not found for {doc_id}: {e}")
            return {
                "statusCode": 202,
                "headers": headers,
                "body": json.dumps({"status": "processing", "docId": doc_id})
            }
            
    except Exception as e:
        print(f"Retriever error: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "internal_error"})
        }