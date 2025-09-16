import json

def lambda_handler(event, context):
    """Agent presets API handler"""
    
    http_method = event.get('httpMethod', 'GET')
    
    if http_method == 'GET':
        agents = [
            {
                "id": "legal_expert",
                "name": "Legal Expert",
                "description": "Specialized in legal document analysis",
                "model": "gpt-4-turbo",
                "temperature": 0.1
            },
            {
                "id": "finance_expert", 
                "name": "Finance Expert",
                "description": "Financial document review and analysis",
                "model": "gpt-4-turbo",
                "temperature": 0.2
            },
            {
                "id": "compliance_expert",
                "name": "Compliance Expert", 
                "description": "Regulatory compliance and risk assessment",
                "model": "gpt-4-turbo",
                "temperature": 0.1
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
            'body': json.dumps(agents)
        }
    
    elif http_method == 'POST':
        try:
            body = json.loads(event.get('body', '{}'))
            if 'name' not in body:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Name required'})
                }
            
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'id': 'new-agent', 'created': True})
            }
        except:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Invalid JSON'})
            }
    
    return {
        'statusCode': 405,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': 'Method not allowed'})
    }