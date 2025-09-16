import json

def lambda_handler(event, context):
    """Debate export handler"""
    
    try:
        # Parse request body
        if event.get('body'):
            body = json.loads(event['body'])
        else:
            body = event
            
        if not body:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Data required'})
            }
        
        # Generate markdown export
        consensus = body.get('consensus', 'No consensus reached')
        debate_cols = body.get('debate_cols', {})
        
        markdown = f"# Debate Export\n\n## Consensus\n{consensus}\n\n"
        
        for agent, arguments in debate_cols.items():
            markdown += f"## {agent} Arguments\n"
            for i, arg in enumerate(arguments, 1):
                markdown += f"{i}. {arg}\n"
            markdown += "\n"
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/markdown',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Content-Disposition': 'attachment; filename=debate_export.md'
            },
            'body': markdown
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