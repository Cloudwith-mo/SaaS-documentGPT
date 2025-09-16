import json
import boto3
import uuid
from datetime import datetime, timedelta

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}
    
    try:
        # Input validation
        if not event.get('body'):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Request body required'})
            }
        
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid JSON format'})
            }
        
        # Extract filename and content type with multiple field name support
        filename = body.get('fileName') or body.get('filename') or body.get('name')
        content_type = body.get('fileType') or body.get('contentType') or body.get('type')
        
        if not filename:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'fileName is required'})
            }
        
        if not content_type:
            content_type = 'application/pdf'  # Default
        
        # Initialize S3 client
        s3 = boto3.client('s3')
        bucket = 'documentgpt-uploads-1757887191'
        
        # Generate unique S3 key
        key = f"uploads/{uuid.uuid4()}_{filename}"
        
        # Generate presigned URL
        url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': bucket, 'Key': key, 'ContentType': content_type},
            ExpiresIn=3600
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'uploadUrl': url,
                'key': key,
                'bucket': bucket
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }