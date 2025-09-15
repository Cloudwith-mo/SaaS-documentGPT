import json

def lambda_handler(event, context):
    """Agent presets API handler"""
    
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
        'body': json.dumps({'agents': agents})
    }