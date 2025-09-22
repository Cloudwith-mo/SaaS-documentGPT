const crypto = require('crypto');

// Simple API key validation
const VALID_API_KEYS = new Set([
    'dk-test-key-123',
    'dk-demo-key-456',
    'dk-prod-key-789'
]);

function validateApiKey(apiKey) {
    return VALID_API_KEYS.has(apiKey);
}

function extractApiKey(event) {
    const headers = event.headers || {};
    
    // Check Authorization header (Bearer token)
    const authHeader = headers.authorization || headers.Authorization;
    if (authHeader && authHeader.startsWith('Bearer ')) {
        return authHeader.substring(7);
    }
    
    // Check x-api-key header
    return headers['x-api-key'] || headers['X-API-Key'];
}

function requireAuth(event) {
    const apiKey = extractApiKey(event);
    
    if (!apiKey) {
        return {
            statusCode: 401,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ error: 'API key required' })
        };
    }
    
    if (!validateApiKey(apiKey)) {
        return {
            statusCode: 403,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ error: 'Invalid API key' })
        };
    }
    
    return null; // Auth passed
}

module.exports = {
    validateApiKey,
    extractApiKey,
    requireAuth
};