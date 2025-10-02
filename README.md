# DocumentGPT - AI Writing & Research Assistant

**"The AI assistant that understands your documents better than you do"**

Production-ready SaaS focused on individual productivity with dual-mode AI assistance.

## Architecture

**Ultra-lean single Lambda function** using OpenAI's Vector Stores and Assistants API:
- 84% function reduction from original multi-Lambda design
- 70-80% cost savings ($12-27/month vs $20-35)
- Smart model routing: gpt-3.5-turbo for simple queries, gpt-4o-mini for document analysis
- DynamoDB caching with 24-hour TTL for instant responses

## Live Deployment

- **Frontend**: https://documentgpt.io/
- **API**: https://i1dy8i3692.execute-api.us-east-1.amazonaws.com/prod
- **Endpoints**: `/upload` and `/chat`

## Key Files

- `index.html` - Main React UI with command palette, toast notifications, backend integration
- `web/backup.html` - Backup advanced UI with PDF viewer and action drawer
- `lambda/fixed_chat_handler.py` - Single Lambda handling all operations via OpenAI APIs
- `.env` - Environment variables (Quadrant API key)

## Core Features

**Dual Writing Modes:**
- **Journal Mode**: Interactive live AI assistant with real-time grammar, style, and depth suggestions
- **Research Mode**: Document analysis with AI chat for uploaded PDFs, DOCX, TXT, MD

**Live AI Assistant:**
- Real-time writing enhancement (grammar, tone, depth)
- Pattern recognition for voice and cadence
- Contextual suggestions to improve flow
- Toggle on/off for distraction-free writing

**AI Agents (6 Core Tools):**
- 📧 Email drafting and sending
- 📊 Data extraction to spreadsheets
- 📅 Calendar event creation
- 💾 Smart document saving
- 📤 Multi-format export
- 📝 Intelligent summarization

## AWS Services

- Lambda (single function)
- API Gateway (CORS enabled)
- DynamoDB (caching + workflows)
- Secrets Manager (OpenAI API key)

## Unique Value Proposition

**What makes DocumentGPT different:**
1. **Dual-mode productivity**: Write journals OR analyze research documents
2. **Live AI assistance**: Real-time writing enhancement while you type
3. **AI Agents**: Automated actions like ChatGPT plugins but integrated
4. **Individual focus**: Built for personal productivity, not team collaboration

## Cost Model

- Smart routing reduces API costs
- DynamoDB caching provides instant responses
- Serverless architecture scales to zero
- Monthly cost: $12-27 for typical usage
- Target: Freemium with usage limits, premium for AI Agents