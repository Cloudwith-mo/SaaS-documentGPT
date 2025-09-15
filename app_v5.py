from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import json
import time
import threading
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Sample data
DOCS = [
    {"id": "sample", "name": "Sample.pdf", "pages": 3, "url": "/sample.pdf"},
    {"id": "d1", "name": "MSA_v12.pdf", "pages": 42, "url": "/api/files/d1"},
    {"id": "d2", "name": "Vendor_NDA.pdf", "pages": 7, "url": "/api/files/d2"},
    {"id": "d3", "name": "Q3_Report.pdf", "pages": 18, "url": "/api/files/d3"},
]

AGENT_PRESETS = {
    "legal_finance_compliance": {
        "name": "Legal/Finance/Compliance",
        "agents": ["Legal", "Finance", "Compliance"]
    },
    "tech_design_pm": {
        "name": "Tech/Design/PM", 
        "agents": ["Tech", "Design", "PM"]
    }
}

# Global debate state
debate_sessions = {}

@app.route('/')
def index():
    return render_template('documentsgpt_v5.html')

@app.route('/api/documents')
def get_documents():
    return jsonify({"documents": DOCS})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    selected_docs = data.get('selectedDocs', [])
    model = data.get('model', 'gpt-5')
    
    # Simulate AI response
    response = {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "text": f"Based on {len(selected_docs)} documents using {model}: {message}",
        "citations": [
            {
                "docId": selected_docs[0] if selected_docs else "sample",
                "page": 1,
                "quote": "Relevant excerpt from document...",
                "bbox": {"x": 0.26, "y": 0.28, "w": 0.42, "h": 0.08}
            }
        ] if selected_docs else [],
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(response)

@app.route('/api/debate/stream')
def debate_stream():
    def generate():
        session_id = str(uuid.uuid4())
        agents = ["Legal", "Finance", "Compliance"]
        
        # Send initial event
        yield f"data: {json.dumps({'type': 'start', 'session': session_id})}\n\n"
        
        # Simulate debate arguments
        arguments = {
            "Legal": [
                "Contract terms require 30-day notice period",
                "Liability caps are standard at $1M",
                "Termination clauses favor the vendor"
            ],
            "Finance": [
                "Payment terms are NET-30 with 2% early discount",
                "Budget allocation exceeds Q3 projections by 15%",
                "Cost structure includes hidden fees"
            ],
            "Compliance": [
                "Data retention policies meet GDPR requirements",
                "Security standards align with SOC2 Type II",
                "Audit trail documentation is incomplete"
            ]
        }
        
        for agent in agents:
            for i, arg in enumerate(arguments[agent]):
                time.sleep(2)  # Simulate thinking time
                event_data = {
                    "agent": agent,
                    "text": arg,
                    "timestamp": datetime.now().isoformat()
                }
                yield f"event: debate.argument\n"
                yield f"data: {json.dumps(event_data)}\n\n"
        
        # Send consensus
        time.sleep(1)
        consensus_data = {
            "text": "All agents agree: Contract requires legal review for liability terms and payment schedule optimization.",
            "confidence": 0.87,
            "timestamp": datetime.now().isoformat()
        }
        yield f"event: debate.consensus\n"
        yield f"data: {json.dumps(consensus_data)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache',
                           'Connection': 'keep-alive'})

@app.route('/api/search', methods=['POST'])
def search_documents():
    data = request.json
    query = data.get('query', '')
    doc_id = data.get('docId', 'sample')
    
    # Simulate search results
    results = [
        {
            "docId": doc_id,
            "page": 1,
            "text": f"Found: '{query}' in document context...",
            "bbox": {"x": 0.25, "y": 0.30, "w": 0.40, "h": 0.08},
            "confidence": 0.95
        }
    ]
    
    return jsonify({"results": results})

@app.route('/api/presets')
def get_presets():
    return jsonify({"presets": AGENT_PRESETS})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Simulate file processing
    doc_id = str(uuid.uuid4())
    new_doc = {
        "id": doc_id,
        "name": file.filename,
        "pages": 1,
        "url": f"/api/files/{doc_id}",
        "status": "completed",
        "uploadedAt": datetime.now().isoformat()
    }
    
    DOCS.append(new_doc)
    return jsonify({"success": True, "document": new_doc})

@app.route('/api/models')
def get_models():
    models = [
        {"id": "gpt-5", "name": "GPT-5 (Quality)", "description": "Latest and most capable"},
        {"id": "gpt-5-turbo", "name": "GPT-5-Turbo (Fast)", "description": "Optimized for speed"},
        {"id": "gpt-4.1-mini", "name": "GPT-4.1-mini (Economy)", "description": "Cost-effective option"}
    ]
    return jsonify({"models": models})

@app.route('/api/files/<doc_id>')
def get_file(doc_id):
    # Serve file content (placeholder)
    return jsonify({"content": "File content placeholder"})

if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)