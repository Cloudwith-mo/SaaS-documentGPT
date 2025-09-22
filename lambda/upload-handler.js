const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');
const { getUserIdFromEvent, addUserPrefix } = require('./multi-tenant-helper');
const { requireAuth } = require('./auth-helper');
const { rateLimitResponse } = require('./rate-limit-helper');
const s3Client = new S3Client({ region: 'us-east-1' });

const BUCKET_NAME = 'documentgpt-uploads';

exports.handler = async (event) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, x-api-key, x-user-id',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Content-Type': 'application/json'
    };

    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers, body: '' };
    }

    // Check authentication
    const authError = requireAuth(event);
    if (authError) {
        return authError;
    }

    const userId = getUserIdFromEvent(event);
    
    // Check rate limit
    const rateLimitResult = rateLimitResponse(userId, 'upload');
    if (!rateLimitResult.allowed) {
        return rateLimitResult;
    }

    try {
        const body = JSON.parse(event.body || '{}');
        const { filename, contentType } = body;
        
        if (!filename || typeof filename !== 'string' || filename.trim() === '') {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: 'Valid filename is required' })
            };
        }
        
        const docId = 'doc_' + Date.now() + '_' + Math.random().toString(36).slice(2);
        // Use single-tenant path for now to match Step Functions
        const key = `${docId}/${filename}`;
        
        // Generate presigned URL for upload
        const putCommand = new PutObjectCommand({
            Bucket: BUCKET_NAME,
            Key: key,
            ContentType: contentType
        });
        const uploadUrl = await getSignedUrl(s3Client, putCommand, { expiresIn: 300 });
        
        // Generate presigned URL for download/preview  
        const getCommand = new (require('@aws-sdk/client-s3').GetObjectCommand)({
            Bucket: BUCKET_NAME,
            Key: key
        });
        const downloadUrl = await getSignedUrl(s3Client, getCommand, { expiresIn: 3600 });
        
        return {
            statusCode: 200,
            headers: {
                ...headers,
                ...rateLimitResult.headers
            },
            body: JSON.stringify({
                docId,
                userId,
                uploadUrl,
                downloadUrl,
                key,
                filename
            })
        };
    } catch (error) {
        console.error('Upload handler error:', error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: 'Failed to generate upload URL' })
        };
    }
};