import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ParsePilot-Facts')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': 'https://documentgpt.io',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}
    
    try:
        doc_id = event.get('pathParameters', {}).get('docId')
        if not doc_id:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'docId required'})}
        
        # Get document content from DynamoDB - try multiple approaches
        response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': 'guest'}
        )
        
        # Extract text content - look for any text-related fields
        content_parts = []
        doc_facts = []
        
        for item in response.get('Items', []):
            if item.get('doc_id') == doc_id:
                doc_facts.append(item)
                # Look for various content fields
                field_key = item.get('field_key', '')
                value_str = item.get('value_str', '')
                
                if field_key in ['content', 'text', 'raw_text', 'extracted_text'] and value_str:
                    content_parts.append(value_str)
                elif field_key and value_str and len(value_str) > 50:  # Substantial text content
                    content_parts.append(f"{field_key}: {value_str}")
        
        # If we have document facts but no long content, create structured preview
        if doc_facts and not content_parts:
            content_parts = [f"Document ID: {doc_id}", "\nExtracted Information:"]
            for item in doc_facts[:10]:  # Show first 10 facts
                field_key = item.get('field_key', 'Unknown')
                value_str = item.get('value_str', '')
                if value_str and field_key != 'metadata':
                    content_parts.append(f"• {field_key}: {value_str}")
        
        # Final fallback to sample content
        if not content_parts:
            content_parts = [
                f"Document: {doc_id}",
                "This is a sample document preview.",
                "The actual document content would appear here after processing.",
                "Key sections and text would be extracted and displayed.",
                "You can ask questions about this document in the chat panel."
            ]
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'docId': doc_id,
                'content': '\n\n'.join(content_parts),
                'pages': 1
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }