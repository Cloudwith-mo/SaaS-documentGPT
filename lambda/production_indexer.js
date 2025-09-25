import OpenAI from "openai";
import crypto from "crypto";
import { S3Client, GetObjectCommand, PutObjectCommand } from "@aws-sdk/client-s3";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const s3 = new S3Client({ region: process.env.AWS_REGION || 'us-east-1' });

const MODEL = process.env.EMBED_MODEL || "text-embedding-3-small";
const OUT_BUCKET = process.env.OUTPUT_BUCKET || "documentgpt-uploads";

const CHUNK_TOKENS = parseInt(process.env.CHUNK_TOKENS || "800", 10);
const OVERLAP_TOKENS = parseInt(process.env.CHUNK_OVERLAP || "100", 10);

const estTokens = (s) => Math.ceil((s || "").length / 4);

const normalize = (t) =>
  (t || "")
    .replace(/\r/g, "\n")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/[\u200B-\u200D\uFEFF]/g, "")
    .trim();

function stripBoilerplate(t) {
  return t
    .replace(/\n?Page\s+\d+(\s+of\s+\d+)?\s*\n/gi, "\n")
    .replace(/-{3,}|_{3,}|\*{3,}/g, "")
    .trim();
}

function contentKey(docId, page, text) {
  const n = normalize(text);
  const h = crypto.createHash("sha256").update(n).digest("hex");
  return `${docId}:${page}:${h}`;
}

function chunkByTokens(text, maxTokens = CHUNK_TOKENS, overlap = OVERLAP_TOKENS) {
  const words = text.split(/\s+/);
  const chunks = [];
  let start = 0;
  while (start < words.length) {
    let end = start;
    let tokens = 0;
    while (end < words.length && tokens + estTokens(words[end] + " ") <= maxTokens) {
      tokens += estTokens(words[end] + " ");
      end++;
    }
    const chunk = words.slice(start, end).join(" ").trim();
    if (chunk) chunks.push(chunk);
    const overlapWords = Math.max(0, Math.round((overlap / maxTokens) * (end - start)));
    start = Math.max(end - overlapWords, end);
  }
  return chunks;
}

async function getS3Text(bucket, key) {
  const out = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
  return await out.Body.transformToString();
}

export const handler = async (event) => {
  console.log(`Production indexer using ${MODEL}`);
  
  const record = typeof event === "string" ? JSON.parse(event) : (event.body ? JSON.parse(event.body) : event);
  const { docId, derivedKey } = record || {};
  
  if (!docId) {
    return { statusCode: 400, body: "Missing docId" };
  }

  const ocrBucket = OUT_BUCKET;
  const ocrKey = derivedKey || `derived/${docId}.txt`;

  try {
    const raw = await getS3Text(ocrBucket, ocrKey);
    
    let pages = [];
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed.pages)) pages = parsed.pages.map(p => ({ page: p.page ?? p.pageNumber ?? null, text: p.text ?? "" }));
      else pages = [{ page: 1, text: raw }];
    } catch {
      pages = [{ page: 1, text: raw }];
    }

    const seen = new Set();
    const chunkRecords = [];

    for (const p of pages) {
      const cleaned = stripBoilerplate(normalize(p.text || ""));
      if (!cleaned) continue;
      const pieces = chunkByTokens(cleaned);
      for (const piece of pieces) {
        const key = contentKey(docId, p.page ?? 0, piece);
        if (seen.has(key)) continue;
        seen.add(key);
        chunkRecords.push({
          id: key,
          docId,
          page: p.page ?? null,
          text: piece
        });
      }
    }

    if (chunkRecords.length === 0) {
      const emptyObj = { docId, model: MODEL, createdAt: new Date().toISOString(), chunks: [] };
      await s3.send(new PutObjectCommand({
        Bucket: OUT_BUCKET,
        Key: `derived/${docId}.index.json`,
        Body: JSON.stringify(emptyObj),
        ContentType: "application/json"
      }));
      return { statusCode: 200, body: JSON.stringify({ ok: true, chunks: 0 }) };
    }

    const batchSize = 64;
    for (let i = 0; i < chunkRecords.length; i += batchSize) {
      const batch = chunkRecords.slice(i, i + batchSize);
      const inputs = batch.map(c => c.text);
      const embed = await openai.embeddings.create({ model: MODEL, input: inputs });
      embed.data.forEach((d, idx) => {
        batch[idx].embedding = d.embedding;
        batch[idx].score = null;
      });
    }

    const outObj = {
      docId,
      model: MODEL,
      createdAt: new Date().toISOString(),
      chunks: chunkRecords.map(({ id, docId: _d, text, page, embedding }) => ({
        id,
        source: docId,
        page,
        text,
        embedding
      }))
    };

    await s3.send(new PutObjectCommand({
      Bucket: OUT_BUCKET,
      Key: `derived/${docId}.index.json`,
      Body: JSON.stringify(outObj),
      ContentType: "application/json"
    }));

    console.log(`Indexed ${outObj.chunks.length} chunks with ${MODEL}`);
    return {
      statusCode: 200,
      body: JSON.stringify({ 
        ok: true, 
        docId, 
        chunks: outObj.chunks.length, 
        model: MODEL,
        estimatedCost: `$${(outObj.chunks.length * 0.00002).toFixed(4)}`
      })
    };
  } catch (error) {
    console.error('Indexer error:', error);
    return { statusCode: 500, body: JSON.stringify({ error: error.message }) };
  }
};