const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');
const s3Client = new S3Client({ region: 'us-east-1' });

const BUCKET_NAME = 'documentgpt-uploads';

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
        const { filename, contentType } = JSON.parse(event.body);
        const docId = 'doc_' + Date.now() + '_' + Math.random().toString(36).slice(2);
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
            headers,
            body: JSON.stringify({
                docId,
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