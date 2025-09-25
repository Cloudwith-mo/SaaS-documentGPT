const { S3Client, GetObjectCommand, PutObjectCommand } = require('@aws-sdk/client-s3');
const { DynamoDBClient, GetItemCommand, PutItemCommand } = require('@aws-sdk/client-dynamodb');
const https = require('https');
const crypto = require('crypto');

const s3Client = new S3Client({ region: 'us-east-1' });
const ddbClient = new DynamoDBClient({ region: 'us-east-1' });

const EMBEDDING_MODEL = "text-embedding-3-small"; // 5x cheaper than ada-002
const EMBEDDINGS_CACHE_TABLE = "EmbeddingsCache";

exports.handler = async (event) => {
    console.log(`Using ${EMBEDDING_MODEL} (5x cheaper than ada-002)`);
    const { docId, derivedKey } = event;
    
    try {
        const textResponse = await s3Client.send(new GetObjectCommand({
            Bucket: 'documentgpt-uploads',
            Key: derivedKey || `derived/${docId}.txt`
        }));
        
        const rawText = await textResponse.Body.transformToString();
        const cleanText = preprocessText(rawText);
        const chunks = createOptimalChunks(cleanText);
        
        console.log(`Processing ${chunks.length} chunks (${cleanText.length} chars)`);
        
        // Get embeddings with deduplication
        const indexData = [];
        let cacheHits = 0, apiCalls = 0;
        
        for (let i = 0; i < chunks.length; i++) {
            const chunk = chunks[i];
            const contentKey = getContentKey(docId, i, chunk);
            
            // Check cache first
            let embedding = await getCachedEmbedding(contentKey);
            if (embedding) {
                cacheHits++;
            } else {
                embedding = await getEmbedding(chunk);
                await cacheEmbedding(contentKey, embedding);
                apiCalls++;
            }
            
            indexData.push({
                chunkIndex: i,
                content: chunk,
                embedding,
                contentKey,
                tokenCount: estimateTokens(chunk)
            });
        }
        
        console.log(`Cache hits: ${cacheHits}, API calls: ${apiCalls}, Saved: $${(cacheHits * 0.00002).toFixed(4)}`);
        
        await s3Client.send(new PutObjectCommand({
            Bucket: 'documentgpt-uploads',
            Key: `derived/${docId}.index.json`,
            Body: JSON.stringify({
                docId,
                model: EMBEDDING_MODEL,
                totalChunks: indexData.length,
                totalTokens: indexData.reduce((sum, chunk) => sum + chunk.tokenCount, 0),
                cacheHits,
                apiCalls,
                createdAt: new Date().toISOString(),
                chunks: indexData
            }),
            ContentType: 'application/json'
        }));
        
        return { 
            docId, 
            chunks: indexData.length, 
            model: EMBEDDING_MODEL,
            cacheHits,
            apiCalls,
            estimatedCost: `$${(apiCalls * 0.00002).toFixed(4)}`
        };
        
    } catch (error) {
        console.error('Indexer error:', error);
        throw error;
    }
};

function preprocessText(text) {
    return text
        // Remove repeated headers/footers
        .replace(/^.{0,50}Page \d+.{0,50}$/gm, '')
        .replace(/^.{0,50}\d{1,2}\/\d{1,2}\/\d{4}.{0,50}$/gm, '')
        // Normalize whitespace
        .replace(/\s+/g, ' ')
        .replace(/[\u200B-\u200D\uFEFF]/g, '')
        .trim();
}

function createOptimalChunks(text, targetTokens = 800, overlap = 100) {
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 10);
    const chunks = [];
    let currentChunk = '';
    
    for (const sentence of sentences) {
        const testChunk = currentChunk + (currentChunk ? '. ' : '') + sentence.trim();
        
        if (estimateTokens(testChunk) > targetTokens && currentChunk.length > 0) {
            chunks.push(currentChunk.trim());
            // Add overlap
            const words = currentChunk.split(' ');
            currentChunk = words.slice(-overlap/4).join(' ') + '. ' + sentence.trim();
        } else {
            currentChunk = testChunk;
        }
    }
    
    if (currentChunk.trim().length > 0) {
        chunks.push(currentChunk.trim());
    }
    
    return chunks.filter(chunk => chunk.length > 50); // Skip tiny chunks
}

function estimateTokens(text) {
    return Math.ceil(text.length / 4); // Rough estimate: 4 chars = 1 token
}

function getContentKey(docId, chunkIndex, text) {
    const normalized = text.replace(/\s+/g, ' ').trim();
    const hash = crypto.createHash('sha256').update(normalized).digest('hex').substring(0, 16);
    return `${docId}:${chunkIndex}:${hash}`;
}

async function getCachedEmbedding(contentKey) {
    try {
        const result = await ddbClient.send(new GetItemCommand({
            TableName: EMBEDDINGS_CACHE_TABLE,
            Key: { contentKey: { S: contentKey } }
        }));
        
        if (result.Item) {
            return JSON.parse(result.Item.embedding.S);
        }
    } catch (error) {
        console.log('Cache miss:', contentKey);
    }
    return null;
}

async function cacheEmbedding(contentKey, embedding) {
    try {
        await ddbClient.send(new PutItemCommand({
            TableName: EMBEDDINGS_CACHE_TABLE,
            Item: {
                contentKey: { S: contentKey },
                embedding: { S: JSON.stringify(embedding) },
                createdAt: { S: new Date().toISOString() },
                ttl: { N: String(Math.floor(Date.now() / 1000) + 86400 * 30) } // 30 day TTL
            }
        }));
    } catch (error) {
        console.log('Cache write failed:', error.message);
    }
}

async function getEmbedding(text) {
    const data = JSON.stringify({
        model: EMBEDDING_MODEL,
        input: text.substring(0, 8000) // Token limit
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
                        resolve(parsed.data[0].embedding);
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