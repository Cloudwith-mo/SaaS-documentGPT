# lambdas/indexer.py
import os, json, hashlib, math, re, boto3
from datetime import datetime
from botocore.exceptions import ClientError

# OpenAI new-style SDK
from openai import OpenAI

OPENAI_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
OUTPUT_BUCKET = os.getenv("OUTPUT_BUCKET", "documentgpt-uploads")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

CHUNK_TOKENS = int(os.getenv("CHUNK_TOKENS", "800"))
OVERLAP_TOKENS = int(os.getenv("CHUNK_OVERLAP", "100"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "64"))

s3 = boto3.client("s3", region_name=AWS_REGION)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _est_tokens(s: str) -> int:
    return math.ceil(len(s) / 4) if s else 0

def _normalize(t: str) -> str:
    if not t:
        return ""
    t = t.replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[\u200B-\u200D\uFEFF]", "", t)
    return t.strip()

def _strip_boilerplate(t: str) -> str:
    if not t:
        return ""
    t = re.sub(r"\n?Page\s+\d+(\s+of\s+\d+)?\s*\n", "\n", t, flags=re.I)
    t = re.sub(r"[-_*]{3,}", "", t)
    return t.strip()

def _chunk_by_tokens(text: str, max_tokens: int, overlap_tokens: int):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start
        tokens = 0
        while end < len(words) and (tokens + _est_tokens(words[end] + " ")) <= max_tokens:
            tokens += _est_tokens(words[end] + " ")
            end += 1
        if end == start:
            end += 1
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        overlap_words = 0
        span = end - start
        if span > 0 and overlap_tokens > 0:
            overlap_words = max(0, min(span - 1, round((overlap_tokens / max_tokens) * span)))
        start = max(end - overlap_words, end)
    return chunks

def _content_key(doc_id: str, page: int, text: str) -> str:
    n = _normalize(text)
    h = hashlib.sha256(n.encode("utf-8")).hexdigest()
    return f"{doc_id}:{page}:{h}"

def _get_s3_text(bucket: str, key: str) -> str:
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8", errors="ignore")

def lambda_handler(event, context):
    print(f"Python indexer using {OPENAI_MODEL}")
    
    if isinstance(event, str):
        payload = json.loads(event)
    elif isinstance(event, dict) and "body" in event:
        payload = json.loads(event["body"] or "{}")
    else:
        payload = event or {}

    doc_id = payload.get("docId")
    ocr_bucket = payload.get("ocrBucket", OUTPUT_BUCKET)
    ocr_key = payload.get("ocrKey") or payload.get("derivedKey") or f"derived/{doc_id}.txt"
    meta = payload.get("meta", {})

    if not doc_id:
        return _resp(400, {"error": "Missing docId"})

    try:
        raw = _get_s3_text(ocr_bucket, ocr_key)
        
        pages = []
        try:
            j = json.loads(raw)
            if isinstance(j, dict) and isinstance(j.get("pages"), list):
                for p in j["pages"]:
                    pages.append({"page": p.get("page") or p.get("pageNumber") or 0, "text": p.get("text") or ""})
            else:
                pages = [{"page": 1, "text": raw}]
        except Exception:
            pages = [{"page": 1, "text": raw}]

        seen = set()
        chunk_records = []
        for p in pages:
            cleaned = _strip_boilerplate(_normalize(p["text"]))
            if not cleaned:
                continue
            pieces = _chunk_by_tokens(cleaned, CHUNK_TOKENS, OVERLAP_TOKENS)
            for piece in pieces:
                cid = _content_key(doc_id, int(p.get("page") or 0), piece)
                if cid in seen:
                    continue
                seen.add(cid)
                chunk_records.append({
                    "id": cid,
                    "docId": doc_id,
                    "page": p.get("page"),
                    "text": piece
                })

        if not chunk_records:
            _put_index(doc_id, {"docId": doc_id, "model": OPENAI_MODEL, "createdAt": datetime.utcnow().isoformat(), "meta": meta, "chunks": []})
            return _resp(200, {"ok": True, "docId": doc_id, "chunks": 0, "model": OPENAI_MODEL})

        # Embed in batches
        for i in range(0, len(chunk_records), BATCH_SIZE):
            batch = chunk_records[i:i+BATCH_SIZE]
            inputs = [c["text"] for c in batch]
            emb = client.embeddings.create(model=OPENAI_MODEL, input=inputs)
            for idx, d in enumerate(emb.data):
                batch[idx]["embedding"] = d.embedding

        out = {
            "docId": doc_id,
            "model": OPENAI_MODEL,
            "createdAt": datetime.utcnow().isoformat(),
            "meta": meta,
            "chunks": [{
                "id": c["id"], "source": c["docId"],
                "page": c.get("page"),
                "text": c["text"],
                "embedding": c["embedding"]
            } for c in chunk_records]
        }
        _put_index(doc_id, out)
        
        cost = len(out["chunks"]) * 0.00002
        print(f"Indexed {len(out['chunks'])} chunks with {OPENAI_MODEL}, cost: ${cost:.4f}")
        
        return _resp(200, {
            "ok": True, 
            "docId": doc_id, 
            "chunks": len(out["chunks"]), 
            "model": OPENAI_MODEL,
            "estimatedCost": f"${cost:.4f}"
        })
        
    except Exception as e:
        print(f"Indexer error: {e}")
        return _resp(500, {"error": str(e)})

def _put_index(doc_id: str, obj: dict):
    key = f"derived/{doc_id}.index.json"
    s3.put_object(Bucket=OUTPUT_BUCKET, Key=key, Body=json.dumps(obj).encode("utf-8"), ContentType="application/json")

def _resp(code, body):
    return {"statusCode": code, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}