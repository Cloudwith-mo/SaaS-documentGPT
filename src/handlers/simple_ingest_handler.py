import json
import boto3
import logging
from datetime import datetime

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

# Configuration
QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/995805900737/documentgpt-ingest-queue'
table = dynamodb.Table('documentgpt-docs')

def lambda_handler(event, context):
    logger.info(f"Ingest request: {json.dumps(event)}")
    
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': ''
        }
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        doc_id = body.get('docId')
        doc_name = body.get('docName')
        bucket = body.get('bucket')
        key = body.get('key')
        
        if not all([doc_id, doc_name, bucket, key]):
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing required fields: docId, docName, bucket, key'})
            }
        
        # Create DynamoDB record
        table.put_item(
            Item={
                'tenant': 'default',
                'docId': doc_id,
                'docName': doc_name,
                'status': 'queued',
                'bucket': bucket,
                'key': key,
                'createdAt': datetime.utcnow().isoformat(),
                'updatedAt': datetime.utcnow().isoformat()
            }
        )
        
        # Send to SQS queue
        message = {
            'docId': doc_id,
            'docName': doc_name,
            'bucket': bucket,
            'key': key
        }
        
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message)
        )
        
        logger.info(f"Queued document {doc_id} for processing")
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'queued': True,
                'docId': doc_id,
                'docName': doc_name
            })
        }
        
    except Exception as e:
        logger.error(f"Ingest error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }