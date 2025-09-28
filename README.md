# DocumentGPT - AI Document Assistant

Production-ready SaaS for document processing with OpenAI integration.

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

## Features

- Document upload (PDF, TXT, DOCX, MD)
- AI chat with document context
- Smart caching and cost optimization
- Command palette (⌘K), keyboard shortcuts
- Toast notifications and progress tracking
- Dark/light theme with brand colors

## AWS Services

- Lambda (single function)
- API Gateway (CORS enabled)
- DynamoDB (caching + workflows)
- Secrets Manager (OpenAI API key)

## Cost Model

- Smart routing reduces API costs
- DynamoDB caching provides instant responses
- Serverless architecture scales to zero
- Monthly cost: $12-27 for typical usage