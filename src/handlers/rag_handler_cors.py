import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ParsePilot-Facts')

def lambda_handler(event, context):
    # CORS headers for all responses
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    # Handle OPTIONS preflight request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Input validation - check for request body
        if not event.get('body'):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Request body required'})
            }
        
        # Parse JSON with error handling
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid JSON format'})
            }
            
        # Support multiple field names for compatibility
        question = body.get('question') or body.get('query', '')
        doc_id = body.get('docId') or body.get('document_id', '')
        
        # Validate required fields
        if not question.strip():
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Question/query is required'})
            }
        
        # Security validation
        if '<script>' in question.lower() or 'javascript:' in question.lower():
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid input detected'})
            }
        
        # Length validation
        if len(question) > 5000:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Query too long (max 5000 characters)'})
            }
        
        # Check if document is still processing
        try:
            response = table.query(
                KeyConditionExpression='PK = :pk',
                FilterExpression='doc_id = :doc_id',
                ExpressionAttributeValues={
                    ':pk': 'guest',
                    ':doc_id': doc_id
                }
            )
            
            if not response.get('Items'):
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'answer': 'Document is still being processed. Status: queued',
                        'citations': []
                    })
                }
            
            # Get document facts for analysis
            doc_facts = response['Items']
            
            # Create a comprehensive answer based on document facts
            if 'summarize' in question.lower():
                # Generate summary from document facts
                summary_parts = []
                for item in doc_facts:
                    field_key = item.get('field_key', '')
                    value_str = item.get('value_str', '')
                    if value_str and len(value_str) > 20:
                        summary_parts.append(f"{field_key}: {value_str}")
                
                if summary_parts:
                    answer = "Document Summary:\n\n" + "\n".join(summary_parts[:10])
                else:
                    answer = "Document processing is complete, but detailed content is not yet available for summarization."
            else:
                # Answer specific questions based on document facts
                relevant_facts = []
                question_lower = question.lower()
                
                for item in doc_facts:
                    field_key = item.get('field_key', '').lower()
                    value_str = item.get('value_str', '')
                    
                    # Simple keyword matching
                    if any(word in field_key for word in question_lower.split()):
                        relevant_facts.append(f"{item.get('field_key', '')}: {value_str}")
                
                if relevant_facts:
                    answer = "Based on the document:\n\n" + "\n".join(relevant_facts[:5])
                else:
                    answer = f"I found information in the document, but couldn't find specific details related to '{question}'. The document contains {len(doc_facts)} data points that have been processed."
            
            response_data = {
                'answer': answer,
                'citations': [{
                    'docId': doc_id,
                    'page': 1,
                    'text': 'Document content processed'
                }]
            }
            
        except Exception as db_error:
            # Fallback response
            response_data = {
                'answer': 'Document is still being processed. Status: queued',
                'citations': []
            }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }