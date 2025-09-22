// Simple in-memory rate limiting (resets on Lambda cold start)
const rateLimits = new Map();

const LIMITS = {
    upload: { requests: 500, window: 60000 }, // 500 uploads per minute (batch friendly)
    chat: { requests: 200, window: 60000 }    // 200 chats per minute
};

function getRateLimitKey(userId, action) {
    return `${userId}:${action}`;
}

function checkRateLimit(userId, action) {
    const limit = LIMITS[action];
    if (!limit) return { allowed: true };
    
    const key = getRateLimitKey(userId, action);
    const now = Date.now();
    
    let userLimits = rateLimits.get(key);
    if (!userLimits) {
        userLimits = { requests: [], windowStart: now };
        rateLimits.set(key, userLimits);
    }
    
    // Clean old requests outside window
    userLimits.requests = userLimits.requests.filter(
        timestamp => now - timestamp < limit.window
    );
    
    // Check if limit exceeded
    if (userLimits.requests.length >= limit.requests) {
        const oldestRequest = Math.min(...userLimits.requests);
        const resetTime = oldestRequest + limit.window;
        
        return {
            allowed: false,
            resetTime,
            remaining: 0,
            limit: limit.requests
        };
    }
    
    // Add current request
    userLimits.requests.push(now);
    
    return {
        allowed: true,
        remaining: limit.requests - userLimits.requests.length,
        limit: limit.requests,
        resetTime: now + limit.window
    };
}

function rateLimitResponse(userId, action) {
    const result = checkRateLimit(userId, action);
    
    if (!result.allowed) {
        return {
            statusCode: 429,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json',
                'X-RateLimit-Limit': result.limit.toString(),
                'X-RateLimit-Remaining': '0',
                'X-RateLimit-Reset': Math.ceil(result.resetTime / 1000).toString()
            },
            body: JSON.stringify({ 
                error: 'Rate limit exceeded',
                resetTime: result.resetTime
            })
        };
    }
    
    return {
        allowed: true,
        headers: {
            'X-RateLimit-Limit': result.limit.toString(),
            'X-RateLimit-Remaining': result.remaining.toString(),
            'X-RateLimit-Reset': Math.ceil(result.resetTime / 1000).toString()
        }
    };
}

module.exports = {
    checkRateLimit,
    rateLimitResponse
};