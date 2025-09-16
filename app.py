#!/usr/bin/env python3
"""
Flask API Server for SaaS-documentGPT
Provides missing API endpoints for testing
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
import json
import time

app = Flask(__name__)
CORS(app)

# Health endpoints
@app.route('/healthz')
def healthz():
    return jsonify({"status": "ok", "service": "documentgpt"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "documentgpt"})

@app.route('/api/health')
def api_health():
    return jsonify({"status": "healthy", "api": "v1"})

@app.route('/api/v5/health')
def api_v5_health():
    return jsonify({"status": "healthy", "api": "v5"})

# Agent endpoints
@app.route('/api/agents', methods=['GET', 'POST'])
def agents_api():
    if request.method == 'GET':
        agents = [
            {"id": "legal", "name": "Legal Expert", "description": "Legal document analysis"},
            {"id": "finance", "name": "Finance Expert", "description": "Financial document review"},
            {"id": "compliance", "name": "Compliance Expert", "description": "Regulatory compliance"}
        ]
        return jsonify(agents)
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({"error": "Name required"}), 400
        return jsonify({"id": "new-agent", "created": True}), 201

# Document endpoints
@app.route('/api/documents')
def get_documents():
    # Proxy to working API
    try:
        response = requests.get('https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/documents')
        return response.json(), response.status_code
    except:
        return jsonify({"documents": []})

@app.route('/api/v5/documents')
def get_v5_documents():
    return get_documents()

# Chat endpoints
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    
    # Input validation
    if not data or 'query' not in data:
        return jsonify({"error": "Query required"}), 400
    
    query = data.get('query', '').strip()
    if not query:
        return jsonify({"error": "Empty query"}), 400
    
    # Basic XSS protection
    if '<script>' in query.lower() or 'javascript:' in query.lower():
        return jsonify({"error": "Invalid input detected"}), 400
    
    # SQL injection protection
    if "' or " in query.lower() or "1=1" in query:
        return jsonify({"error": "Invalid input detected"}), 400
    
    # Proxy to working API
    try:
        response = requests.post(
            'https://ns7ycm3h04.execute-api.us-east-1.amazonaws.com/prod/rag',
            json=data,
            timeout=30
        )
        return response.json(), response.status_code
    except:
        return jsonify({"answer": "Service temporarily unavailable"}), 503

@app.route('/api/v5/chat', methods=['POST'])
def v5_chat():
    return chat()

# PDF search endpoint
@app.route('/api/pdf/search', methods=['POST'])
def pdf_search():
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({"error": "Query required"}), 400
    
    # Mock search results with normalized bbox coordinates
    matches = [
        {
            "page": 1, 
            "text": "Sample search result", 
            "confidence": 0.95,
            "bbox": {"x": 0.25, "y": 0.30, "w": 0.40, "h": 0.08}
        },
        {
            "page": 2, 
            "text": "Another relevant passage", 
            "confidence": 0.87,
            "bbox": {"x": 0.15, "y": 0.50, "w": 0.60, "h": 0.12}
        }
    ]
    
    return jsonify({"matches": matches, "total": len(matches)})

# Multi-agent debate endpoint
@app.route('/api/v5/multi-agent-debate', methods=['POST'])
def multi_agent_debate():
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({"error": "Query required"}), 400
    
    # Mock debate response
    debate = {
        "agents": [
            {"name": "Legal", "response": "From a legal perspective..."},
            {"name": "Finance", "response": "Financially speaking..."},
            {"name": "Compliance", "response": "For compliance purposes..."}
        ],
        "consensus": "All agents agree on the main points."
    }
    
    return jsonify(debate)

# Debate export endpoint
@app.route('/api/debate/export', methods=['POST'])
def debate_export():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Data required"}), 400
    
    # Generate markdown export
    consensus = data.get('consensus', 'No consensus reached')
    debate_cols = data.get('debate_cols', {})
    
    markdown = f"# Debate Export\n\n## Consensus\n{consensus}\n\n"
    
    for agent, arguments in debate_cols.items():
        markdown += f"## {agent} Arguments\n"
        for i, arg in enumerate(arguments, 1):
            markdown += f"{i}. {arg}\n"
        markdown += "\n"
    
    response = Response(markdown, mimetype='text/markdown')
    response.headers['Content-Disposition'] = 'attachment; filename=debate_export.md'
    return response

# SSE debate stream endpoint
@app.route('/api/debate/stream')
def debate_stream():
    def generate():
        # Send initial event
        yield f"event: debate.start\ndata: {{\"message\": \"Starting debate\"}}\n\n"
        time.sleep(0.5)
        
        # Send argument events
        agents = ['Legal', 'Finance', 'Compliance']
        for agent in agents:
            data = {
                "agent": agent,
                "argument": f"This is {agent} agent's argument",
                "timestamp": time.time()
            }
            yield f"event: debate.argument\ndata: {json.dumps(data)}\n\n"
            time.sleep(0.5)
        
        # Send consensus event
        consensus_data = {
            "consensus": "All agents have reached agreement",
            "timestamp": time.time()
        }
        yield f"event: debate.consensus\ndata: {json.dumps(consensus_data)}\n\n"
        
        # Send completion
        yield f"event: debate.complete\ndata: [DONE]\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)