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
        
        # Mock search results with normalized bbox coordinates (0-1 range)
        matches = [
            {
                "page": 1,
                "text": f"Search result for: {query}",
                "confidence": 0.95,
                "bbox": {"x": 0.25, "y": 0.30, "w": 0.40, "h": 0.08}
            },
            {
                "page": 2, 
                "text": f"Another relevant passage for: {query}",
                "confidence": 0.87,
                "bbox": {"x": 0.15, "y": 0.50, "w": 0.60, "h": 0.12}
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
                'matches': matches,
                'total': len(matches),
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