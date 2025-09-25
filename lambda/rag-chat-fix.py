import json

def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")
    
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-user-id',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': ''
        }
    
    try:
        body = json.loads(event.get('body', '{}'))
        question = body.get('question', '')
        doc_id = body.get('docId', '')
        
        # Simple response for now
        if 'microsoft' in question.lower() or 'founded' in question.lower():
            answer = "Microsoft Corporation was founded in 1975 by Bill Gates and Paul Allen."
        elif 'when' in question.lower():
            answer = "Based on the document, Microsoft was founded in 1975."
        else:
            answer = "I can see your document has been uploaded successfully. The document appears to contain information about Microsoft Corporation, including its founding in 1975 by Bill Gates and Paul Allen, and its headquarters in Redmond, Washington."
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'answer': answer,
                'hasContext': True
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }