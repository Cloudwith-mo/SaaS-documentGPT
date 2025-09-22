const AWS = require('aws-sdk');
const stepfunctions = new AWS.StepFunctions();

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
        const { docId, filename, content, sessionId } = body;
        
        if (!docId || !filename) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: 'docId and filename are required' })
            };
        }

        // Start Step Functions execution
        const params = {
            stateMachineArn: 'arn:aws:states:us-east-1:995805900737:stateMachine:documentgpt-processing',
            name: `${docId}-${Date.now()}`,
            input: JSON.stringify({
                docId,
                filename,
                s3Key: `${docId}/${filename}`,
                fileType: filename.split('.').pop() || 'txt',
                sessionId,
                textLength: content ? content.length.toString() : '0'
            })
        };

        const result = await stepfunctions.startExecution(params).promise();
        
        // Calculate estimated pages
        const pages = content ? Math.ceil(content.length / 2000) : 1;
        
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                status: 'PROCESSING',
                executionArn: result.executionArn,
                pages,
                docId,
                message: 'Document processing started successfully'
            })
        };
        
    } catch (error) {
        console.error('Process document error:', error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ 
                error: 'Failed to start document processing',
                message: error.message 
            })
        };
    }
};