import json
import boto3
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")
    
    # Handle OPTIONS for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': ''
        }
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('documentgpt-docs')
        
        # Scan for recent documents
        response = table.scan(
            Limit=10,
            ProjectionExpression='docId, docName, #status, createdAt',
            ExpressionAttributeNames={'#status': 'status'}
        )
        
        documents = []
        for item in response.get('Items', []):
            documents.append({
                'docId': item.get('docId'),
                'docName': item.get('docName', 'Unknown'),
                'status': item.get('status', 'processing'),
                'createdAt': item.get('createdAt', '')
            })
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps({'documents': documents})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }