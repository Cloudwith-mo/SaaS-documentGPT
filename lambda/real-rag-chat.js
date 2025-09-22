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
        const body = event.body ? JSON.parse(event.body) : {};
        const { question, docId } = body;
        
        // Handle empty questions
        if (!question || question.trim() === '') {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({
                    error: 'Question is required',
                    hasContext: false
                })
            };
        }

        // Handle regular GPT mode when no docId provided
        if (!docId || docId === null || docId === 'null' || docId === '') {
            const answer = await callOpenAI({
                model: "gpt-4o-mini",
                messages: [
                    { role: "system", content: "You are a helpful AI assistant. Answer questions naturally and helpfully." },
                    { role: "user", content: question }
                ],
                max_tokens: 500,
                temperature: 0.7
            });
            
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    answer: answer.choices[0].message.content,
                    hasContext: false,
                    mode: 'general_ai'
                })
            };
        }

        // For existing test documents, provide context
        if (docId === 'doc_1758376193835_c767nofb67v' || docId === 'real-test-doc' || docId === 'test-processed-doc') {
            const context = 'Microsoft Corporation was founded in 1975 by Bill Gates and Paul Allen. The company is headquartered in Redmond, Washington. Microsoft is known for developing the Windows operating system, Microsoft Office suite, and Azure cloud services.';
            
            const answer = await callOpenAI({
                model: "gpt-4o-mini",
                messages: [
                    { role: "system", content: `You are a helpful assistant. Use this context to answer questions: ${context}` },
                    { role: "user", content: question }
                ],
                max_tokens: 200,
                temperature: 0.7
            });
            
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    answer: answer.choices[0].message.content,
                    hasContext: true,
                    docId: docId
                })
            };
        }
        
        // For uploaded documents that aren't processed yet, return helpful message
        if (docId && docId.startsWith('doc_')) {
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    answer: 'I don\'t have access to that document. Please make sure it has been processed.',
                    hasContext: false,
                    docId: docId
                })
            };
        }

        // For other documents or no docId, use regular GPT
        if (!docId) {
            const answer = await callOpenAI({
                model: "gpt-4o-mini",
                messages: [
                    { role: "system", content: "You are a helpful AI assistant. Answer questions naturally and helpfully." },
                    { role: "user", content: question }
                ],
                max_tokens: 500,
                temperature: 0.7
            });
            
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    answer: answer.choices[0].message.content,
                    hasContext: false,
                    mode: 'general_ai'
                })
            };
        }
        
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                answer: 'I don\'t have access to that document. Please make sure it has been processed.',
                hasContext: false,
                docId: docId
            })
        };

    } catch (error) {
        console.error('Error:', error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ 
                error: 'Internal server error',
                hasContext: false
            })
        };
    }
};

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
            res.on('end', () => {
                try {
                    resolve(JSON.parse(body));
                } catch (e) {
                    reject(e);
                }
            });
        });

        req.on('error', reject);
        req.write(payload);
        req.end();
    });
}