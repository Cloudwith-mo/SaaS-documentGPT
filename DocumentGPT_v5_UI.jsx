import React, { useState, useEffect, useRef } from 'react';
import { Upload, MessageSquare, FileText, Settings, Download, Users, Zap, Eye, Search } from 'lucide-react';

const DocumentGPTv5 = () => {
  // State management
  const [documents, setDocuments] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [agentMode, setAgentMode] = useState('guided'); // guided, autonomous
  const [selectedModel, setSelectedModel] = useState('gpt-5-turbo');
  const [selectedPreset, setSelectedPreset] = useState('');
  const [debateActive, setDebateActive] = useState(false);
  const [debateResults, setDebateResults] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [highlights, setHighlights] = useState([]);
  
  // Refs
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const eventSourceRef = useRef(null);

  // Agent presets
  const agentPresets = {
    'tax_analysis': {
      name: 'Tax Analysis',
      agents: ['Tax Expert', 'Compliance Officer', 'Financial Advisor'],
      description: 'Specialized team for tax document analysis'
    },
    'legal_review': {
      name: 'Legal Review', 
      agents: ['Legal Analyst', 'Contract Specialist', 'Risk Assessor'],
      description: 'Expert legal document review team'
    },
    'financial_audit': {
      name: 'Financial Audit',
      agents: ['Auditor', 'Financial Analyst', 'Compliance Expert'],
      description: 'Comprehensive financial document analysis'
    }
  };

  // Models available
  const models = [
    { id: 'gpt-5-turbo', name: 'GPT-5 Turbo', description: 'Latest and most capable' },
    { id: 'gpt-4', name: 'GPT-4', description: 'Reliable and accurate' },
    { id: 'claude-3', name: 'Claude 3', description: 'Excellent for analysis' }
  ];

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Handle file upload
  const handleFileUpload = async (files) => {
    const fileArray = Array.from(files);
    
    for (const file of fileArray) {
      const docId = `doc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Add document to state
      const newDoc = {
        id: docId,
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'uploading',
        pages: Math.ceil(file.size / 50000), // Estimate pages
        uploadedAt: new Date().toISOString()
      };
      
      setDocuments(prev => [...prev, newDoc]);
      
      try {
        // Simulate upload and processing
        await simulateUpload(docId, file);
        
        // Update status to completed
        setDocuments(prev => prev.map(doc => 
          doc.id === docId ? { ...doc, status: 'completed' } : doc
        ));
        
      } catch (error) {
        setDocuments(prev => prev.map(doc => 
          doc.id === docId ? { ...doc, status: 'error', error: error.message } : doc
        ));
      }
    }
  };

  const simulateUpload = async (docId, file) => {
    // Simulate upload progress
    const steps = ['uploading', 'processing', 'extracting', 'indexing'];
    
    for (const step of steps) {
      setDocuments(prev => prev.map(doc => 
        doc.id === docId ? { ...doc, status: step } : doc
      ));
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  };

  // Handle chat message
  const handleSendMessage = async () => {
    if (!currentMessage.trim() || selectedDocs.length === 0) return;
    
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: currentMessage,
      timestamp: new Date().toISOString()
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsLoading(true);
    
    try {
      // Simulate AI response
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Based on the selected documents (${selectedDocs.length} files), here's my analysis: ${currentMessage}`,
        timestamp: new Date().toISOString(),
        citations: selectedDocs.slice(0, 2).map(docId => ({
          docId,
          docName: documents.find(d => d.id === docId)?.name || 'Unknown',
          page: 1,
          text: 'Relevant excerpt from document...'
        }))
      };
      
      setChatMessages(prev => [...prev, aiMessage]);
      
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Start multi-agent debate
  const startDebate = async () => {
    if (!selectedPreset || selectedDocs.length === 0) return;
    
    setDebateActive(true);
    setIsLoading(true);
    
    try {
      // Setup SSE connection for real-time debate
      const eventSource = new EventSource(`/api/v5/stream/debate_${Date.now()}`);
      eventSourceRef.current = eventSource;
      
      const agents = agentPresets[selectedPreset].agents;
      const debateData = {
        question: currentMessage || "Analyze the uploaded documents",
        agents: agents,
        documents: selectedDocs
      };
      
      // Simulate debate results
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      const mockResults = {
        question: debateData.question,
        agents: agents.map((agent, i) => ({
          name: agent,
          response: `${agent} analysis: This is a detailed perspective from ${agent} regarding the documents.`,
          confidence: 0.9 - (i * 0.1),
          timestamp: new Date().toISOString()
        })),
        consensus: {
          summary: "The agents have reached a consensus on the document analysis.",
          confidence: 0.85,
          keyPoints: [
            "Key finding 1 from the debate",
            "Key finding 2 from the debate", 
            "Key finding 3 from the debate"
          ]
        }
      };
      
      setDebateResults(mockResults);
      
    } catch (error) {
      console.error('Debate error:', error);
    } finally {
      setDebateActive(false);
      setIsLoading(false);
    }
  };

  // Search within documents
  const handleSearch = async () => {
    if (!searchQuery.trim() || selectedDocs.length === 0) return;
    
    try {
      // Simulate search results with bbox coordinates
      const mockResults = [
        {
          docId: selectedDocs[0],
          docName: documents.find(d => d.id === selectedDocs[0])?.name || 'Document',
          page: 1,
          text: `Found: "${searchQuery}" in document context...`,
          bbox: { x: 0.25, y: 0.30, w: 0.40, h: 0.08 },
          confidence: 0.95
        },
        {
          docId: selectedDocs[0],
          docName: documents.find(d => d.id === selectedDocs[0])?.name || 'Document',
          page: 2,
          text: `Related to: "${searchQuery}" - additional context...`,
          bbox: { x: 0.15, y: 0.60, w: 0.50, h: 0.06 },
          confidence: 0.87
        }
      ];
      
      setSearchResults(mockResults);
      
      // Update highlights for PDF viewer
      const newHighlights = mockResults.map(result => ({
        page: result.page,
        bbox: result.bbox,
        text: result.text
      }));
      setHighlights(newHighlights);
      
    } catch (error) {
      console.error('Search error:', error);
    }
  };

  // Export functionality
  const handleExport = async (format = 'json') => {
    try {
      const exportData = {
        type: debateResults ? 'debate' : 'chat',
        data: debateResults || { messages: chatMessages },
        documents: selectedDocs.map(id => documents.find(d => d.id === id)),
        exportedAt: new Date().toISOString()
      };
      
      // Create and download file
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `documentgpt_export_${Date.now()}.${format}`;\n      document.body.appendChild(a);\n      a.click();\n      document.body.removeChild(a);\n      URL.revokeObjectURL(url);\n      \n    } catch (error) {\n      console.error('Export error:', error);\n    }\n  };\n\n  return (\n    <div className=\"min-h-screen\" style={{background: 'linear-gradient(135deg, #f0fdfa 0%, #e6fffa 50%, #ccfbf1 100%)'}}>\n      {/* Header */}\n      <div className=\"bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-50\">\n        <div className=\"max-w-7xl mx-auto px-4 py-4\">\n          <div className=\"flex items-center justify-between\">\n            <div className=\"flex items-center space-x-3\">\n              <div className=\"w-10 h-10 bg-gradient-to-r from-teal-500 to-emerald-500 rounded-xl flex items-center justify-center\">\n                <FileText className=\"w-6 h-6 text-white\" />\n              </div>\n              <div>\n                <h1 className=\"text-2xl font-bold bg-gradient-to-r from-teal-800 to-emerald-600 bg-clip-text text-transparent\">\n                  DocumentsGPT v5\n                </h1>\n                <p className=\"text-sm text-slate-500\">AI-Powered Document Analysis Platform</p>\n              </div>\n            </div>\n            \n            <div className=\"flex items-center space-x-4\">\n              {/* Model Selector */}\n              <select \n                value={selectedModel} \n                onChange={(e) => setSelectedModel(e.target.value)}\n                className=\"px-3 py-2 bg-white border border-teal-200 rounded-lg text-sm focus:ring-2 focus:ring-teal-500 focus:border-transparent\"\n              >\n                {models.map(model => (\n                  <option key={model.id} value={model.id}>{model.name}</option>\n                ))}\n              </select>\n              \n              {/* Agent Mode Toggle */}\n              <div className=\"flex bg-slate-100 rounded-lg p-1\">\n                <button\n                  onClick={() => setAgentMode('guided')}\n                  className={`px-3 py-1 text-sm rounded-md transition-all ${\n                    agentMode === 'guided' \n                      ? 'bg-white text-slate-800 shadow-sm' \n                      : 'text-slate-600 hover:text-slate-800'\n                  }`}\n                >\n                  Guided\n                </button>\n                <button\n                  onClick={() => setAgentMode('autonomous')}\n                  className={`px-3 py-1 text-sm rounded-md transition-all ${\n                    agentMode === 'autonomous' \n                      ? 'bg-white text-slate-800 shadow-sm' \n                      : 'text-slate-600 hover:text-slate-800'\n                  }`}\n                >\n                  Auto\n                </button>\n              </div>\n            </div>\n          </div>\n        </div>\n      </div>\n\n      <div className=\"max-w-7xl mx-auto px-4 py-6\">\n        <div className=\"grid grid-cols-12 gap-6 h-[calc(100vh-140px)]\">\n          \n          {/* Sidebar */}\n          <div className=\"col-span-3 space-y-4\">\n            \n            {/* Upload Area */}\n            <div className=\"bg-white/70 backdrop-blur-sm rounded-xl p-6 border border-slate-200\">\n              <h3 className=\"font-semibold text-slate-800 mb-4 flex items-center\">\n                <Upload className=\"w-5 h-5 mr-2 text-teal-500\" />\n                Upload Documents\n              </h3>\n              \n              <div \n                className=\"border-2 border-dashed border-teal-300 rounded-lg p-6 text-center hover:border-teal-400 transition-colors cursor-pointer\"\n                onClick={() => fileInputRef.current?.click()}\n                onDragOver={(e) => e.preventDefault()}\n                onDrop={(e) => {\n                  e.preventDefault();\n                  handleFileUpload(e.dataTransfer.files);\n                }}\n              >\n                <Upload className=\"w-8 h-8 text-slate-400 mx-auto mb-2\" />\n                <p className=\"text-sm text-slate-600\">Drop files or click to upload</p>\n                <p className=\"text-xs text-slate-400 mt-1\">PDF, DOCX, TXT supported</p>\n              </div>\n              \n              <input\n                ref={fileInputRef}\n                type=\"file\"\n                multiple\n                accept=\".pdf,.docx,.txt\"\n                onChange={(e) => handleFileUpload(e.target.files)}\n                className=\"hidden\"\n              />\n            </div>\n            \n            {/* Document List */}\n            <div className=\"bg-white/70 backdrop-blur-sm rounded-xl p-6 border border-slate-200 flex-1\">\n              <h3 className=\"font-semibold text-slate-800 mb-4 flex items-center\">\n                <FileText className=\"w-5 h-5 mr-2 text-green-500\" />\n                Documents ({documents.length})\n              </h3>\n              \n              <div className=\"space-y-2 max-h-64 overflow-y-auto\">\n                {documents.map(doc => (\n                  <div key={doc.id} className=\"flex items-center space-x-3 p-2 rounded-lg hover:bg-slate-50\">\n                    <input\n                      type=\"checkbox\"\n                      checked={selectedDocs.includes(doc.id)}\n                      onChange={(e) => {\n                        if (e.target.checked) {\n                          setSelectedDocs(prev => [...prev, doc.id]);\n                        } else {\n                          setSelectedDocs(prev => prev.filter(id => id !== doc.id));\n                        }\n                      }}\n                      className=\"rounded border-slate-300 text-teal-500 focus:ring-teal-500\"\n                    />\n                    <div className=\"flex-1 min-w-0\">\n                      <p className=\"text-sm font-medium text-slate-800 truncate\">{doc.name}</p>\n                      <div className=\"flex items-center space-x-2\">\n                        <span className={`inline-block w-2 h-2 rounded-full ${\n                          doc.status === 'completed' ? 'bg-green-400' :\n                          doc.status === 'error' ? 'bg-red-400' : 'bg-yellow-400'\n                        }`} />\n                        <span className=\"text-xs text-slate-500 capitalize\">{doc.status}</span>\n                      </div>\n                    </div>\n                  </div>\n                ))}\n                \n                {documents.length === 0 && (\n                  <p className=\"text-sm text-slate-500 text-center py-8\">No documents uploaded yet</p>\n                )}\n              </div>\n            </div>\n            \n            {/* Agent Presets */}\n            <div className=\"bg-white/70 backdrop-blur-sm rounded-xl p-6 border border-slate-200\">\n              <h3 className=\"font-semibold text-slate-800 mb-4 flex items-center\">\n                <Users className=\"w-5 h-5 mr-2 text-purple-500\" />\n                Agent Presets\n              </h3>\n              \n              <select\n                value={selectedPreset}\n                onChange={(e) => setSelectedPreset(e.target.value)}\n                className=\"w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-teal-500 focus:border-transparent\"\n              >\n                <option value=\"\">Select preset...</option>\n                {Object.entries(agentPresets).map(([key, preset]) => (\n                  <option key={key} value={key}>{preset.name}</option>\n                ))}\n              </select>\n              \n              {selectedPreset && (\n                <div className=\"mt-3 p-3 bg-slate-50 rounded-lg\">\n                  <p className=\"text-xs text-slate-600 mb-2\">{agentPresets[selectedPreset].description}</p>\n                  <div className=\"flex flex-wrap gap-1\">\n                    {agentPresets[selectedPreset].agents.map(agent => (\n                      <span key={agent} className=\"inline-block px-2 py-1 bg-teal-100 text-teal-700 text-xs rounded\">\n                        {agent}\n                      </span>\n                    ))}\n                  </div>\n                </div>\n              )}\n              \n              <button\n                onClick={startDebate}\n                disabled={!selectedPreset || selectedDocs.length === 0 || debateActive}\n                className=\"w-full mt-3 px-4 py-2 bg-gradient-to-r from-teal-500 to-emerald-500 text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:from-teal-600 hover:to-emerald-600 transition-all\"\n              >\n                {debateActive ? (\n                  <div className=\"flex items-center justify-center\">\n                    <div className=\"animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2\" />\n                    Debating...\n                  </div>\n                ) : (\n                  'Start Multi-Agent Debate'\n                )}\n              </button>\n            </div>\n          </div>\n          \n          {/* PDF Viewer */}\n          <div className=\"col-span-5\">\n            <div className=\"bg-white/70 backdrop-blur-sm rounded-xl border border-slate-200 h-full flex flex-col\">\n              <div className=\"p-4 border-b border-slate-200\">\n                <div className=\"flex items-center justify-between mb-4\">\n                  <h3 className=\"font-semibold text-slate-800 flex items-center\">\n                    <Eye className=\"w-5 h-5 mr-2 text-indigo-500\" />\n                    Document Viewer\n                  </h3>\n                  \n                  <div className=\"flex items-center space-x-2\">\n                    <button className=\"px-3 py-1 text-sm bg-slate-100 hover:bg-slate-200 rounded-md transition-colors\">\n                      Page {currentPage}\n                    </button>\n                    <button \n                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}\n                      className=\"px-2 py-1 text-sm bg-slate-100 hover:bg-slate-200 rounded-md transition-colors\"\n                    >\n                      ←\n                    </button>\n                    <button \n                      onClick={() => setCurrentPage(currentPage + 1)}\n                      className=\"px-2 py-1 text-sm bg-slate-100 hover:bg-slate-200 rounded-md transition-colors\"\n                    >\n                      →\n                    </button>\n                  </div>\n                </div>\n                \n                {/* Search Bar */}\n                <div className=\"flex space-x-2\">\n                  <div className=\"flex-1 relative\">\n                    <Search className=\"absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400\" />\n                    <input\n                      type=\"text\"\n                      value={searchQuery}\n                      onChange={(e) => setSearchQuery(e.target.value)}\n                      placeholder=\"Search in documents...\"\n                      className=\"w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-teal-500 focus:border-transparent\"\n                      onKeyPress={(e) => e.key === 'Enter' && handleSearch()}\n                    />\n                  </div>\n                  <button\n                    onClick={handleSearch}\n                    className=\"px-4 py-2 bg-teal-500 text-white rounded-lg text-sm hover:bg-teal-600 transition-colors\"\n                  >\n                    Search\n                  </button>\n                </div>\n              </div>\n              \n              {/* PDF Content Area */}\n              <div className=\"flex-1 p-4\">\n                {selectedDocs.length > 0 ? (\n                  <div className=\"h-full bg-slate-50 rounded-lg border-2 border-dashed border-slate-300 flex items-center justify-center relative\">\n                    <div className=\"text-center\">\n                      <FileText className=\"w-16 h-16 text-slate-400 mx-auto mb-4\" />\n                      <p className=\"text-slate-600 font-medium\">PDF Viewer</p>\n                      <p className=\"text-sm text-slate-500\">Document: {documents.find(d => d.id === selectedDocs[0])?.name}</p>\n                      <p className=\"text-xs text-slate-400 mt-2\">Page {currentPage} • {highlights.length} highlights</p>\n                    </div>\n                    \n                    {/* Search Highlights Overlay */}\n                    {highlights.map((highlight, index) => (\n                      highlight.page === currentPage && (\n                        <div\n                          key={index}\n                          className=\"absolute bg-yellow-200 bg-opacity-50 border border-yellow-400 rounded\"\n                          style={{\n                            left: `${highlight.bbox.x * 100}%`,\n                            top: `${highlight.bbox.y * 100}%`,\n                            width: `${highlight.bbox.w * 100}%`,\n                            height: `${highlight.bbox.h * 100}%`\n                          }}\n                          title={highlight.text}\n                        />\n                      )\n                    ))}\n                  </div>\n                ) : (\n                  <div className=\"h-full bg-slate-50 rounded-lg border-2 border-dashed border-slate-300 flex items-center justify-center\">\n                    <div className=\"text-center\">\n                      <FileText className=\"w-16 h-16 text-slate-400 mx-auto mb-4\" />\n                      <p className=\"text-slate-600\">Select documents to view</p>\n                    </div>\n                  </div>\n                )}\n              </div>\n            </div>\n          </div>\n          \n          {/* Chat Panel */}\n          <div className=\"col-span-4\">\n            <div className=\"bg-white/70 backdrop-blur-sm rounded-xl border border-slate-200 h-full flex flex-col\">\n              <div className=\"p-4 border-b border-slate-200\">\n                <div className=\"flex items-center justify-between\">\n                  <h3 className=\"font-semibold text-slate-800 flex items-center\">\n                    <MessageSquare className=\"w-5 h-5 mr-2 text-emerald-500\" />\n                    AI Assistant\n                  </h3>\n                  \n                  <div className=\"flex items-center space-x-2\">\n                    <button\n                      onClick={() => handleExport('json')}\n                      className=\"p-2 text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors\"\n                      title=\"Export conversation\"\n                    >\n                      <Download className=\"w-4 h-4\" />\n                    </button>\n                    <button className=\"p-2 text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors\">\n                      <Settings className=\"w-4 h-4\" />\n                    </button>\n                  </div>\n                </div>\n                \n                {selectedDocs.length > 0 && (\n                  <div className=\"mt-2 flex items-center text-xs text-slate-500\">\n                    <Zap className=\"w-3 h-3 mr-1\" />\n                    Analyzing {selectedDocs.length} document{selectedDocs.length !== 1 ? 's' : ''} • {selectedModel}\n                  </div>\n                )}\n              </div>\n              \n              {/* Messages */}\n              <div className=\"flex-1 overflow-y-auto p-4 space-y-4\">\n                {chatMessages.length === 0 && (\n                  <div className=\"text-center py-8\">\n                    <MessageSquare className=\"w-12 h-12 text-slate-300 mx-auto mb-4\" />\n                    <p className=\"text-slate-500\">Start a conversation about your documents</p>\n                    <p className=\"text-xs text-slate-400 mt-2\">Upload documents and ask questions to get started</p>\n                  </div>\n                )}\n                \n                {chatMessages.map(message => (\n                  <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>\n                    <div className={`max-w-[80%] rounded-xl px-4 py-3 ${\n                      message.role === 'user' \n                        ? 'bg-gradient-to-r from-teal-500 to-emerald-500 text-white' \n                        : 'bg-slate-100 text-slate-800'\n                    }`}>\n                      <p className=\"text-sm\">{message.content}</p>\n                      \n                      {message.citations && message.citations.length > 0 && (\n                        <div className=\"mt-2 pt-2 border-t border-slate-200\">\n                          <p className=\"text-xs text-slate-600 mb-1\">Sources:</p>\n                          {message.citations.map((citation, index) => (\n                            <div key={index} className=\"text-xs text-slate-500\">\n                              📄 {citation.docName} (Page {citation.page})\n                            </div>\n                          ))}\n                        </div>\n                      )}\n                      \n                      <p className=\"text-xs opacity-70 mt-1\">\n                        {new Date(message.timestamp).toLocaleTimeString()}\n                      </p>\n                    </div>\n                  </div>\n                ))}\n                \n                {isLoading && (\n                  <div className=\"flex justify-start\">\n                    <div className=\"bg-slate-100 rounded-xl px-4 py-3\">\n                      <div className=\"flex items-center space-x-2\">\n                        <div className=\"animate-spin w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full\" />\n                        <span className=\"text-sm text-slate-600\">Thinking...</span>\n                      </div>\n                    </div>\n                  </div>\n                )}\n                \n                <div ref={chatEndRef} />\n              </div>\n              \n              {/* Debate Results */}\n              {debateResults && (\n                <div className=\"p-4 border-t border-slate-200 bg-gradient-to-r from-purple-50 to-pink-50\">\n                  <h4 className=\"font-semibold text-slate-800 mb-2 flex items-center\">\n                    <Users className=\"w-4 h-4 mr-2 text-purple-500\" />\n                    Multi-Agent Consensus\n                  </h4>\n                  \n                  <div className=\"space-y-2\">\n                    <div className=\"text-sm text-slate-700\">\n                      <strong>Consensus:</strong> {debateResults.consensus.summary}\n                    </div>\n                    \n                    <div className=\"text-xs text-slate-600\">\n                      <strong>Confidence:</strong> {(debateResults.consensus.confidence * 100).toFixed(1)}%\n                    </div>\n                    \n                    <div className=\"text-xs text-slate-600\">\n                      <strong>Agents:</strong> {debateResults.agents.map(a => a.name).join(', ')}\n                    </div>\n                  </div>\n                  \n                  <button\n                    onClick={() => handleExport('md')}\n                    className=\"mt-2 px-3 py-1 bg-purple-500 text-white text-xs rounded-md hover:bg-purple-600 transition-colors\"\n                  >\n                    Export Debate\n                  </button>\n                </div>\n              )}\n              \n              {/* Input */}\n              <div className=\"p-4 border-t border-slate-200\">\n                <div className=\"flex space-x-2\">\n                  <input\n                    type=\"text\"\n                    value={currentMessage}\n                    onChange={(e) => setCurrentMessage(e.target.value)}\n                    placeholder={selectedDocs.length === 0 ? \"Select documents first...\" : \"Ask about your documents...\"}\n                    disabled={selectedDocs.length === 0 || isLoading}\n                    className=\"flex-1 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-teal-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed\"\n                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}\n                  />\n                  <button\n                    onClick={handleSendMessage}\n                    disabled={!currentMessage.trim() || selectedDocs.length === 0 || isLoading}\n                    className=\"px-4 py-2 bg-gradient-to-r from-teal-500 to-emerald-500 text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:from-teal-600 hover:to-emerald-600 transition-all\"\n                  >\n                    Send\n                  </button>\n                </div>\n                \n                {selectedDocs.length === 0 && (\n                  <p className=\"text-xs text-slate-500 mt-2\">Upload and select documents to start chatting</p>\n                )}\n              </div>\n            </div>\n          </div>\n        </div>\n      </div>\n    </div>\n  );\n};\n\nexport default DocumentGPTv5;"
<parameter name="explanation">Creating the complete v5 React UI component with all features