import json
import boto3

def lambda_handler(event, context):
    """Notification dispatcher Lambda function"""
    
    try:
        sns = boto3.client('sns')
        
        # Get topic ARN
        topic_arn = 'arn:aws:sns:us-east-1:995805900737:document-processing-notifications'
        
        # Process notification event
        message = event.get('message', 'Document processing notification')
        
        # Send SNS notification
        response = sns.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject='DocumentGPT Notification'
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Notification sent successfully',
                'messageId': response['MessageId']
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }