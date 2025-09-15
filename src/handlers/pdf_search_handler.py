import json
import boto3
from typing import Dict, List

def lambda_handler(event, context):
    """PDF search API handler"""
    
    try:
        # Parse request body
        if event.get('body'):
            body = json.loads(event['body'])
        else:
            body = event
            
        query = body.get('query', '').strip()
        document_id = body.get('document_id', body.get('docId'))
        
        if not query:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Query is required'})
            }
        
        # Input validation
        if '<script>' in query.lower() or "' or " in query.lower():
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Invalid input detected'})
            }
        
        # Mock search results for now
        results = [
            {
                "page": 1,
                "text": f"Search result for: {query}",
                "confidence": 0.95,
                "bbox": [100, 200, 300, 250]
            },
            {
                "page": 2, 
                "text": f"Another relevant passage for: {query}",
                "confidence": 0.87,
                "bbox": [150, 300, 400, 350]
            }
        ]
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'results': results,
                'total': len(results),
                'query': query
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }