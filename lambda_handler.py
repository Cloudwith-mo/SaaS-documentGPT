import json
import os
from datetime import datetime
import uuid
import boto3

def lambda_handler(event, context):
    """
    AWS Lambda handler for DocumentsGPT v5 with light theme UI
    """
    
    # Get request details
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Content-Type': 'text/html'
    }
    
    # Handle OPTIONS for CORS
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # Route handling
    if path == '/' or path == '/index.html':
        return serve_v5_ui()
    elif path == '/v2':
        return serve_v2_ui()
    elif path == '/health':
        return health_check()
    elif path.startswith('/api/'):
        return handle_api(event, context)
    else:
        return {
            'statusCode': 404,
            'headers': headers,
            'body': 'Not Found'
        }

def serve_v5_ui():
    """Serve v5 light theme UI"""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>DocumentsGPT v5</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50 min-h-screen">
    <div class="bg-white/80 backdrop-blur-sm border-b border-slate-200 p-4">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
                <span class="text-white font-bold">📄</span>
            </div>
            <div>
                <h1 class="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                    DocumentsGPT v5
                </h1>
                <p class="text-sm text-slate-500">Light Theme - Mint-Sky Gradients</p>
            </div>
        </div>
    </div>
    
    <div class="max-w-4xl mx-auto px-4 py-20 text-center">
        <div class="w-20 h-20 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <span class="text-white text-2xl">⚡</span>
        </div>
        <h2 class="text-4xl font-bold text-slate-800 mb-4">Welcome to v5</h2>
        <p class="text-xl text-slate-600 mb-8">Modern light interface with mint-sky gradients</p>
        
        <div class="bg-white/70 backdrop-blur-sm rounded-xl p-8 border border-slate-200">
            <h3 class="text-lg font-semibold text-slate-800 mb-4">✨ v5 Features</h3>
            <div class="grid grid-cols-2 gap-4 text-slate-600">
                <div>🤖 Multi-Agent Debates</div>
                <div>📄 PDF Search & Highlights</div>
                <div>🔄 Real-time Streaming</div>
                <div>💾 Export Capabilities</div>
            </div>
            <div class="mt-6 space-x-4">
                <a href="/v2" class="bg-gradient-to-r from-blue-500 to-cyan-500 text-white px-6 py-2 rounded-lg hover:from-blue-600 hover:to-cyan-600 transition-all">
                    Try v2 Interface
                </a>
                <a href="/api/v5/health" class="bg-slate-100 text-slate-700 px-6 py-2 rounded-lg hover:bg-slate-200 transition-all">
                    API Status
                </a>
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html',
            'Access-Control-Allow-Origin': '*'
        },
        'body': html
    }

def serve_v2_ui():
    """Serve v2 purple theme UI"""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>DocumentsGPT v2</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; margin: 0; padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        .header { 
            text-align: center; margin-bottom: 40px; color: white;
            background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        .card { 
            background: white; border-radius: 15px; padding: 30px; margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .btn { 
            background: #667eea; color: white; border: none; padding: 12px 24px; 
            border-radius: 8px; cursor: pointer; font-size: 16px; text-decoration: none;
            display: inline-block; margin: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 DocumentGPT v2</h1>
            <p>Purple Theme - Original Interface</p>
        </div>
        <div class="card">
            <h3>📄 Document Processing</h3>
            <p>Upload and analyze documents with AI</p>
            <a href="/" class="btn">Try v5 Light Theme</a>
        </div>
    </div>
</body>
</html>
    """
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html',
            'Access-Control-Allow-Origin': '*'
        },
        'body': html
    }

def health_check():
    """Health check endpoint"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'status': 'ok',
            'version': '5.0.0',
            'theme': 'light',
            'timestamp': datetime.utcnow().isoformat()
        })
    }

def handle_api(event, context):
    """Handle API requests"""
    path = event.get('path', '')
    
    if path == '/api/v5/health':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'api_status': 'operational',
                'theme': 'light_mint_sky',
                'features': {
                    'document_upload': True,
                    'pdf_search': True,
                    'multi_agent_debate': True,
                    'sse_streaming': True,
                    'export': True
                }
            })
        }
    
    # Default API response
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'DocumentsGPT v5 API',
            'path': path,
            'theme': 'light'
        })
    }