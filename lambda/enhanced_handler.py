import json
import boto3
import os
import urllib3
import base64
import hashlib
import time
from datetime import datetime, timedelta

http = urllib3.PoolManager()

BUCKET_NAME = 'documentgpt-uploads'
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

try:
    cache_table = dynamodb.Table('documentgpt-cache')
    users_table = dynamodb.Table('documentgpt-users')
except:
    cache_table = None
    users_table = None

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
        
        if path == '/upload' and method == 'POST':
            return handle_upload(event, headers)
        elif path == '/chat' and method == 'POST':
            return handle_chat(event, headers)
        elif path == '/live-assist' and method == 'POST':
            return handle_live_assist(event, headers)
        elif path == '/agent' and method == 'POST':
            return handle_agent(event, headers)
        elif path == '/user' and method == 'POST':
            return handle_user(event, headers)
        else:
            return {'statusCode': 404, 'headers': headers, 'body': json.dumps({'error': 'Not found'})}
            
    except Exception as e:
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}

def handle_live_assist(event, headers):
    """Live AI assistant for real-time writing enhancement"""
    body = json.loads(event['body'])
    content = body.get('content', '')
    user_id = body.get('user_id', 'anonymous')
    
    if len(content) < 20:
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'suggestions': []})
        }
    
    # Get user writing patterns
    user_context = get_user_context(user_id)
    
    prompt = f"""You are a live writing assistant. Analyze this text and provide 1-2 brief, actionable suggestions.

Focus on:
- Grammar and clarity improvements
- Tone consistency with user's style
- Deeper insights or questions to explore
- Flow and readability

User's typical style: {user_context}
Current text: "{content[-500:]}"

Respond with 1-2 concise suggestions in this format:
1. [Brief suggestion]
2. [Brief suggestion]

Be helpful but not overwhelming."""

    try:
        response = openai_chat(prompt, model='gpt-4o-mini')
        suggestions = parse_suggestions(response)
        
        # Update user patterns
        update_user_patterns(user_id, content)
        
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

def handle_agent(event, headers):
    """AI Agents for automation tasks"""
    body = json.loads(event['body'])
    agent_type = body.get('agent_type')
    content = body.get('content', '')
    user_email = body.get('user_email', '')
    
    agent_prompts = {
        'email': f"""Draft a professional email based on this content. Format as:
Subject: [subject line]
Body: [email body]

Content: "{content}" """,
        
        'sheets': f"""Extract structured data from this content and format as CSV:
- Identify tables, lists, or data points
- Create appropriate column headers
- Format as comma-separated values

Content: "{content}" """,
        
        'calendar': f"""Identify dates, times, and events in this content. Format as:
Event: [event name]
Date: [date]
Time: [time if mentioned]
Notes: [additional details]

Content: "{content}" """,
        
        'save': f"""Suggest a filename and folder structure for this content:
Filename: [descriptive filename]
Folder: [suggested folder/category]
Tags: [relevant tags]

Content: "{content}" """,
        
        'export': f"""Format this content for export. Provide:
1. Clean formatted version
2. Key points summary
3. Action items (if any)

Content: "{content}" """,
        
        'summary': f"""Create a concise summary with:
1. Main points (3-5 bullets)
2. Key insights
3. Action items (if any)

Content: "{content}" """
    }
    
    if agent_type not in agent_prompts:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'Invalid agent type'})
        }
    
    try:
        response = openai_chat(agent_prompts[agent_type], model='gpt-4o-mini')
        
        # For email agent, could integrate with Gmail API here
        # For sheets agent, could integrate with Google Sheets API here
        # For calendar agent, could integrate with Google Calendar API here
        
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

def handle_user(event, headers):
    """User management and preferences"""
    body = json.loads(event['body'])
    action = body.get('action')
    user_id = body.get('user_id')
    
    if action == 'get_profile':
        profile = get_user_profile(user_id)
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(profile)
        }
    elif action == 'update_profile':
        update_user_profile(user_id, body.get('profile', {}))
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'status': 'updated'})
        }
    
    return {
        'statusCode': 400,
        'headers': headers,
        'body': json.dumps({'error': 'Invalid action'})
    }

def handle_chat(event, headers):
    """Enhanced chat with journal mode support"""
    body = json.loads(event['body'])
    messages = body['messages']
    vs_id = body.get('vector_store_id')
    user_email = body.get('user_email', 'user@documentgpt.io')
    
    # Check cache first
    cache_key = hashlib.md5(json.dumps(messages).encode()).hexdigest()
    if cache_table:
        try:
            response = cache_table.get_item(Key={'cache_key': cache_key})
            if 'Item' in response:
                cached_response = response['Item']['response']
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({'response': cached_response, 'cached': True})
                }
        except:
            pass
    
    question = messages[-1]['content'] if messages else ''
    
    # Journal mode (no vector store)
    if not vs_id:
        try:
            response = openai_chat(question, model='gpt-4o-mini')
            
            # Cache response
            if cache_table:
                try:
                    cache_table.put_item(
                        Item={
                            'cache_key': cache_key,
                            'response': response,
                            'ttl': int(time.time()) + 86400  # 24 hours
                        }
                    )
                except:
                    pass
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'response': response})
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': str(e)})
            }
    
    # Document mode (with vector store)
    assistant_response = openai_request('POST', '/assistants', {
        'model': 'gpt-4o-mini-2024-07-18',
        'name': 'Document Analyzer',
        'instructions': 'You are a helpful assistant that analyzes documents. Answer questions based on the uploaded document content. Be concise and helpful.',
        'tools': [{'type': 'file_search'}],
        'tool_resources': {
            'file_search': {
                'vector_store_ids': [vs_id]
            }
        }
    })
    
    if not assistant_response.get('id'):
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Failed to create assistant'})
        }
    
    assistant_id = assistant_response['id']
    
    try:
        thread_response = openai_request('POST', '/threads', {})
        thread_id = thread_response['id']
        
        openai_request('POST', f'/threads/{thread_id}/messages', {
            'role': 'user',
            'content': question
        })
        
        run_response = openai_request('POST', f'/threads/{thread_id}/runs', {
            'assistant_id': assistant_id
        })
        
        run_id = run_response['id']
        
        # Wait for completion
        for _ in range(30):
            run_status = openai_request('GET', f'/threads/{thread_id}/runs/{run_id}')
            if run_status['status'] == 'completed':
                break
            elif run_status['status'] in ['failed', 'cancelled', 'expired']:
                raise Exception(f"Run failed: {run_status['status']}")
            time.sleep(1)
        
        messages_response = openai_request('GET', f'/threads/{thread_id}/messages')
        
        if messages_response.get('data') and len(messages_response['data']) > 0:
            assistant_message = messages_response['data'][0]
            content = assistant_message['content'][0]['text']['value']
            formatted_content = format_response(content)
            
            # Cache response
            if cache_table:
                try:
                    cache_table.put_item(
                        Item={
                            'cache_key': cache_key,
                            'response': formatted_content,
                            'ttl': int(time.time()) + 86400
                        }
                    )
                except:
                    pass
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'response': formatted_content})
            }
        
    finally:
        try:
            openai_request('DELETE', f'/assistants/{assistant_id}')
        except:
            pass
    
    return {
        'statusCode': 500,
        'headers': headers,
        'body': json.dumps({'error': 'No response generated'})
    }

def handle_upload(event, headers):
    """File upload with enhanced processing"""
    body = json.loads(event['body'])
    file_content = base64.b64decode(body['file_content'])
    filename = body['filename']
    user_id = body.get('user_id', 'default')
    
    file_hash = hashlib.md5(file_content).hexdigest()
    
    # Check if file already processed
    try:
        s3_client.head_object(Bucket=BUCKET_NAME, Key=f"files/{file_hash}.json")
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=f"files/{file_hash}.json")
        file_metadata = json.loads(response['Body'].read())
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'File already processed',
                'vector_store_id': file_metadata['vector_store_id'],
                'file_id': file_metadata['file_id']
            })
        }
    except:
        pass
    
    vs_id = ensure_vector_store(user_id)
    file_response = openai_file_upload(filename, file_content)
    
    if not file_response.get('id'):
        raise Exception(f"File upload failed: {file_response}")
    
    file_id = file_response['id']
    openai_request('POST', f'/vector_stores/{vs_id}/files', {'file_id': file_id})
    
    file_metadata = {
        'filename': filename,
        'file_hash': file_hash,
        'file_id': file_id,
        'vector_store_id': vs_id,
        'user_id': user_id,
        'uploaded_at': datetime.now().isoformat()
    }
    
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=f"files/{file_hash}.json",
        Body=json.dumps(file_metadata),
        ContentType='application/json'
    )
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'message': 'File uploaded successfully',
            'vector_store_id': vs_id,
            'file_id': file_id
        })
    }

# Helper functions
def openai_chat(prompt, model='gpt-4o-mini'):
    """Simple OpenAI chat completion"""
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

def get_user_context(user_id):
    """Get user writing patterns for personalization"""
    if not users_table:
        return "Professional, clear writing style"
    
    try:
        response = users_table.get_item(Key={'user_id': user_id})
        if 'Item' in response:
            patterns = response['Item'].get('writing_patterns', {})
            return f"Tone: {patterns.get('tone', 'professional')}, Style: {patterns.get('style', 'clear')}"
    except:
        pass
    
    return "Professional, clear writing style"

def update_user_patterns(user_id, content):
    """Update user writing patterns"""
    if not users_table:
        return
    
    # Simple pattern analysis
    word_count = len(content.split())
    sentence_count = content.count('.') + content.count('!') + content.count('?')
    avg_sentence_length = word_count / max(sentence_count, 1)
    
    patterns = {
        'avg_sentence_length': avg_sentence_length,
        'word_count': word_count,
        'last_updated': datetime.now().isoformat()
    }
    
    try:
        users_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET writing_patterns = :patterns',
            ExpressionAttributeValues={':patterns': patterns}
        )
    except:
        pass

def parse_suggestions(response):
    """Parse AI response into suggestion list"""
    suggestions = []
    lines = response.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and (line.startswith('1.') or line.startswith('2.') or line.startswith('-')):
            suggestion = line.replace('1.', '').replace('2.', '').replace('-', '').strip()
            if suggestion:
                suggestions.append(suggestion)
    
    return suggestions[:2]  # Max 2 suggestions

def get_user_profile(user_id):
    """Get user profile"""
    if not users_table:
        return {'user_id': user_id, 'preferences': {}}
    
    try:
        response = users_table.get_item(Key={'user_id': user_id})
        if 'Item' in response:
            return response['Item']
    except:
        pass
    
    return {'user_id': user_id, 'preferences': {}}

def update_user_profile(user_id, profile):
    """Update user profile"""
    if not users_table:
        return
    
    try:
        users_table.put_item(Item={
            'user_id': user_id,
            'preferences': profile,
            'updated_at': datetime.now().isoformat()
        })
    except:
        pass

def ensure_vector_store(user_id):
    """Ensure vector store exists for user"""
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=f"users/{user_id}/vector_store.json")
        metadata = json.loads(response['Body'].read())
        return metadata['vector_store_id']
    except:
        vs_response = openai_request('POST', '/vector_stores', {'name': f'user:{user_id}'})
        if vs_response.get('id'):
            vs_id = vs_response['id']
            metadata = {'vector_store_id': vs_id, 'user_id': user_id}
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=f"users/{user_id}/vector_store.json",
                Body=json.dumps(metadata),
                ContentType='application/json'
            )
            return vs_id
        else:
            raise Exception(f"Failed to create vector store: {vs_response}")

def openai_request(method, endpoint, data=None):
    """OpenAI API request helper"""
    url = f'https://api.openai.com/v1{endpoint}'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json',
        'OpenAI-Beta': 'assistants=v2'
    }
    
    if method == 'POST' and data:
        response = http.request(method, url, body=json.dumps(data), headers=headers)
    elif method == 'DELETE':
        response = http.request(method, url, headers=headers)
    else:
        response = http.request(method, url, headers=headers)
    
    return json.loads(response.data.decode('utf-8'))

def format_response(content):
    """Format AI response for better readability"""
    import re
    content = re.sub(r'【\d+:\d+†source】', '', content)
    content = content.replace('**', '\n**')
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()

def openai_file_upload(filename, file_content):
    """Upload file to OpenAI"""
    url = 'https://api.openai.com/v1/files'
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="purpose"\r\n\r\n'
        f'assistants\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f'Content-Type: text/plain\r\n\r\n'
    ).encode('utf-8') + file_content + f'\r\n--{boundary}--\r\n'.encode('utf-8')
    
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    }
    
    response = http.request('POST', url, body=body, headers=headers)
    return json.loads(response.data.decode('utf-8'))