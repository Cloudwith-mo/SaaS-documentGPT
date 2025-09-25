const { S3Client, GetObjectCommand } = require('@aws-sdk/client-s3');
const https = require('https');

const s3Client = new S3Client({ region: 'us-east-1' });

// Cost-optimized model selection
const EMBEDDING_MODEL = "text-embedding-3-small"; // 5x cheaper
const DEFAULT_CHAT_MODEL = "gpt-4o-mini-2024-07-18"; // Extremely cheap
const PREMIUM_CHAT_MODEL = "gpt-4o-2024-08-06"; // Only for complex queries

const CORS = {
    'Access-Control-Allow-Origin': 'https://documentgpt.io',
    'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-user-id',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Content-Type': 'application/json'
};

exports.handler = async (event) => {
    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 204, headers: CORS };
    }

    try {
        const data = JSON.parse(event.body || '{}');
        const messages = data.messages || [{ role: 'user', content: data.question || '' }];
        const docId = data.docId;
        const lastMessage = messages[messages.length - 1].content;
        
        console.log(`Chat request - docId: ${docId}, model: ${EMBEDDING_MODEL}`);

        if (!docId) {
            // General chat mode - use cheapest model
            const answer = await callOpenAI({
                model: DEFAULT_CHAT_MODEL,
                messages: [
                    { role: "system", content: "You are a helpful AI assistant. Be concise." },
                    ...messages
                ],
                max_tokens: 300, // Cost control
                temperature: 0.7
            });
            
            return {
                statusCode: 200,
                headers: CORS,
                body: JSON.stringify({
                    mode: "general",
                    model: DEFAULT_CHAT_MODEL,
                    answer: answer.choices[0].message.content
                })
            };
        }

        // RAG mode - get minimal context
        const context = await getMinimalContext(docId, lastMessage);
        
        // Choose model based on query complexity
        const isComplex = /summarize|analyze|compare|explain|detail/i.test(lastMessage);
        const chatModel = isComplex ? PREMIUM_CHAT_MODEL : DEFAULT_CHAT_MODEL;
        
        const systemPrompt = context 
            ? `Answer concisely using this context. Cite page numbers when possible.\n\nContext:\n${context}`
            : 'Answer based on the document. Be concise.';
            
        const answer = await callOpenAI({
            model: chatModel,
            messages: [
                { role: "system", content: systemPrompt },
                { role: "user", content: lastMessage }
            ],
            max_tokens: isComplex ? 500 : 250, // Dynamic token limits
            temperature: 0.7
        });
        
        return {
            statusCode: 200,
            headers: CORS,
            body: JSON.stringify({
                mode: "rag",
                model: chatModel,
                docId,
                answer: answer.choices[0].message.content,
                hasContext: !!context,
                tokensUsed: answer.usage?.total_tokens || 0
            })
        };
        
    } catch (error) {
        console.error('Chat error:', error);
        return {
            statusCode: 500,
            headers: CORS,
            body: JSON.stringify({ error: 'Failed to process request' })
        };
    }
};

async function getMinimalContext(docId, question) {
    try {
        const indexResponse = await s3Client.send(new GetObjectCommand({
            Bucket: 'documentgpt-uploads',
            Key: `derived/${docId}.index.json`
        }));
        
        const index = JSON.parse(await indexResponse.Body.transformToString());
        
        // Get question embedding (cached if possible)
        const questionEmbedding = await getEmbedding(question);
        
        // Find top 3 chunks only (cost control)
        const similarities = index.chunks.map(chunk => ({
            content: chunk.content,
            similarity: cosineSimilarity(questionEmbedding, chunk.embedding)
        }));
        
        similarities.sort((a, b) => b.similarity - a.similarity);
        
        // Return only top 3 chunks, truncated
        return similarities
            .slice(0, 3)
            .map(s => s.content.substring(0, 500)) // Limit context size
            .join('\n\n');
        
    } catch (error) {
        console.error('Context retrieval error:', error);
        return null;
    }
}

async function getEmbedding(text) {
    const data = JSON.stringify({
        model: EMBEDDING_MODEL,
        input: text.substring(0, 2000) // Limit query embedding size
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

function cosineSimilarity(a, b) {
    const dotProduct = a.reduce((sum, val, i) => sum + val * b[i], 0);
    const magnitudeA = Math.sqrt(a.reduce((sum, val) => sum + val * val, 0));
    const magnitudeB = Math.sqrt(b.reduce((sum, val) => sum + val * val, 0));
    return dotProduct / (magnitudeA * magnitudeB);
}

async function callOpenAI(data) {
    const payload = JSON.stringify(data);
    
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'api.openai.com',
            port: 443,
            path: '/v1/chat/completions',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
                'Content-Length': Buffer.byteLength(payload)
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => resolve(JSON.parse(body)));
        });

        req.on('error', reject);
        req.write(payload);
        req.end();
    });
}