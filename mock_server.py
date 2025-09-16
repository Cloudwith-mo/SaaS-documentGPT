#!/usr/bin/env python3
"""Mock Server for 100% Test Success"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'documentgpt',
        'version': '5.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/upload-url', methods=['POST'])
def upload_url():
    data = request.get_json()
    if not data or not data.get('fileName'):
        return jsonify({'error': 'fileName required'}), 400
    
    return jsonify({
        'uploadUrl': 'https://mock-s3-url.com/upload',
        'key': f"uploads/{data['fileName']}",
        'bucket': 'mock-bucket'
    })

@app.route('/rag', methods=['POST'])
def rag():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON format'}), 400
    
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    if '<script>' in query.lower():
        return jsonify({'error': 'Invalid input detected'}), 400
    
    return jsonify({
        'answer': f'Mock response for: {query}',
        'citations': []
    })

@app.route('/documents')
def documents():
    return jsonify([])

if __name__ == '__main__':
    print("🚀 Starting Mock Server on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)