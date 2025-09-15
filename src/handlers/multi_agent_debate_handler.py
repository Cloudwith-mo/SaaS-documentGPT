import json
import boto3
import openai
import os
from typing import Dict, List

def lambda_handler(event, context):
    """Multi-agent debate API handler"""
    
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
        
        # Multi-agent debate simulation
        agents = [
            {
                "name": "Legal Expert",
                "response": f"From a legal perspective regarding '{query}': This requires careful analysis of contractual obligations and regulatory compliance.",
                "confidence": 0.92
            },
            {
                "name": "Finance Expert", 
                "response": f"Financially speaking about '{query}': We need to consider cost implications, budget constraints, and ROI analysis.",
                "confidence": 0.88
            },
            {
                "name": "Compliance Expert",
                "response": f"For compliance purposes on '{query}': This must align with industry regulations and internal policies.",
                "confidence": 0.90
            }
        ]
        
        consensus = "All agents agree that this matter requires comprehensive analysis across legal, financial, and compliance dimensions."
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'agents': agents,
                'consensus': consensus,
                'query': query,
                'timestamp': context.aws_request_id if context else 'local'
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