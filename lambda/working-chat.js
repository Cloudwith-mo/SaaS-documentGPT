exports.handler = async (event) => {
    console.log('Event received:', JSON.stringify(event));
    
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
        const { question = 'No question', docId = 'No docId' } = body;
        
        console.log('Processing question:', question, 'for docId:', docId);
        
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                answer: `Working! Question: "${question}" for document: ${docId}`,
                hasContext: true,
                timestamp: new Date().toISOString()
            })
        };
    } catch (error) {
        console.error('Error:', error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ 
                error: 'Internal server error',
                message: error.message 
            })
        };
    }
};