const https = require('https');

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
        const { question } = JSON.parse(event.body);
        
        const openaiData = JSON.stringify({
            model: "gpt-4o",
            messages: [
                {
                    role: "system",
                    content: "You are a helpful document assistant. Answer questions clearly and concisely."
                },
                {
                    role: "user",
                    content: question
                }
            ],
            max_tokens: 500,
            temperature: 0.7
        });

        const response = await callOpenAI(openaiData);
        
        if (!response || !response.choices || !response.choices[0]) {
            throw new Error('Invalid OpenAI response');
        }
        
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                answer: response.choices[0].message.content
            })
        };
    } catch (error) {
        console.error('Error:', error);
        
        // Mock response for testing when API key is invalid
        if (error.message && error.message.includes('API key')) {
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    answer: `Hello! I'm GPT-4o-mini (mock response). Your question was: "${question}". Please add a valid OpenAI API key to get real responses.`
                })
            };
        }
        
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: 'Failed to process request' })
        };
    }
};

function callOpenAI(data) {
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
                    if (parsed.error) {
                        reject(new Error(parsed.error.message || 'OpenAI API error'));
                    } else {
                        resolve(parsed);
                    }
                } catch (e) {
                    reject(new Error('Failed to parse OpenAI response: ' + body));
                }
            });
        });

        req.on('error', reject);
        req.write(data);
        req.end();
    });
}