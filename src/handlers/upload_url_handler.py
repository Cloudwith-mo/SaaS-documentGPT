import json
import boto3
import uuid
from datetime import datetime, timedelta

s3 = boto3.client('s3')
BUCKET = 'documentgpt-uploads-1757887191'

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': 'https://documentgpt.io',
        'Access-Control-Allow-Methods': 'POST,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}
    
    try:
        # Handle POST request with JSON body
        if event.get('body'):
            body = json.loads(event['body'])
            filename = body.get('filename', 'document.pdf')
            content_type = body.get('contentType', 'application/pdf')
        else:
            # Fallback to query parameters
            params = event.get('queryStringParameters') or {}
            filename = params.get('filename', 'document.pdf')
            content_type = params.get('contentType', 'application/pdf')
        
        # Generate unique S3 key
        key = f"uploads/{uuid.uuid4()}_{filename}"
        
        # Generate presigned URL
        url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': BUCKET, 'Key': key, 'ContentType': content_type},
            ExpiresIn=3600
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'uploadUrl': url,
                'key': key,
                'bucket': BUCKET
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }