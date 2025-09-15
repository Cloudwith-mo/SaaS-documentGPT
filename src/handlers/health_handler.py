import json
from datetime import datetime

def lambda_handler(event, context):
    """Health check API handler"""
    
    health_data = {
        'status': 'healthy',
        'version': 'v5',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'documentgpt-api',
        'environment': 'production'
    }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(health_data)
    }