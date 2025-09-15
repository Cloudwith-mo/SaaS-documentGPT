# SaaS DocumentGPT v5

🚀 **AI-Powered Document Analysis Platform** - Multi-tenant SaaS with advanced agent capabilities, real-time streaming, and comprehensive document processing.

## ✨ Features

### 🤖 AI-Powered Analysis
- **GPT-5 Integration** - Latest AI models for document understanding
- **Multi-Agent Debates** - Collaborative AI analysis with consensus building
- **Real-time Streaming** - SSE-based live updates and responses
- **Smart Citations** - Precise document references with bbox coordinates

### 📄 Document Processing
- **Multi-format Support** - PDF, DOCX, TXT, images
- **Advanced OCR** - Text extraction with high accuracy
- **Vector Search** - Semantic document search and retrieval
- **Batch Processing** - Handle multiple documents simultaneously

### 🏢 SaaS Architecture
- **Multi-tenant** - Secure data isolation per organization
- **Plan-based Features** - Free, Pro, Enterprise tiers
- **RESTful APIs** - Complete backend API suite
- **Export Capabilities** - JSON, Markdown, PDF exports

### 🎨 Modern UI
- **React Components** - Responsive, accessible interface
- **Three-pane Layout** - Sidebar, PDF viewer, chat panel
- **Light Theme** - Clean, futuristic design with mint-sky gradients
- **Real-time Updates** - Live chat and debate streaming

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Services   │
│   React UI      │◄──►│   Flask API     │◄──►│   GPT-5/Claude  │
│   - Document    │    │   - REST APIs   │    │   - Multi-Agent │
│   - Chat        │    │   - SSE Stream  │    │   - Embeddings  │
│   - PDF Viewer  │    │   - Auth        │    │   - Vector DB   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Installation

1. **Clone Repository**
```bash
git clone https://github.com/Cloudwith-mo/SaaS-documentGPT.git
cd SaaS-documentGPT
```

2. **Setup Backend**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-flask.txt

# Start Flask server
python app.py
```

3. **Setup Frontend**
```bash
# Install dependencies
npm install

# Start development server
npm start
```

4. **Run Tests**
```bash
# Run complete test suite
bash run_all_tests.sh

# Run specific test suites
bash run_all_tests.sh --backend
bash run_all_tests.sh --frontend
bash run_all_tests.sh --integration
```

## 📊 Test Results

Current test status (all passing ✅):

- **Backend Tests**: 12/12 ✅ (100%)
- **Frontend Tests**: 12/12 ✅ (100%) 
- **Integration Tests**: 11/11 ✅ (100%)
- **Overall Success Rate**: 100% (35/35)

## 🛠️ Development

### Project Structure
```
├── app.py                     # Main Flask server
├── DocumentGPT_v5_UI.jsx     # React v5 UI component
├── index-fixed.html          # v2 HTML interface
├── test_suite_v5.py          # Backend API tests
├── frontend_test_v5.js       # Frontend component tests
├── integration_test_v5.py    # End-to-end tests
├── run_all_tests.sh          # Automated test runner
├── v2_to_v5_roadmap.md       # Development roadmap
├── src/
│   ├── handlers/             # Lambda handlers
│   ├── services/             # Business logic
│   └── config/               # Configuration
└── web-app/                  # React application
```

### API Endpoints

#### Core APIs
- `GET /health` - Health check
- `GET /api/v5/health` - API status
- `GET /api/agents` - Agent presets
- `POST /api/pdf/search` - Document search
- `POST /api/debate/export` - Export debates
- `GET /api/debate/stream` - SSE streaming

#### Document APIs
- `POST /api/v5/documents` - Upload documents
- `GET /api/v5/documents` - List documents
- `POST /api/v5/chat` - Chat with documents
- `POST /api/v5/multi-agent-debate` - Start debates

### Testing Strategy

**Mini-Test Approach**: Run focused tests after each change
```bash
# Test specific functionality
python3 test_suite_v5.py --test="Health Endpoint"
python3 test_suite_v5.py --test="PDF Search API"
```

**Full Test Suite**: Comprehensive validation
```bash
./run_all_tests.sh
```

## 🔧 Configuration

### Environment Variables
```bash
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000

# AI Services
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Database
DATABASE_URL=your_db_url
REDIS_URL=your_redis_url
```

### Agent Presets
Configure multi-agent teams in `app.py`:
```python
agent_presets = {
    "tax_expert": {
        "name": "Tax Expert",
        "description": "Specialized in tax document analysis",
        "model": "gpt-4",
        "temperature": 0.1
    }
}
```

## 📈 Roadmap

### Version Progression
- **v2**: Basic upload + chat ✅
- **v3**: Multi-document support ✅
- **v4**: Agent debates + streaming ✅
- **v5**: Full SaaS platform ✅
- **v6**: Advanced analytics (planned)

### Upcoming Features
- [ ] Advanced user management
- [ ] Custom agent training
- [ ] Workflow automation
- [ ] Enterprise integrations
- [ ] Mobile applications

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`bash run_all_tests.sh`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/Cloudwith-mo/SaaS-documentGPT/wiki)
- **Issues**: [GitHub Issues](https://github.com/Cloudwith-mo/SaaS-documentGPT/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Cloudwith-mo/SaaS-documentGPT/discussions)

---

**Built with ❤️ for the future of document intelligence**