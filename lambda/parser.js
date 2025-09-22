const { S3Client, GetObjectCommand, PutObjectCommand } = require('@aws-sdk/client-s3');
const { TextractClient, DetectDocumentTextCommand } = require('@aws-sdk/client-textract');
const { emitMetric } = require('./metrics-helper');

const s3Client = new S3Client({ region: 'us-east-1' });
const textractClient = new TextractClient({ region: 'us-east-1' });

exports.handler = async (event) => {
    console.log('Parser event:', JSON.stringify(event, null, 2));
    
    const { docId, s3Key, filename, fileType } = event;
    const bucket = 'documentgpt-uploads';
    const startTime = Date.now();
    
    try {
        let extractedText = '';
        
        switch (fileType) {
            case 'txt':
                extractedText = await parseTextFile(bucket, s3Key);
                break;
            case 'pdf':
                extractedText = await parsePdfWithTextract(bucket, s3Key);
                break;
            case 'image':
                extractedText = await parseImageWithTextract(bucket, s3Key);
                break;
            case 'docx':
                extractedText = await parseDocxFile(bucket, s3Key);
                break;
            case 'xlsx':
                extractedText = await parseXlsxFile(bucket, s3Key);
                break;
            default:
                throw new Error(`Unsupported file type: ${fileType}`);
        }
        
        // Save extracted text to derived folder
        const derivedKey = `derived/${docId}.txt`;
        await s3Client.send(new PutObjectCommand({
            Bucket: bucket,
            Key: derivedKey,
            Body: extractedText,
            ContentType: 'text/plain'
        }));
        
        console.log(`Extracted ${extractedText.length} characters from ${filename}`);
        
        // Emit metrics
        const duration = Date.now() - startTime;
        await emitMetric('ParserDurationMs', duration, 'Milliseconds', [
            { Name: 'FileType', Value: fileType },
            { Name: 'Function', Value: process.env.AWS_LAMBDA_FUNCTION_NAME }
        ]);
        
        return {
            docId,
            s3Key,
            filename,
            textLength: extractedText.length.toString(),
            derivedKey
        };
        
    } catch (error) {
        console.error('Parser error:', error);
        // Emit error metric
        await emitMetric('ParserErrors', 1, 'Count', [
            { Name: 'FileType', Value: fileType || 'unknown' },
            { Name: 'Function', Value: process.env.AWS_LAMBDA_FUNCTION_NAME }
        ]);
        throw error;
    }
};

async function parseTextFile(bucket, key) {
    const response = await s3Client.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
    return await response.Body.transformToString();
}

async function parsePdfWithTextract(bucket, key) {
    try {
        const command = new DetectDocumentTextCommand({
            Document: {
                S3Object: {
                    Bucket: bucket,
                    Name: key
                }
            }
        });
        
        const response = await textractClient.send(command);
        return response.Blocks
            .filter(block => block.BlockType === 'LINE')
            .map(block => block.Text)
            .join('\n');
    } catch (error) {
        console.error('Textract error:', error);
        throw new Error(`PDF parsing failed: ${error.message}`);
    }
}

async function parseImageWithTextract(bucket, key) {
    return await parsePdfWithTextract(bucket, key); // Same Textract API
}

async function parseDocxFile(bucket, key) {
    // For now, return placeholder - would need mammoth library
    const response = await s3Client.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
    return `[DOCX content from ${key} - parsing not yet implemented]`;
}

async function parseXlsxFile(bucket, key) {
    // For now, return placeholder - would need xlsx library  
    const response = await s3Client.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
    return `[XLSX content from ${key} - parsing not yet implemented]`;
}