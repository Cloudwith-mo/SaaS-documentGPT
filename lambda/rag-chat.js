const https = require('https');
const { Client } = require('pg');

const client = new Client({
    host: process.env.DB_HOST,
    database: 'postgres',
    user: 'postgres',
    password: process.env.DB_PASSWORD,
    port: 5432,
    ssl: { rejectUnauthorized: false }
});

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

    try {
        const { question, docId } = JSON.parse(event.body);
        
        let context = '';
        
        // If docId provided, search for relevant chunks
        if (docId) {
            await client.connect();
            
            // Get question embedding
            const questionEmbedding = await getEmbedding(question);
            
            // Search for similar chunks
            const result = await client.query(`
                SELECT content, 1 - (embedding <=> $1) as similarity
                FROM document_chunks 
                WHERE doc_id = $2
                ORDER BY embedding <=> $1
                LIMIT 3
            `, [JSON.stringify(questionEmbedding), docId]);
            
            context = result.rows.map(row => row.content).join('\n\n');
            await client.end();
        }
        
        // Generate response with context
        const systemPrompt = context 
            ? `You are a helpful assistant. Use this context to answer questions: ${context}`
            : 'You are a helpful assistant.';
            
        const response = await callOpenAI({
            model: "gpt-4o",
            messages: [
                { role: "system", content: systemPrompt },
                { role: "user", content: question }
            ],
            max_tokens: 500,
            temperature: 0.7
        });
        
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                answer: response.choices[0].message.content,
                hasContext: !!context
            })
        };
    } catch (error) {
        console.error('Error:', error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: 'Failed to process request' })
        };
    }
};

async function getEmbedding(text) {
    const data = JSON.stringify({
        model: "text-embedding-ada-002",
        input: text
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
                const parsed = JSON.parse(body);
                resolve(parsed.data[0].embedding);
            });
        });

        req.on('error', reject);
        req.write(data);
        req.end();
    });
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