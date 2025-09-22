const { DynamoDBClient, PutItemCommand } = require('@aws-sdk/client-dynamodb');
const { SFNClient, StartExecutionCommand } = require('@aws-sdk/client-sfn');

const dynamoClient = new DynamoDBClient({ region: 'us-east-1' });
const sfnClient = new SFNClient({ region: 'us-east-1' });

const STEP_FUNCTION_ARN = 'arn:aws:states:us-east-1:995805900737:stateMachine:documentgpt-processing';
const TABLE_NAME = 'documentgpt-documents';

exports.handler = async (event) => {
    console.log('S3 trigger event:', JSON.stringify(event, null, 2));
    
    for (const record of event.Records) {
        if (record.eventName.startsWith('ObjectCreated')) {
            const bucket = record.s3.bucket.name;
            const key = decodeURIComponent(record.s3.object.key.replace(/\+/g, ' '));
            
            console.log(`Processing S3 object: ${bucket}/${key}`);
            
            // Parse multi-tenant path: users/{userId}/{docId}/filename
            const pathParts = key.split('/');
            if (pathParts.length >= 4 && pathParts[0] === 'users') {
                const userId = pathParts[1];
                const docId = pathParts[2];
                const filename = pathParts.slice(3).join('/');
                
                console.log(`Parsed: userId=${userId}, docId=${docId}, filename=${filename}`);
                
                // Determine file type
                const fileExtension = filename.split('.').pop().toLowerCase();
                const fileType = getFileType(fileExtension);
                
                try {
                    // Create DynamoDB record
                    await dynamoClient.send(new PutItemCommand({
                        TableName: TABLE_NAME,
                        Item: {
                            docId: { S: docId },
                            userId: { S: userId },
                            filename: { S: filename },
                            fileType: { S: fileType },
                            s3Key: { S: key },
                            status: { S: 's1.ckpt-01.uploaded' },
                            uploadedAt: { S: new Date().toISOString() }
                        }
                    }));
                    
                    console.log(`DynamoDB record created for ${docId}`);
                    
                    // Start Step Function execution
                    const executionInput = {
                        docId,
                        userId,
                        s3Key: key,
                        filename,
                        fileType,
                        bucket
                    };
                    
                    await sfnClient.send(new StartExecutionCommand({
                        stateMachineArn: STEP_FUNCTION_ARN,
                        name: `${docId}-${Date.now()}`,
                        input: JSON.stringify(executionInput)
                    }));
                    
                    console.log(`Step Function started for ${docId}`);
                    
                } catch (error) {
                    console.error('Error processing S3 event:', error);
                    throw error;
                }
            } else {
                console.log(`Ignoring non-multi-tenant path: ${key}`);
            }
        }
    }
};

function getFileType(extension) {
    const typeMap = {
        'pdf': 'pdf',
        'txt': 'txt',
        'doc': 'docx',
        'docx': 'docx',
        'xls': 'xlsx',
        'xlsx': 'xlsx',
        'jpg': 'image',
        'jpeg': 'image',
        'png': 'image',
        'gif': 'image',
        'bmp': 'image'
    };
    return typeMap[extension] || 'txt';
}