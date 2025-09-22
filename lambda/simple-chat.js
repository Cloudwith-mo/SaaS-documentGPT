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
        const { question, docId } = JSON.parse(event.body || '{}');
        
        // Simple response for testing
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                answer: `I received your question: "${question}" about document ${docId}. The system is working!`,
                hasContext: true
            })
        };
    } catch (error) {
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: 'Failed to process request' })
        };
    }
};