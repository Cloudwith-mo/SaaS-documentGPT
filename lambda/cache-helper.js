const crypto = require('crypto');

// Simple in-memory cache for Lambda (resets on cold start)
const cache = new Map();
const CACHE_TTL = 300000; // 5 minutes

function getCacheKey(question, docId) {
    return crypto.createHash('md5').update(`${question}:${docId}`).digest('hex');
}

function getFromCache(question, docId) {
    const key = getCacheKey(question, docId);
    const cached = cache.get(key);
    
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        return cached.data;
    }
    
    // Clean expired entries
    if (cached) {
        cache.delete(key);
    }
    
    return null;
}

function setCache(question, docId, data) {
    const key = getCacheKey(question, docId);
    cache.set(key, {
        data,
        timestamp: Date.now()
    });
    
    // Limit cache size to prevent memory issues
    if (cache.size > 100) {
        const firstKey = cache.keys().next().value;
        cache.delete(firstKey);
    }
}

module.exports = { getFromCache, setCache };