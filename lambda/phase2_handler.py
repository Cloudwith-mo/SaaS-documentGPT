import json
import boto3
import os
import urllib3
import base64
import hashlib
import time
from datetime import datetime

# Import Phase 2 modules
from gmail_integration import send_gmail, create_google_sheet
from folders_system import create_folder, get_user_folders, move_document_to_folder

http = urllib3.PoolManager()

BUCKET_NAME = 'documentgpt-uploads'
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
COGNITO_USER_POOL_ID = 'us-east-1_Yvd3qyxO4'
COGNITO_CLIENT_ID = '2so2ts96g17aileldepb45rleo'

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
cognito_client = boto3.client('cognito-idp')

try:
    cache_table = dynamodb.Table('documentgpt-cache')
    users_table = dynamodb.Table('documentgpt-users')
    folders_table = dynamodb.Table('documentgpt-folders')
except:
    cache_table = None
    users_table = None
    folders_table = None

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }
    
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return {'statusCode': 200, 'headers': headers, 'body': ''}
        
        path = event.get('path', '')
        method = event.get('httpMethod', '')
        
        # Existing endpoints
        if path == '/upload' and method == 'POST':
            return handle_upload(event, headers)
        elif path == '/chat' and method == 'POST':
            return handle_chat(event, headers)
        elif path == '/live-assist' and method == 'POST':
            return handle_live_assist(event, headers)
        elif path == '/agent' and method == 'POST':
            return handle_agent_enhanced(event, headers)
        elif path == '/user' and method == 'POST':
            return handle_user(event, headers)
        
        # Phase 2 endpoints
        elif path == '/auth/login' and method == 'POST':
            return handle_login(event, headers)
        elif path == '/auth/register' and method == 'POST':
            return handle_register(event, headers)
        elif path == '/folders' and method == 'POST':
            return handle_folders(event, headers)
        elif path == '/folders' and method == 'GET':
            return handle_get_folders(event, headers)
        
        else:
            return {'statusCode': 404, 'headers': headers, 'body': json.dumps({'error': 'Not found'})}
            
    except Exception as e:
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}

def handle_login(event, headers):
    """Handle user login with Cognito"""
    body = json.loads(event['body'])
    email = body.get('email')
    password = body.get('password')
    
    try:
        response = cognito_client.admin_initiate_auth(
            UserPoolId=COGNITO_USER_POOL_ID,
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'access_token': response['AuthenticationResult']['AccessToken'],
                'id_token': response['AuthenticationResult']['IdToken'],
                'refresh_token': response['AuthenticationResult']['RefreshToken']
            })
        }
    except Exception as e:
        return {
            'statusCode': 401,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_register(event, headers):
    """Handle user registration with Cognito"""
    body = json.loads(event['body'])
    email = body.get('email')
    password = body.get('password')
    name = body.get('name', '')
    
    try:
        response = cognito_client.admin_create_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'name', 'Value': name},
                {'Name': 'email_verified', 'Value': 'true'}
            ],
            TemporaryPassword=password,
            MessageAction='SUPPRESS'
        )
        
        # Set permanent password
        cognito_client.admin_set_user_password(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email,
            Password=password,
            Permanent=True
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'success': True, 'user_id': response['User']['Username']})
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_folders(event, headers):
    """Handle folder operations"""
    body = json.loads(event['body'])
    action = body.get('action')
    user_id = body.get('user_id')
    
    if action == 'create':
        folder_name = body.get('folder_name')
        parent_id = body.get('parent_id')
        folder = create_folder(user_id, folder_name, parent_id)
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(folder)
        }
    
    elif action == 'move_document':
        document_id = body.get('document_id')
        folder_id = body.get('folder_id')
        result = move_document_to_folder(user_id, document_id, folder_id)
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(result)
        }
    
    return {
        'statusCode': 400,
        'headers': headers,
        'body': json.dumps({'error': 'Invalid action'})
    }

def handle_get_folders(event, headers):
    """Get user folders"""
    user_id = event.get('queryStringParameters', {}).get('user_id')
    if not user_id:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'user_id required'})
        }
    
    folders = get_user_folders(user_id)
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({'folders': folders})
    }

def handle_agent_enhanced(event, headers):
    """Enhanced AI Agents with real API integrations"""
    body = json.loads(event['body'])
    agent_type = body.get('agent_type')
    content = body.get('content', '')
    user_email = body.get('user_email', '')
    user_credentials = body.get('user_credentials', {})
    
    try:
        # Generate AI response first
        response = openai_chat(get_agent_prompt(agent_type, content), model='gpt-4o-mini')
        
        # Real integrations for premium users
        if user_credentials and agent_type == 'email':
            gmail_result = send_gmail(response, user_credentials)
            if gmail_result['success']:
                response += f"\n\n✅ Email sent successfully! Message ID: {gmail_result['message_id']}"
            else:
                response += f"\n\n❌ Email sending failed: {gmail_result['error']}"
        
        elif user_credentials and agent_type == 'sheets':
            sheets_result = create_google_sheet(response, user_credentials)
            if sheets_result['success']:
                response += f"\n\n✅ Google Sheet created: {sheets_result['url']}"
            else:
                response += f"\n\n❌ Sheet creation failed: {sheets_result['error']}"
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'agent': agent_type,
                'result': response,
                'status': 'completed'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def get_agent_prompt(agent_type, content):
    """Get prompt for AI agent"""
    prompts = {
        'email': f"Draft a professional email based on this content. Include subject line and body: {content}",
        'sheets': f"Extract data and format as CSV with headers: {content}",
        'calendar': f"Identify dates/events and format as calendar entries: {content}",
        'save': f"Suggest filename and folder structure: {content}",
        'export': f"Format for export with clean structure: {content}",
        'summary': f"Create concise summary with key points: {content}"
    }
    return prompts.get(agent_type, f"Process this content: {content}")

def openai_chat(prompt, model='gpt-4o-mini'):
    """OpenAI chat completion"""
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 500,
        'temperature': 0.3
    }
    
    response = http.request('POST', url, body=json.dumps(data), headers=headers)
    result = json.loads(response.data.decode('utf-8'))
    
    if 'choices' in result and len(result['choices']) > 0:
        return result['choices'][0]['message']['content']
    else:
        raise Exception(f"OpenAI API error: {result}")

# Include all existing functions from enhanced_handler.py
def handle_live_assist(event, headers):
    """Live AI assistant - same as before"""
    body = json.loads(event['body'])
    content = body.get('content', '')
    user_id = body.get('user_id', 'anonymous')
    
    if len(content) < 20:
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'suggestions': []})
        }
    
    prompt = f"""Analyze this text and provide 1-2 brief suggestions for improvement:
    
    Focus on grammar, clarity, tone, and deeper insights.
    Text: "{content[-500:]}"
    
    Format as:
    1. [suggestion]
    2. [suggestion]"""
    
    try:
        response = openai_chat(prompt, model='gpt-4o-mini')
        suggestions = parse_suggestions(response)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'suggestions': suggestions})
        }
    except Exception as e:
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'suggestions': []})
        }

def parse_suggestions(response):
    """Parse AI response into suggestions"""
    suggestions = []
    lines = response.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and (line.startswith('1.') or line.startswith('2.') or line.startswith('-')):
            suggestion = line.replace('1.', '').replace('2.', '').replace('-', '').strip()
            if suggestion:
                suggestions.append(suggestion)
    
    return suggestions[:2]

# Add other existing functions (handle_upload, handle_chat, etc.)
def handle_upload(event, headers):
    """File upload - same as enhanced_handler.py"""
    # Copy implementation from enhanced_handler.py
    pass

def handle_chat(event, headers):
    """Chat handling - same as enhanced_handler.py"""
    # Copy implementation from enhanced_handler.py
    pass

def handle_user(event, headers):
    """User management - same as enhanced_handler.py"""
    # Copy implementation from enhanced_handler.py
    pass