import json
import boto3

def lambda_handler(event, context):
    """Document processing Lambda function"""
    
    try:
        # Process document from SQS message
        if 'Records' in event:
            for record in event['Records']:
                # Process each document
                body = json.loads(record['body'])
                doc_id = body.get('docId')
                
                # Update DynamoDB status
                dynamodb = boto3.resource('dynamodb')
                table = dynamodb.Table('documents')
                
                table.update_item(
                    Key={'docId': doc_id},
                    UpdateExpression='SET #status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': 'processing'}
                )
                
                # Simulate processing
                import time
                time.sleep(1)
                
                # Mark as completed
                table.update_item(
                    Key={'docId': doc_id},
                    UpdateExpression='SET #status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': 'completed'}
                )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Document processed successfully'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }