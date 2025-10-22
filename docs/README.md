# DocumentGPT - AI Writing & Research Assistant

**"The AI assistant that understands your documents better than you do"**

Ultra-lean SaaS for individual productivity with dual-mode AI assistance and interactive agents.

## 🚀 Live URLs
- **Production**: https://documentgpt.io/app.html
- **Landing**: https://documentgpt.io/landing-page.html
- **API**: https://i1dy8i3692.execute-api.us-east-1.amazonaws.com/prod

## 🔄 Development Workflow
- **app.html** = Production (stable, live users)
- Work directly on app.html for all changes

## 🏗️ Ultra-Lean Architecture

**Single Lambda Function** handling everything:
- 84% function reduction from multi-Lambda designs
- 70-80% cost savings ($8-15/month vs $20-35)
- Smart OpenAI model routing
- Real-time usage tracking & limits

**AWS Resources:**
- `docgpt-chat` - Single Lambda (Python 3.9)
- `docgpt` - DynamoDB cache table
- `documentgpt-subscriptions` - User subscriptions
- `documentgpt-usage` - Usage tracking & limits
- `documentgpt/stripe-secret` - Stripe API key
- S3 static hosting + API Gateway

## 💡 Core Features

**Dual Writing Modes:**
- **Journal**: Live AI writing assistance with real-time suggestions
- **Research**: Document analysis with intelligent Q&A chat

**6 Interactive AI Agents:**
- 📧 Email drafting & sending (AWS SES)
- 📊 Data extraction to CSV (S3 exports)
- 📅 Calendar event creation (iCal downloads)
- 💾 Smart document saving
- 📤 Multi-format export (PDF/DOCX/TXT)
- 📝 Intelligent summarization

**Freemium Model:**
- **Free**: 10 chats/month, 2 documents
- **Premium**: $14.99/month unlimited + all agents

## 📁 File Structure
```
├── web/
│   ├── app.html             # Production
│   └── landing-page.html    # Marketing page
├── lambda/
│   ├── simple_handler.py    # Single Lambda function
│   └── requirements.txt     # Dependencies
├── cognito-config.json      # Auth configuration
├── test_real_user.py        # User workflow tests
└── README.md               # This file
```

## 🎯 Unique Value Proposition
1. **Maximized chat interface** - Chat is the primary feature
2. **Interactive AI agents** - Two-step confirmation workflows
3. **Ultra-lean architecture** - Single Lambda, minimal costs
4. **Individual productivity focus** - Not team collaboration
5. **Real AWS integrations** - SES, S3, iCal, Stripe

## 💰 Business Model
- **Target**: Individual knowledge workers
- **Pricing**: Freemium with usage limits
- **Revenue**: Subscription upgrades for unlimited access
- **Costs**: $8-15/month operating expenses
- **Margin**: 85-90% gross margin potential

## 🔧 Development Commands
```bash
# Deploy to production
aws s3 cp web/app.html s3://documentgpt-website-prod/app.html --cache-control "max-age=0, no-cache"
aws cloudfront create-invalidation --distribution-id E2O361IH9ALLK6 --paths "/app.html"
```

## ⚡ Performance Optimizations

**Frontend**:
- ✅ Removed unused Lumina features (focus horizon, active block)
- ✅ Cached render() - skips if doc unchanged
- ✅ Lazy loaded heavy libraries (PDF.js, jsPDF)

**Backend**:
- ✅ DynamoDB cache for chat responses (1 hour TTL)
- ✅ Using gpt-4o-mini for faster responses (800ms vs 1200ms)
- 🔄 Streaming responses (prepared, not yet enabled)

**Infrastructure**:
- ✅ CloudFront CDN for static files (200+ edge locations)
- ✅ Gzip compression (72% file size reduction)
- ✅ Browser caching headers (1 hour HTML, 7 days assets)

**Results**:
- 36% faster initial load (2.8s → 1.8s)
- 60% faster chat responses (1.5s → 0.6s)
- 70% lower API costs ($0.002 → $0.0006 per chat)
- 60% reduction in operating costs ($20-35 → $8-15/month)

See `PERFORMANCE_OPTIMIZATIONS.md` for details.

## 🧪 Testing

**Automated Test Runner**: https://documentgpt.io/test-runner.html

**Quick Test**:
```bash
# Verify all buttons exist and have handlers
./verify_buttons.sh
```

**Manual Test Checklist**: See `MANUAL_TEST_CHECKLIST.md`

**Console Test**: Open backup.html and run `test_user_flow.js` in console

### Test Coverage
- ✅ 23+ buttons verified
- ✅ 10 automated user flow tests
- ✅ Event handler verification
- ✅ State persistence tests
- ✅ Modal functionality tests

Built for maximum efficiency, minimum complexity, maximum profitability.