import json
import boto3
import uuid
from datetime import datetime

textract = boto3.client('textract')
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # Handle OPTIONS request for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': ''
        }
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        s3_key = body.get('s3Key')
        filename = body.get('filename', 'document')
        
        if not s3_key:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing s3Key'})
            }
        
        # Process with Textract
        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': 'documentgpt-uploads-1757887191',
                    'Name': s3_key
                }
            }
        )
        
        # Extract text and fields
        extracted_text = ""
        fields = {}
        
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                extracted_text += block['Text'] + "\n"
            elif block['BlockType'] == 'KEY_VALUE_SET':
                if 'KEY' in block.get('EntityTypes', []):
                    key_text = get_text_from_block(block, response['Blocks'])
                    value_block = find_value_block(block, response['Blocks'])
                    if value_block:
                        value_text = get_text_from_block(value_block, response['Blocks'])
                        fields[key_text] = value_text
        
        # Determine document type
        doc_type = classify_document(extracted_text)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'docId': str(uuid.uuid4()),
                'filename': filename,
                'docType': doc_type,
                'fields': fields,
                'extractedText': extracted_text[:1000],  # Limit text
                'processedAt': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def get_text_from_block(block, all_blocks):
    text = ""
    if 'Relationships' in block:
        for relationship in block['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    child_block = next((b for b in all_blocks if b['Id'] == child_id), None)
                    if child_block and child_block['BlockType'] == 'WORD':
                        text += child_block['Text'] + " "
    return text.strip()

def find_value_block(key_block, all_blocks):
    if 'Relationships' in key_block:
        for relationship in key_block['Relationships']:
            if relationship['Type'] == 'VALUE':
                for value_id in relationship['Ids']:
                    return next((b for b in all_blocks if b['Id'] == value_id), None)
    return None

def classify_document(text):
    text_lower = text.lower()
    if 'w-2' in text_lower or 'wage and tax statement' in text_lower:
        return 'W-2'
    elif '1099' in text_lower:
        return '1099'
    elif 'invoice' in text_lower or 'bill to' in text_lower:
        return 'Invoice'
    elif 'receipt' in text_lower or 'total' in text_lower:
        return 'Receipt'
    else:
        return 'Document'