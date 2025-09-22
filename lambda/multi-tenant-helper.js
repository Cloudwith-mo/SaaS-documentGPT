const crypto = require('crypto');

function generateUserId() {
    return 'user_' + Date.now() + '_' + crypto.randomBytes(4).toString('hex');
}

function getUserIdFromEvent(event) {
    // Extract userId from headers, query params, or body
    const headers = event.headers || {};
    const queryParams = event.queryStringParameters || {};
    
    // Priority: header > query > body
    let userId = headers['x-user-id'] || queryParams.userId;
    
    if (!userId && event.body) {
        try {
            const body = JSON.parse(event.body);
            userId = body.userId;
        } catch (e) {
            // Ignore parsing errors
        }
    }
    
    // Generate anonymous user if none provided
    if (!userId) {
        userId = generateUserId();
    }
    
    return userId;
}

function addUserPrefix(key, userId) {
    return `users/${userId}/${key}`;
}

function getUserDocId(docId, userId) {
    return `${userId}_${docId}`;
}

module.exports = {
    generateUserId,
    getUserIdFromEvent,
    addUserPrefix,
    getUserDocId
};