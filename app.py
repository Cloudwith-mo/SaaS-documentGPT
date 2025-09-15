#!/usr/bin/env python3
"""
DocumentsGPT v5 Flask Server
Main server integrating all handlers and providing v5 API endpoints
"""

import os
import json
import uuid
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import threading
import queue

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Mock data stores (replace with real DB in production)
documents = {}
chat_sessions = {}
agent_presets = {
    "tax_expert": {
        "name": "Tax Expert",
        "description": "Specialized in tax document analysis",
        "model": "gpt-4",
        "temperature": 0.1
    },
    "legal_analyst": {
        "name": "Legal Analyst", 
        "description": "Expert in legal document review",
        "model": "gpt-4",
        "temperature": 0.2
    },
    "financial_advisor": {
        "name": "Financial Advisor",
        "description": "Financial document specialist",
        "model": "gpt-4",
        "temperature": 0.15
    }
}

# SSE connections
sse_connections = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "5.0.0",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/healthz', methods=['GET'])
def health_check_alt():
    """Alternative health check endpoint for tests"""
    return jsonify({
        "status": "ok",
        "version": "5.0.0",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/v5/health', methods=['GET'])
def api_health():
    """API health check"""
    return jsonify({
        "api_status": "operational",
        "features": {
            "document_upload": True,
            "pdf_search": True,
            "multi_agent_debate": True,
            "sse_streaming": True,
            "export": True
        }
    })

@app.route('/api/v5/agent-presets', methods=['GET'])
def get_agent_presets():
    """Get available agent presets"""
    return jsonify({"presets": agent_presets})

@app.route('/api/agents', methods=['GET', 'POST'])
def agents_api():
    """Agent presets CRUD API"""
    if request.method == 'GET':
        # Return list of presets
        presets_list = [
            {"name": "Legal/Finance/Compliance", "agents": ["Legal", "Finance", "Compliance"]},
            {"name": "Tech/Design/PM", "agents": ["Tech", "Design", "PM"]},
            {"name": "Sales/Marketing/Support", "agents": ["Sales", "Marketing", "Support"]}
        ]
        return jsonify(presets_list)
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'name' not in data or 'agents' not in data:
            return jsonify({"error": "Missing name or agents"}), 400
        
        # Mock creation
        return jsonify({"id": str(uuid.uuid4()), "created": True}), 201

@app.route('/api/v5/documents', methods=['POST'])
def upload_document():
    """Upload and process document"""
    try:
        data = request.get_json()
        
        doc_id = str(uuid.uuid4())
        doc_name = data.get('name', 'Untitled Document')
        
        # Mock document processing
        document = {
            "id": doc_id,
            "name": doc_name,
            "status": "processing",
            "uploaded_at": datetime.utcnow().isoformat(),
            "pages": data.get('pages', 1),
            "size": data.get('size', 0),
            "type": data.get('type', 'pdf')
        }
        
        documents[doc_id] = document
        
        # Simulate processing completion after 2 seconds
        def complete_processing():
            time.sleep(2)
            documents[doc_id]["status"] = "completed"
            documents[doc_id]["processed_at"] = datetime.utcnow().isoformat()
            
        threading.Thread(target=complete_processing).start()
        
        return jsonify({
            "success": True,
            "document": document
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v5/documents', methods=['GET'])
def list_documents():
    """List all documents"""
    return jsonify({
        "documents": list(documents.values())
    })

@app.route('/api/v5/documents/<doc_id>', methods=['GET'])
def get_document(doc_id):
    """Get specific document"""
    if doc_id not in documents:
        return jsonify({"error": "Document not found"}), 404
    
    return jsonify({"document": documents[doc_id]})

@app.route('/api/v5/documents/<doc_id>/search', methods=['POST'])
def search_document():
    """Search within document with bbox coordinates"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        # Mock search results with bbox coordinates
        results = [
            {
                "text": f"Found relevant content for: {query}",
                "page": 1,
                "bbox": [100, 200, 300, 250],  # x1, y1, x2, y2
                "confidence": 0.95
            },
            {
                "text": f"Additional context about: {query}",
                "page": 2, 
                "bbox": [150, 300, 400, 350],
                "confidence": 0.87
            }
        ]
        
        return jsonify({
            "query": query,
            "results": results,
            "total": len(results)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pdf/search', methods=['POST'])
def pdf_search():
    """PDF search with normalized bbox coordinates"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing query"}), 400
            
        query = data.get('query')
        doc_id = data.get('doc_id', 'test-doc')
        page = data.get('page', 1)
        
        # Mock search results with normalized bbox (0-1 range)
        matches = [
            {
                "text": f"Found: {query}",
                "page": page,
                "bbox": {"x": 0.25, "y": 0.30, "w": 0.40, "h": 0.08},
                "confidence": 0.95
            },
            {
                "text": f"Related to: {query}",
                "page": page,
                "bbox": {"x": 0.15, "y": 0.60, "w": 0.50, "h": 0.06},
                "confidence": 0.87
            }
        ]
        
        return jsonify({
            "doc_id": doc_id,
            "query": query,
            "matches": matches,
            "total": len(matches)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v5/chat', methods=['POST'])
def chat():
    """Chat with documents"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        doc_ids = data.get('document_ids', [])
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        # Initialize session if new
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                "id": session_id,
                "messages": [],
                "created_at": datetime.utcnow().isoformat()
            }
        
        # Add user message
        user_msg = {
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        chat_sessions[session_id]["messages"].append(user_msg)
        
        # Generate response
        response_text = f"Based on the documents {doc_ids}, here's my analysis of: {message}"
        
        assistant_msg = {
            "role": "assistant", 
            "content": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "citations": [
                {
                    "document_id": doc_ids[0] if doc_ids else "mock-doc",
                    "page": 1,
                    "text": "Relevant excerpt from document"
                }
            ] if doc_ids else []
        }
        chat_sessions[session_id]["messages"].append(assistant_msg)
        
        return jsonify({
            "response": assistant_msg,
            "session_id": session_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v5/multi-agent-debate', methods=['POST'])
def multi_agent_debate():
    """Start multi-agent debate"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        agents = data.get('agents', ['tax_expert', 'legal_analyst'])
        
        debate_id = str(uuid.uuid4())
        
        # Mock debate responses
        debate_responses = []
        for i, agent_id in enumerate(agents):
            agent = agent_presets.get(agent_id, agent_presets['tax_expert'])
            response = {
                "agent": agent_id,
                "agent_name": agent["name"],
                "response": f"{agent['name']} perspective on: {question}",
                "confidence": 0.9 - (i * 0.1),
                "timestamp": datetime.utcnow().isoformat()
            }
            debate_responses.append(response)
        
        # Generate consensus
        consensus = {
            "summary": f"Consensus analysis of: {question}",
            "confidence": 0.85,
            "key_points": [
                "Point 1 from debate",
                "Point 2 from debate", 
                "Point 3 from debate"
            ]
        }
        
        return jsonify({
            "debate_id": debate_id,
            "question": question,
            "agents": debate_responses,
            "consensus": consensus
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v5/stream/<session_id>')
def stream_events(session_id):
    """SSE streaming endpoint"""
    def event_stream():
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id})}\n\n"
        
        # Mock streaming events
        events = [
            {"type": "agent_thinking", "agent": "tax_expert", "message": "Analyzing document..."},
            {"type": "agent_response", "agent": "tax_expert", "message": "Found relevant tax information"},
            {"type": "debate_update", "message": "Agents reaching consensus..."},
            {"type": "complete", "message": "Analysis complete"}
        ]
        
        for event in events:
            time.sleep(1)  # Simulate processing time
            yield f"data: {json.dumps(event)}\n\n"
    
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/api/debate/stream', methods=['GET'])
def debate_stream():
    """SSE debate stream endpoint"""
    def event_stream():
        # Send debate events
        agents = ['Legal', 'Finance', 'Compliance']
        
        for i, agent in enumerate(agents):
            # Send argument event
            event_data = {
                "agent": agent,
                "argument": f"{agent} argument {i+1}",
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"event: debate.argument\ndata: {json.dumps(event_data)}\n\n"
            time.sleep(0.5)
        
        # Send consensus event
        consensus_data = {
            "consensus": "Final consensus reached",
            "confidence": 0.85,
            "timestamp": datetime.utcnow().isoformat()
        }
        yield f"event: debate.consensus\ndata: {json.dumps(consensus_data)}\n\n"
        
        # Send completion
        yield f"data: [DONE]\n\n"
    
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/api/v5/export', methods=['POST'])
def export_data():
    """Export chat or analysis data"""
    try:
        data = request.get_json()
        export_type = data.get('type', 'chat')  # chat, analysis, document
        session_id = data.get('session_id')
        format_type = data.get('format', 'json')  # json, pdf, docx
        
        if export_type == 'chat' and session_id:
            session = chat_sessions.get(session_id, {})
            export_data = {
                "type": "chat_export",
                "session_id": session_id,
                "messages": session.get("messages", []),
                "exported_at": datetime.utcnow().isoformat()
            }
        else:
            export_data = {
                "type": export_type,
                "data": "Mock export data",
                "exported_at": datetime.utcnow().isoformat()
            }
        
        return jsonify({
            "success": True,
            "export_id": str(uuid.uuid4()),
            "format": format_type,
            "data": export_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/debate/export', methods=['POST'])
def debate_export():
    """Export debate as markdown"""
    try:
        data = request.get_json()
        consensus = data.get('consensus', '')
        debate_cols = data.get('debate_cols', {})
        
        # Generate markdown content
        markdown_content = f"# Debate Export\n\n## Consensus\n{consensus}\n\n"
        
        for agent, arguments in debate_cols.items():
            markdown_content += f"## {agent} Arguments\n"
            for i, arg in enumerate(arguments, 1):
                markdown_content += f"{i}. {arg}\n"
            markdown_content += "\n"
        
        markdown_content += f"\n---\nExported at: {datetime.utcnow().isoformat()}"
        
        return Response(
            markdown_content,
            mimetype='text/markdown',
            headers={'Content-Disposition': 'attachment; filename=debate_export.md'}
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v5/concurrent-test', methods=['POST'])
def concurrent_test():
    """Test concurrent request handling"""
    try:
        data = request.get_json()
        request_id = data.get('request_id', str(uuid.uuid4()))
        
        # Simulate processing time
        time.sleep(0.5)
        
        return jsonify({
            "request_id": request_id,
            "processed_at": datetime.utcnow().isoformat(),
            "status": "completed"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v5/validate', methods=['POST'])
def validate_request():
    """Validate request data and security"""
    try:
        data = request.get_json()
        
        # Basic validation
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Check for required fields based on endpoint
        endpoint = data.get('endpoint')
        if endpoint == 'chat' and not data.get('message'):
            return jsonify({"error": "Message required for chat"}), 400
        
        return jsonify({
            "valid": True,
            "endpoint": endpoint,
            "validated_at": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting DocumentsGPT v5 server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)