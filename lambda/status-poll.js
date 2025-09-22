const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand } = require('@aws-sdk/lib-dynamodb');
const { requireAuth } = require('./auth-helper');

const client = new DynamoDBClient({});
const dynamodb = DynamoDBDocumentClient.from(client);

exports.handler = async (event) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, OPTIONS'
    };

    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers };
    }

    // Check authentication
    const authError = requireAuth(event);
    if (authError) {
        return authError;
    }

    try {
        const { docId } = event.queryStringParameters || {};
        
        if (!docId) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: 'docId required' })
            };
        }

        const result = await dynamodb.send(new GetCommand({
            TableName: 'documentgpt-documents',
            Key: { docId }
        }));

        if (!result.Item) {
            return {
                statusCode: 404,
                headers,
                body: JSON.stringify({ error: 'Document not found' })
            };
        }

        const doc = result.Item;
        let phase = 'upload';
        let progress = 0;
        let message = 'Document uploaded';

        // Determine phase and progress from status
        if (doc.status === 's1.ckpt-06.upload') {
            phase = 'upload';
            progress = 33;
            message = 'Document uploaded successfully';
        } else if (doc.status === 's1.ckpt-07.parsing') {
            phase = 'parsing';
            progress = 66;
            message = 'Processing document content...';
        } else if (doc.status === 's1.ckpt-08.chat') {
            phase = 'ready';
            progress = 100;
            message = 'Document ready for chat';
        } else {
            phase = 'processing';
            progress = 10;
            message = 'Processing...';
        }

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                docId,
                phase,
                progress,
                message,
                status: doc.status,
                filename: doc.filename,
                uploadedAt: doc.uploadedAt
            })
        };
    } catch (error) {
        console.error('Status poll error:', error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: 'Internal server error' })
        };
    }
};