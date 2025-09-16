import json
from datetime import datetime

def lambda_handler(event, context):
    """Health check endpoint for /health and /healthz"""
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps({
            'status': 'healthy',
            'service': 'documentgpt',
            'version': '5.0.0',
            'timestamp': datetime.now().isoformat()
        })
    }