import json
import boto3
import uuid
import time

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-user-id',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}
    
    try:
        body = json.loads(event.get('body', '{}'))
        filename = body.get('filename', 'document.txt')
        content_type = body.get('contentType', 'text/plain')
        
        doc_id = f"doc_{int(time.time() * 1000)}_{uuid.uuid4().hex[:12]}"
        file_key = f"{doc_id}/{filename}"
        
        upload_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': 'documentgpt-uploads', 'Key': file_key, 'ContentType': content_type},
            ExpiresIn=300
        )
        
        return {
            'statusCode': 200,
            'headers': {**headers, 'Content-Type': 'application/json'},
            'body': json.dumps({
                'docId': doc_id,
                'uploadUrl': upload_url,
                'key': file_key,
                'filename': filename
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }