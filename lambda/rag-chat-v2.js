const { S3Client, GetObjectCommand } = require('@aws-sdk/client-s3');
const { DynamoDBClient, GetItemCommand } = require('@aws-sdk/client-dynamodb');
const https = require('https');
const { emitMetric } = require('./metrics-helper');
const { getFromCache, setCache } = require('./cache-helper');
const { getUserIdFromEvent, addUserPrefix } = require('./multi-tenant-helper');
const { requireAuth } = require('./auth-helper');
const { rateLimitResponse } = require('./rate-limit-helper');

const s3Client = new S3Client({ region: 'us-east-1' });
const dynamoClient = new DynamoDBClient({ region: 'us-east-1' });

exports.handler = async (event) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Content-Type': 'application/json'
    };

    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers, body: '' };
    }

    // Remove auth for now
    const userId = 'system';
    
    // Check rate limit
    const rateLimitResult = rateLimitResponse(userId, 'chat');
    if (!rateLimitResult.allowed) {
        return rateLimitResult;
    }

    try {
        const startTime = Date.now();
        const { question, docId } = JSON.parse(event.body);
        
        // Check cache first (user-scoped)
        const cached = getFromCache(question, `${userId}_${docId}`);
        if (cached) {
            await emitMetric('CacheHits', 1, 'Count');
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({ ...cached, cached: true })
            };
        }
        
        let context = '';
        let hasContext = false;
        let retrievalTime = 0;
        
        if (docId) {
            // Check document status in DynamoDB
            const docStatus = await getDocumentStatus(docId);
            
            if (docStatus === 's1.ckpt-08.chat') {
                // Get relevant chunks using new index format
                const retrievalStart = Date.now();
                context = await getRelevantContext(docId, question, userId);
                retrievalTime = Date.now() - retrievalStart;
                hasContext = context.length > 0;
            }
        }
        
        // Generate response with OpenAI
        const answer = await generateAnswer(question, context);
        
        // Cache the response (user-scoped)
        const responseData = { answer, hasContext };
        setCache(question, `${userId}_${docId}`, responseData);
        await emitMetric('CacheMisses', 1, 'Count');
        
        // Emit metrics
        const totalDuration = Date.now() - startTime;
        await emitMetric('ChatLatencyMs', totalDuration, 'Milliseconds', [
            { Name: 'HasContext', Value: hasContext.toString() },
            { Name: 'Function', Value: process.env.AWS_LAMBDA_FUNCTION_NAME }
        ]);
        
        if (retrievalTime > 0) {
            await emitMetric('RetrievalLatencyMs', retrievalTime, 'Milliseconds');
        }
        
        return {
            statusCode: 200,
            headers: {
                ...headers,
                ...rateLimitResult.headers
            },
            body: JSON.stringify(responseData)
        };
    } catch (error) {
        console.error('RAG Chat error:', error);
        // Emit error metric
        await emitMetric('ChatErrors', 1, 'Count', [
            { Name: 'Function', Value: process.env.AWS_LAMBDA_FUNCTION_NAME }
        ]);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: 'Failed to process chat request' })
        };
    }
};

async function getDocumentStatus(docId) {
    try {
        const response = await dynamoClient.send(new GetItemCommand({
            TableName: 'documentgpt-documents',
            Key: { docId: { S: docId } }
        }));
        
        return response.Item?.status?.S || null;
    } catch (error) {
        console.error('Error getting document status:', error);
        return null;
    }
}

async function getRelevantContext(docId, question, userId) {
    try {
        // Get question embedding
        const questionEmbedding = await getEmbedding(question);
        
        // Use single-tenant path for now
        const indexKey = `derived/${docId}.index.json`;
        const indexResponse = await s3Client.send(new GetObjectCommand({
            Bucket: 'documentgpt-uploads',
            Key: indexKey
        }));
        
        const indexData = JSON.parse(await indexResponse.Body.transformToString());
        
        // Calculate cosine similarity for each chunk
        const similarities = indexData.chunks.map(chunk => ({
            content: chunk.content,
            similarity: cosineSimilarity(questionEmbedding, chunk.embedding)
        }));
        
        // Get top 3 most relevant chunks
        const topChunks = similarities
            .sort((a, b) => b.similarity - a.similarity)
            .slice(0, 3)
            .filter(chunk => chunk.similarity > 0.3); // Lower threshold for testing
        
        return topChunks.map(chunk => chunk.content).join('\n\n');
        
    } catch (error) {
        console.error('Error getting context:', error);
        return '';
    }
}

function cosineSimilarity(a, b) {
    const dotProduct = a.reduce((sum, val, i) => sum + val * b[i], 0);
    const magnitudeA = Math.sqrt(a.reduce((sum, val) => sum + val * val, 0));
    const magnitudeB = Math.sqrt(b.reduce((sum, val) => sum + val * val, 0));
    return dotProduct / (magnitudeA * magnitudeB);
}

async function getEmbedding(text) {
    const data = JSON.stringify({
        model: "text-embedding-ada-002",
        input: text.substring(0, 8000)
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
                    resolve(parsed.data[0].embedding);
                } catch (e) {
                    reject(e);
                }
            });
        });

        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

async function generateAnswer(question, context) {
    const systemPrompt = context 
        ? `Answer the question based on the provided context. If the context doesn't contain relevant information, say so.

Context:
${context}`
        : 'Answer the question helpfully and concisely.';

    const data = JSON.stringify({
        model: "gpt-4o-mini",
        messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: question }
        ],
        max_tokens: 500,
        temperature: 0.7
    });
    
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'api.openai.com',
            port: 443,
            path: '/v1/chat/completions',
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
                    resolve(parsed.choices[0].message.content);
                } catch (e) {
                    reject(e);
                }
            });
        });

        req.on('error', reject);
        req.write(data);
        req.end();
    });
}