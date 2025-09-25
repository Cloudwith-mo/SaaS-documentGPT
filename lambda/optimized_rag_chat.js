const { S3Client, GetObjectCommand } = require('@aws-sdk/client-s3');
const https = require('https');

const s3Client = new S3Client({ region: 'us-east-1' });
const EMBEDDING_MODEL = process.env.EMBEDDING_MODEL || "text-embedding-3-small";
const RAG_CHAT_MODEL = process.env.RAG_CHAT_MODEL || "gpt-4o-mini-2024-07-18";
const GENERAL_CHAT_MODEL = process.env.GENERAL_CHAT_MODEL || "gpt-4o-mini-2024-07-18";

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
        
        console.log(`Chat request - docId: ${docId}, embedding model: ${EMBEDDING_MODEL}`);

        if (!docId) {
            // General chat mode
            const answer = await callOpenAI({
                model: GENERAL_CHAT_MODEL,
                messages: [
                    { role: "system", content: "You are a helpful AI assistant." },
                    ...messages
                ],
                max_tokens: 1000,
                temperature: 0.7
            });
            
            return {
                statusCode: 200,
                headers: CORS,
                body: JSON.stringify({
                    mode: "general",
                    answer: answer.choices[0].message.content
                })
            };
        }

        // RAG mode - get context from index
        const context = await getDocumentContext(docId, messages[messages.length - 1].content);
        
        const systemPrompt = context 
            ? `You are a helpful assistant. Use this document context to answer questions, but also provide general knowledge when relevant.\n\nDocument Context:\n${context}`
            : 'You are a helpful assistant analyzing a document.';
            
        const answer = await callOpenAI({
            model: RAG_CHAT_MODEL,
            messages: [
                { role: "system", content: systemPrompt },
                ...messages
            ],
            max_tokens: 1000,
            temperature: 0.7
        });
        
        return {
            statusCode: 200,
            headers: CORS,
            body: JSON.stringify({
                mode: "rag",
                docId,
                answer: answer.choices[0].message.content,
                hasContext: !!context
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

async function getDocumentContext(docId, question) {
    try {
        // Get document index
        const indexResponse = await s3Client.send(new GetObjectCommand({
            Bucket: 'documentgpt-uploads',
            Key: `derived/${docId}.index.json`
        }));
        
        const index = JSON.parse(await indexResponse.Body.transformToString());
        
        // Get question embedding (single call, cached if possible)
        const questionEmbedding = await getSingleEmbedding(question);
        
        // Find most similar chunks
        const similarities = index.chunks.map(chunk => ({
            content: chunk.content,
            similarity: cosineSimilarity(questionEmbedding, chunk.embedding)
        }));
        
        similarities.sort((a, b) => b.similarity - a.similarity);
        
        // Return top 3 chunks as context
        return similarities.slice(0, 3).map(s => s.content).join('\n\n');
        
    } catch (error) {
        console.error('Context retrieval error:', error);
        return null;
    }
}

async function getSingleEmbedding(text) {
    const data = JSON.stringify({
        model: EMBEDDING_MODEL,
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