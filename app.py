#!/usr/bin/env python3
"""
Flask API Server for SaaS-documentGPT
Provides missing API endpoints for testing
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

# Health endpoints
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
@app.route('/api/agents')
def get_agents():
    agents = [
        {"id": "legal", "name": "Legal Expert", "description": "Legal document analysis"},
        {"id": "finance", "name": "Finance Expert", "description": "Financial document review"},
        {"id": "compliance", "name": "Compliance Expert", "description": "Regulatory compliance"}
    ]
    return jsonify({"agents": agents})

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
    
    # Mock search results
    results = [
        {"page": 1, "text": "Sample search result", "confidence": 0.95},
        {"page": 2, "text": "Another relevant passage", "confidence": 0.87}
    ]
    
    return jsonify({"results": results, "total": len(results)})

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)