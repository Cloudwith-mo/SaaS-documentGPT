const { S3Client, GetObjectCommand, PutObjectCommand } = require('@aws-sdk/client-s3');
const https = require('https');
const { emitMetric } = require('./metrics-helper');

const s3Client = new S3Client({ region: 'us-east-1' });

exports.handler = async (event) => {
    console.log('Indexer event:', JSON.stringify(event, null, 2));
    
    const { docId, derivedKey } = event;
    const bucket = 'documentgpt-uploads';
    const startTime = Date.now();
    let embeddingCalls = 0;
    
    try {
        // Read extracted text from derived file
        const textResponse = await s3Client.send(new GetObjectCommand({
            Bucket: bucket,
            Key: derivedKey || `derived/${docId}.txt`
        }));
        
        const text = await textResponse.Body.transformToString();
        console.log(`Processing ${text.length} characters for indexing`);
        
        // Split text into chunks
        const chunks = splitIntoChunks(text, 1000);
        console.log(`Created ${chunks.length} chunks`);
        
        // Generate embeddings for each chunk
        const indexData = [];
        for (let i = 0; i < chunks.length; i++) {
            const chunk = chunks[i];
            if (chunk.trim().length > 0) {
                const embedding = await getEmbedding(chunk);
                embeddingCalls++;
                indexData.push({
                    chunkIndex: i,
                    content: chunk,
                    embedding: embedding,
                    length: chunk.length
                });
            }
        }
        
        // Save index to S3
        const indexKey = `derived/${docId}.index.json`;
        await s3Client.send(new PutObjectCommand({
            Bucket: bucket,
            Key: indexKey,
            Body: JSON.stringify({
                docId,
                totalChunks: indexData.length,
                createdAt: new Date().toISOString(),
                chunks: indexData
            }),
            ContentType: 'application/json'
        }));
        
        console.log(`Created index with ${indexData.length} chunks`);
        
        // Emit metrics
        const duration = Date.now() - startTime;
        await emitMetric('IndexerDurationMs', duration, 'Milliseconds', [
            { Name: 'Function', Value: process.env.AWS_LAMBDA_FUNCTION_NAME }
        ]);
        await emitMetric('EmbeddingAPICalls', embeddingCalls, 'Count', [
            { Name: 'Model', Value: 'text-embedding-ada-002' }
        ]);
        
        return {
            docId,
            chunks: indexData.length.toString(),
            indexKey
        };
        
    } catch (error) {
        console.error('Indexer error:', error);
        // Emit error metric
        await emitMetric('IndexerErrors', 1, 'Count', [
            { Name: 'Function', Value: process.env.AWS_LAMBDA_FUNCTION_NAME }
        ]);
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

async function getEmbedding(text) {
    const data = JSON.stringify({
        model: "text-embedding-ada-002",
        input: text.substring(0, 8000) // OpenAI limit
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