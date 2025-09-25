const { S3Client, GetObjectCommand, PutObjectCommand } = require('@aws-sdk/client-s3');
const https = require('https');

const s3Client = new S3Client({ region: 'us-east-1' });
const EMBEDDING_MODEL = process.env.EMBEDDING_MODEL || "text-embedding-3-small";
const GENERAL_CHAT_MODEL = process.env.GENERAL_CHAT_MODEL || "gpt-4o-mini-2024-07-18";

exports.handler = async (event) => {
    console.log(`Using embedding model: ${EMBEDDING_MODEL}`);
    const { docId, derivedKey } = event;
    const bucket = 'documentgpt-uploads';
    
    try {
        const textResponse = await s3Client.send(new GetObjectCommand({
            Bucket: bucket,
            Key: derivedKey || `derived/${docId}.txt`
        }));
        
        const text = await textResponse.Body.transformToString();
        const chunks = splitIntoChunks(text, 1000);
        console.log(`Processing ${chunks.length} chunks with ${EMBEDDING_MODEL}`);
        
        // Batch embeddings for efficiency
        const embeddings = await getBatchEmbeddings(chunks);
        
        const indexData = chunks.map((chunk, i) => ({
            chunkIndex: i,
            content: chunk,
            embedding: embeddings[i],
            contentHash: hashContent(chunk)
        }));
        
        await s3Client.send(new PutObjectCommand({
            Bucket: bucket,
            Key: `derived/${docId}.index.json`,
            Body: JSON.stringify({
                docId,
                model: EMBEDDING_MODEL,
                totalChunks: indexData.length,
                createdAt: new Date().toISOString(),
                chunks: indexData
            }),
            ContentType: 'application/json'
        }));
        
        return { docId, chunks: indexData.length, model: EMBEDDING_MODEL };
        
    } catch (error) {
        console.error('Indexer error:', error);
        throw error;
    }
};

function splitIntoChunks(text, chunkSize) {
    const chunks = [];
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    
    let currentChunk = '';
    for (const sentence of sentences) {
        if (currentChunk.length + sentence.length > chunkSize && currentChunk.length > 0) {
            chunks.push(currentChunk.trim());
            currentChunk = sentence.trim();
        } else {
            currentChunk += (currentChunk ? '. ' : '') + sentence.trim();
        }
    }
    
    if (currentChunk.trim().length > 0) {
        chunks.push(currentChunk.trim());
    }
    
    return chunks.length > 0 ? chunks : [text.substring(0, chunkSize)];
}

function hashContent(content) {
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(content).digest('hex').substring(0, 16);
}

async function getBatchEmbeddings(texts) {
    const data = JSON.stringify({
        model: EMBEDDING_MODEL,
        input: texts.slice(0, 100) // Batch limit
    });
    
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'api.openai.com',
            port: 443,
            path: '/v1/embeddings',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
                'Content-Length': Buffer.byteLength(data)
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(body);
                    if (parsed.error) {
                        reject(new Error(`OpenAI API error: ${parsed.error.message}`));
                    } else {
                        resolve(parsed.data.map(item => item.embedding));
                    }
                } catch (e) {
                    reject(new Error(`Failed to parse OpenAI response: ${e.message}`));
                }
            });
        });

        req.on('error', reject);
        req.write(data);
        req.end();
    });
}