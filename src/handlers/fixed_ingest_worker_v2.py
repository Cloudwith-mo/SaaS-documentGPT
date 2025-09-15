import json
import boto3
import logging
from datetime import datetime

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Table
table = dynamodb.Table('documentgpt-docs')

def lambda_handler(event, context):
    logger.info(f"Processing event: {json.dumps(event)}")
    
    for record in event['Records']:
        try:
            # Parse SQS message
            body = json.loads(record['body'])
            logger.info(f"Processing message: {body}")
            
            doc_id = body.get('docId')
            doc_name = body.get('docName')
            bucket = body.get('bucket')
            key = body.get('key')
            
            if not all([doc_id, doc_name, bucket, key]):
                logger.error(f"Missing required fields: {body}")
                continue
            
            # Update status to processing (with tenant key)
            update_status(doc_id, 'processing')
            
            # Check if S3 object exists
            try:
                s3.head_object(Bucket=bucket, Key=key)
                logger.info(f"S3 object found: s3://{bucket}/{key}")
            except Exception as e:
                logger.error(f"S3 object not found: s3://{bucket}/{key} - {str(e)}")
                update_status(doc_id, 'error', f"File not found: {str(e)}")
                continue
            
            # Process with Textract
            logger.info(f"Starting Textract processing for {key}")
            textract_response = textract.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                }
            )
            
            # Extract text
            extracted_text = ""
            for block in textract_response['Blocks']:
                if block['BlockType'] == 'LINE':
                    extracted_text += block['Text'] + "\n"
            
            logger.info(f"Extracted {len(extracted_text)} characters of text")
            
            # Update DynamoDB with results (using composite key)
            table.update_item(
                Key={
                    'tenant': 'default',  # Use default tenant
                    'docId': doc_id
                },
                UpdateExpression='SET #status = :status, extractedText = :text, processedAt = :timestamp',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':text': extracted_text[:5000],  # Limit text size
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Successfully processed document {doc_id}")
            
        except Exception as e:
            logger.error(f"Error processing record: {str(e)}")
            if 'doc_id' in locals():
                update_status(doc_id, 'error', str(e))

def update_status(doc_id, status, error_msg=None):
    try:
        update_expr = 'SET #status = :status, updatedAt = :timestamp'
        expr_values = {
            ':status': status,
            ':timestamp': datetime.utcnow().isoformat()
        }
        
        if error_msg:
            update_expr += ', errorMessage = :error'
            expr_values[':error'] = error_msg
        
        table.update_item(
            Key={
                'tenant': 'default',  # Use default tenant
                'docId': doc_id
            },
            UpdateExpression=update_expr,
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues=expr_values
        )
        logger.info(f"Updated status for {doc_id}: {status}")
    except Exception as e:
        logger.error(f"Failed to update status: {str(e)}")