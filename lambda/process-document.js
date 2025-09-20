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
        const { docId, filename, content } = JSON.parse(event.body);
        
        await client.connect();
        
        // Split content into chunks (simple approach)
        const chunks = splitIntoChunks(content, 1000);
        
        // Store document
        await client.query(`
            INSERT INTO documents (doc_id, filename, content, embedding)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (doc_id) DO UPDATE SET
            filename = $2, content = $3, embedding = $4
        `, [docId, filename, content, JSON.stringify(await getEmbedding(content.substring(0, 8000)))]);
        
        // Store chunks with embeddings
        for (let i = 0; i < chunks.length; i++) {
            const embedding = await getEmbedding(chunks[i]);
            await client.query(`
                INSERT INTO document_chunks (doc_id, chunk_index, content, embedding)
                VALUES ($1, $2, $3, $4)
            `, [docId, i, chunks[i], JSON.stringify(embedding)]);
        }
        
        await client.end();
        
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                docId,
                status: 'READY',
                chunks: chunks.length
            })
        };
    } catch (error) {
        console.error('Error:', error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: 'Failed to process document' })
        };
    }
};

function splitIntoChunks(text, chunkSize) {
    const chunks = [];
    for (let i = 0; i < text.length; i += chunkSize) {
        chunks.push(text.substring(i, i + chunkSize));
    }
    return chunks;
}

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