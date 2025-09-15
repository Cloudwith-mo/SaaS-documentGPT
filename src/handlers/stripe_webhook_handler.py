import json
import boto3

def lambda_handler(event, context):
    """Stripe webhook handler"""
    
    try:
        # Parse webhook payload
        if event.get('body'):
            body = json.loads(event['body'])
        else:
            body = event
            
        webhook_type = body.get('type', '')
        
        if webhook_type == 'checkout.session.completed':
            # Handle successful payment
            session = body.get('data', {}).get('object', {})
            customer_id = session.get('customer')
            
            # Update user subscription in DynamoDB
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table('users')
            
            table.update_item(
                Key={'customerId': customer_id},
                UpdateExpression='SET subscription_status = :status',
                ExpressionAttributeValues={':status': 'active'}
            )
            
        elif webhook_type == 'customer.subscription.deleted':
            # Handle subscription cancellation
            subscription = body.get('data', {}).get('object', {})
            customer_id = subscription.get('customer')
            
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table('users')
            
            table.update_item(
                Key={'customerId': customer_id},
                UpdateExpression='SET subscription_status = :status',
                ExpressionAttributeValues={':status': 'cancelled'}
            )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'received': True})
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