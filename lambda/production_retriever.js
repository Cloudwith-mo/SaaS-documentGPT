import OpenAI from "openai";
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const s3 = new S3Client({ region: process.env.AWS_REGION || 'us-east-1' });
const MODEL = process.env.EMBED_MODEL || "text-embedding-3-small";
const INDEX_BUCKET = process.env.INDEX_BUCKET || "documentgpt-uploads";

async function getIndex(docId) {
  const key = `derived/${docId}.index.json`;
  const out = await s3.send(new GetObjectCommand({ Bucket: INDEX_BUCKET, Key: key }));
  const json = await out.Body.transformToString();
  return JSON.parse(json);
}

function cosine(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) + 1e-8);
}

function cors(origin) {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Headers": "content-type,authorization",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Content-Type": "application/json"
  };
}

export const handler = async (event) => {
  const origin = event.headers?.origin || "https://documentgpt.io";
  
  if (event.requestContext?.http?.method === "OPTIONS") {
    return { statusCode: 204, headers: cors(origin) };
  }
  
  try {
    const q = event.queryStringParameters || {};
    const docId = q.docId;
    const query = q.q || "";
    const k = Math.min(parseInt(q.k || "5", 10), 10);

    if (!docId) {
      return { statusCode: 400, headers: cors(origin), body: JSON.stringify({ error: "missing docId" }) };
    }

    const index = await getIndex(docId);
    
    if (!query || !query.trim()) {
      return { 
        statusCode: 200, 
        headers: cors(origin), 
        body: JSON.stringify({ 
          status: "ok", 
          chunks: index.chunks.slice(0, k).map(c => ({ 
            text: c.text, 
            source: c.source, 
            page: c.page, 
            score: 0 
          })) 
        }) 
      };
    }

    console.log(`Retrieving with ${MODEL} for query: ${query.substring(0, 50)}...`);
    
    const qe = await openai.embeddings.create({ model: MODEL, input: [query] });
    const qvec = qe.data[0].embedding;

    const scored = index.chunks.map(c => ({ ...c, score: cosine(qvec, c.embedding) }));
    scored.sort((a, b) => b.score - a.score);

    const top = scored.slice(0, k).map(c => ({
      text: c.text,
      source: c.source,
      page: c.page,
      score: Number(c.score.toFixed(4))
    }));

    return { 
      statusCode: 200, 
      headers: cors(origin), 
      body: JSON.stringify({ 
        status: "ok", 
        chunks: top,
        model: MODEL,
        queryTokens: Math.ceil(query.length / 4)
      }) 
    };
  } catch (e) {
    console.error("retriever error", e);
    return { 
      statusCode: 500, 
      headers: cors(origin), 
      body: JSON.stringify({ error: "internal_error" }) 
    };
  }
};