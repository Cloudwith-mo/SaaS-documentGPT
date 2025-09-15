import json
import boto3
import uuid
from datetime import datetime

def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    
    # Handle proxy path
    if '/v5/' in path:
        path = path.split('/v5/')[-1]
        path = '/' + path if not path.startswith('/') else path
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }
    
    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}
    
    try:
        if 'chat' in path and method == 'POST':
            return handle_chat(event, headers)
        elif 'debate' in path and method == 'GET':
            return handle_debate_stream(event, headers)
        elif 'search' in path and method == 'POST':
            return handle_search(event, headers)
        elif 'models' in path and method == 'GET':
            return handle_models(headers)
        elif 'presets' in path and method == 'GET':
            return handle_presets(headers)
        elif 'upload' in path and method == 'POST':
            return handle_upload(event, headers)
        elif 'documents' in path and method == 'GET':
            return handle_documents(headers)
        else:
            return {'statusCode': 404, 'headers': headers, 'body': json.dumps({'error': 'Not found'})}
    except Exception as e:
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}

def handle_chat(event, headers):
    body = json.loads(event.get('body', '{}'))
    message = body.get('message', '')
    model = body.get('model', 'gpt-5')
    
    response = {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "text": f"Based on documents using {model}: {message}",
        "citations": [{
            "docId": "sample",
            "page": 1,
            "quote": "Relevant excerpt...",
            "bbox": {"x": 0.26, "y": 0.28, "w": 0.42, "h": 0.08}
        }],
        "timestamp": datetime.now().isoformat()
    }
    
    return {'statusCode': 200, 'headers': headers, 'body': json.dumps(response)}

def handle_debate_stream(event, headers):
    # For SSE, return initial response and use separate WebSocket/polling
    return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'status': 'debate started'})}

def handle_search(event, headers):
    body = json.loads(event.get('body', '{}'))
    query = body.get('query', '')
    
    results = [{
        "docId": "sample",
        "page": 1,
        "text": f"Found: '{query}' in document",
        "bbox": {"x": 0.25, "y": 0.30, "w": 0.40, "h": 0.08},
        "confidence": 0.95
    }]
    
    return {'statusCode': 200, 'headers': headers, 'body': json.dumps({"results": results})}

def handle_models(headers):
    models = [
        {"id": "gpt-5", "name": "GPT-5 (Quality)"},
        {"id": "gpt-5-turbo", "name": "GPT-5-Turbo (Fast)"},
        {"id": "gpt-4.1-mini", "name": "GPT-4.1-mini (Economy)"}
    ]
    return {'statusCode': 200, 'headers': headers, 'body': json.dumps({"models": models})}

def handle_presets(headers):
    presets = {
        "legal_finance_compliance": {
            "name": "Legal/Finance/Compliance",
            "agents": ["Legal", "Finance", "Compliance"]
        },
        "tech_design_pm": {
            "name": "Tech/Design/PM",
            "agents": ["Tech", "Design", "PM"]
        }
    }
    return {'statusCode': 200, 'headers': headers, 'body': json.dumps({"presets": presets})}

def handle_upload(event, headers):
    # Simulate file upload
    doc_id = str(uuid.uuid4())
    doc = {
        "id": doc_id,
        "name": "uploaded_document.pdf",
        "pages": 3,
        "status": "completed",
        "uploadedAt": datetime.now().isoformat()
    }
    return {'statusCode': 200, 'headers': headers, 'body': json.dumps({"success": True, "document": doc})}

def handle_documents(headers):
    docs = [
        {"id": "sample", "name": "Sample.pdf", "pages": 3, "status": "completed"},
        {"id": "doc1", "name": "Contract.pdf", "pages": 5, "status": "completed"}
    ]
    return {'statusCode': 200, 'headers': headers, 'body': json.dumps({"documents": docs})}