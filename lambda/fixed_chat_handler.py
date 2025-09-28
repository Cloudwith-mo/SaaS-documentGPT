import json
import boto3
import os
import urllib3
import base64
import hashlib
import time

http = urllib3.PoolManager()

BUCKET_NAME = 'documentgpt-uploads'
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

try:
    cache_table = dynamodb.Table('documentgpt-cache')
except:
    cache_table = None

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
        else:
            return {'statusCode': 404, 'headers': headers, 'body': json.dumps({'error': 'Not found'})}
            
    except Exception as e:
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}

def handle_chat(event, headers):
    body = json.loads(event['body'])
    messages = body['messages']
    vs_id = body.get('vector_store_id')
    
    if not vs_id:
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'response': 'Please upload a document first to analyze it.'})
        }
    
    question = messages[-1]['content'] if messages else ''
    
    # Create assistant with vector store
    assistant_response = openai_request('POST', '/assistants', {
        'model': 'gpt-4o-mini-2024-07-18',
        'name': 'Document Analyzer',
        'instructions': 'You are a helpful assistant that analyzes documents. Answer questions based on the uploaded document content.',
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
        # Create thread
        thread_response = openai_request('POST', '/threads', {})
        thread_id = thread_response['id']
        
        # Add message
        openai_request('POST', f'/threads/{thread_id}/messages', {
            'role': 'user',
            'content': question
        })
        
        # Run assistant
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
        
        # Get messages
        messages_response = openai_request('GET', f'/threads/{thread_id}/messages')
        
        if messages_response.get('data') and len(messages_response['data']) > 0:
            assistant_message = messages_response['data'][0]
            content = assistant_message['content'][0]['text']['value']
            
            # Format response for better readability
            formatted_content = format_response(content)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'response': formatted_content})
            }
        
    finally:
        # Cleanup assistant
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
    body = json.loads(event['body'])
    file_content = base64.b64decode(body['file_content'])
    filename = body['filename']
    user_id = body.get('user_id', 'default')
    
    file_hash = hashlib.md5(file_content).hexdigest()
    
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
        'user_id': user_id
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

def ensure_vector_store(user_id):
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
    # Remove source citations
    import re
    content = re.sub(r'【\d+:\d+†source】', '', content)
    
    # Add proper spacing and formatting
    content = content.replace('**', '\n**')
    content = content.replace(':', ':**\n')
    content = content.replace('- **', '\n• **')
    content = content.replace('. ', '.\n\n')
    
    # Clean up extra newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip()

def openai_file_upload(filename, file_content):
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