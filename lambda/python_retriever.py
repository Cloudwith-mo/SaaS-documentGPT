# lambdas/retriever.py
import os, json, math, boto3
from openai import OpenAI

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
INDEX_BUCKET = os.getenv("INDEX_BUCKET") or os.getenv("OUTPUT_BUCKET", "documentgpt-uploads")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "https://documentgpt.io")

s3 = boto3.client("s3", region_name=AWS_REGION)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _cors():
    return {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Headers": "content-type,authorization",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Content-Type": "application/json"
    }

def _cosine(a, b):
    dot = 0.0
    na = 0.0
    nb = 0.0
    for i in range(len(a)):
        ai = a[i]; bi = b[i]
        dot += ai * bi
        na += ai * ai
        nb += bi * bi
    denom = (math.sqrt(na) * math.sqrt(nb)) or 1e-8
    return dot / denom

def lambda_handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {"statusCode": 204, "headers": _cors(), "body": ""}

    qs = event.get("queryStringParameters") or {}
    doc_id = qs.get("docId")
    q = (qs.get("q") or "").strip()
    k = min(int(qs.get("k") or "5"), 10)

    if not doc_id:
        return {"statusCode": 400, "headers": _cors(), "body": json.dumps({"error": "missing docId"})}

    key = f"derived/{doc_id}.index.json"
    try:
        obj = s3.get_object(Bucket=INDEX_BUCKET, Key=key)
        index = json.loads(obj["Body"].read().decode("utf-8"))
    except Exception as e:
        print(f"Index not ready for {doc_id}: {e}")
        # Return 202 to match frontend polling expectations
        return {"statusCode": 202, "headers": _cors(), "body": json.dumps({"status": "processing", "docId": doc_id})}

    # If no query, return preview (first K chunks without scores)
    if not q:
        preview = [{"text": c["text"], "source": c["source"], "page": c.get("page"), "score": 0} for c in index.get("chunks", [])[:k]]
        return {"statusCode": 200, "headers": _cors(), "body": json.dumps({"status": "ok", "chunks": preview})}

    print(f"Retrieving with {EMBED_MODEL} for query: {q[:50]}...")
    
    # Embed query and rank
    qe = client.embeddings.create(model=EMBED_MODEL, input=[q])
    qvec = qe.data[0].embedding

    scored = []
    for c in index.get("chunks", []):
        score = _cosine(qvec, c["embedding"])
        scored.append({"text": c["text"], "source": c["source"], "page": c.get("page"), "score": round(float(score), 4)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:k]
    
    return {"statusCode": 200, "headers": _cors(), "body": json.dumps({
        "status": "ok", 
        "chunks": top,
        "model": EMBED_MODEL,
        "docId": doc_id
    })}