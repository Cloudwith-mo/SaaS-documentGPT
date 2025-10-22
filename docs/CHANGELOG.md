# DocumentGPT Changelog

All notable changes to DocumentGPT will be documented in this file.

## [Unreleased] - STG Environment

### Added
- 🎯 **Phase 1 - Frontend Quick Wins**
  - Google Analytics integration (tracking ready)
  - Enhanced mobile responsive CSS (better phone/tablet layouts)
  - Reduced motion support for accessibility

- 🚀 **Phase 2 - Marketing Improvements**
  - Already had Open Graph meta tags ✅
  - Already had Twitter Card support ✅

- 🔧 **Phase 3 - Backend Improvements**
  - File size validation (10MB limit)
  - Analytics event tracking (chat_sent, document_uploaded)
  - Better error logging (console.error)

- ♿ **Phase 4 - Polish & Accessibility**
  - Enhanced ARIA labels on all interactive buttons
  - aria-expanded states for dropdown menus
  - aria-live regions for toast notifications
  - Reduced motion CSS support

### Changed
- None

### Fixed
- None

---

## [1.1.0] - 2024-01-15 - PRODUCTION

### Added
- 🎨 Transparent loading overlay with animated wizard character
  - Dark semi-transparent background (50% opacity)
  - Bouncing wizard emoji animation
  - Dynamic loading text updates
  - Non-blocking UI (can see app underneath)

### Changed
- None

### Fixed
- None

---

## [1.0.0] - 2024-01-15 - PRODUCTION

### 🎉 Initial Production Release

#### Core Features
- ✅ Rich text editor with formatting toolbar
- ✅ AI-powered chat assistant
- ✅ PDF document upload & analysis
- ✅ Multi-document management
- ✅ Real-time autosave (3s debounce)

#### AI Features
- ✅ 6 AI Agents:
  - 📝 Summarization
  - 📧 Email drafting (AWS SES)
  - 📊 Data extraction to CSV (S3 exports)
  - 📅 Calendar event creation (iCal downloads)
  - 💾 Smart document saving
  - 📤 Multi-format export (PDF/DOCX/TXT)
- ✅ Instant Insights panel (draggable)
- ✅ Smart highlights (3 types: key, action, important)
- ✅ Contextual AI chat with document awareness

#### Document Management
- ✅ Multiple document tabs
- ✅ Folder organization
- ✅ Document search
- ✅ Version history (auto-save every 30s, keep last 20)
- ✅ Undo delete (5s window)

#### UI/UX
- ✅ 7 Modal dialogs:
  - Upgrade plans
  - Login/Signup
  - Settings
  - Folders
  - Command Palette (⌘K)
  - Keyboard Shortcuts
  - Version History
- ✅ Dark mode support
- ✅ Focus mode (hide sidebars)
- ✅ Zoom controls (80%-150%)
- ✅ Find & replace
- ✅ Mobile responsive design
- ✅ Keyboard shortcuts
- ✅ Tooltips on hover

#### Analytics & Metrics
- ✅ Word count
- ✅ Reading time estimate
- ✅ Tone detection (Excited/Curious/Neutral)
- ✅ Readability score (Flesch-Kincaid)

#### Authentication & Billing
- ✅ AWS Cognito authentication
- ✅ Guest mode (localStorage)
- ✅ Usage tracking (chats, documents)
- ✅ Freemium model:
  - Free: 50 chats/month, 10 documents
  - Starter: $1.99/mo - 50 chats, 5 docs
  - Pro: $12.99/mo - Unlimited chats, 30 docs
  - Business: $29.99/mo - Unlimited everything
- ✅ Stripe integration (planned)

#### Performance
- ✅ Client-side PDF parsing (pdf.js)
- ✅ Optimistic UI updates
- ✅ 30s usage cache (reduce API calls)
- ✅ Debounced autosave
- ✅ Lazy-loaded chat history
- ✅ Progress bar for operations

#### Data Persistence
- ✅ localStorage state management (v3)
- ✅ Cloud sync for authenticated users
- ✅ Per-document chat history
- ✅ Per-document insights & highlights
- ✅ Settings persistence

---

## Version History

### v1.1.0 (Current Production)
- **File**: `index.html`
- **Size**: ~95.4KB
- **Status**: 🚀 Live at https://documentgpt.io/
- **Stability**: Production-ready
- **Last Updated**: 2024-01-15
- **New Features**:
  - Transparent loading overlay

### v1.1.0-staging
- **File**: `backup.html`
- **Size**: ~95.4KB
- **Status**: 🧪 Testing at https://documentgpt.io/backup.html
- **Stability**: Stable, pre-production
- **Last Updated**: 2024-01-15

### v1.1.0-dev
- **File**: `backup-unified.html`
- **Size**: ~95.4KB
- **Status**: 🔧 Development at https://documentgpt.io/backup-unified.html
- **Stability**: Experimental
- **Last Updated**: 2024-01-15

---

## Deployment History

### 2024-01-15
- ✅ Added transparent loading overlay to DEV
- ✅ Promoted to STG (backup.html)
- ✅ Promoted to PRD (index.html)
- 🚀 v1.1.0 LIVE!

### 2024-01-14
- ✅ Fixed upload bug in STG
- ✅ Promoted to PRD

### 2024-01-13
- ✅ Added version history feature
- ✅ Tested in STG
- ✅ Promoted to PRD

### 2024-01-12
- ✅ Initial production deployment
- ✅ All core features live

---

## Known Issues

### DEV
- None currently

### STG
- None currently

### PRD
- None currently

---

## Planned Features

### v1.1.0 (Current Release)
- [x] Transparent loading overlay ✅ LIVE

### v1.2.0 (Next Release)
- [ ] DocIQ metrics in bottom bar
- [ ] Voice input (speech-to-text)
- [ ] Mode-based processing (Journal vs Research)
- [ ] Simplified UI (fewer buttons)

### v1.2.0 (Future)
- [ ] Real-time collaboration
- [ ] Document templates
- [ ] Advanced export options
- [ ] Mobile app (PWA)
- [ ] Offline mode
- [ ] Custom AI prompts

### v2.0.0 (Long-term)
- [ ] Team workspaces
- [ ] Document sharing
- [ ] Comments & annotations
- [ ] API access
- [ ] Integrations (Notion, Google Drive, Dropbox)

---

## Breaking Changes

### v1.0.0
- Migrated from `dgpt:state:v1` to `dgpt:state:v3`
- Old state automatically cleared on load
- Users may need to re-upload documents

---

## Performance Metrics

### Load Times
- Initial page load: ~300ms
- Document upload: 4-10s (depending on size)
- Chat response: 2-5s
- Autosave: 3s debounce

### File Sizes
- HTML/CSS/JS: 95KB (uncompressed)
- Gzipped: ~25KB (estimated)
- PDF.js library: 3.11.174 (CDN)
- jsPDF library: 2.5.1 (CDN)

### API Endpoints
- Chat: `POST /prod/chat`
- Upload: `POST /prod/upload`
- Agent: `POST /prod/agent`
- Usage: `GET /prod/usage`
- Documents: `POST /prod/documents`, `GET /prod/documents`

---

## Security

### Authentication
- AWS Cognito user pools
- JWT token-based sessions
- Guest mode with localStorage

### Data Storage
- Client-side: localStorage (encrypted by browser)
- Server-side: DynamoDB (encrypted at rest)
- S3: Encrypted exports

### API Security
- CORS enabled for documentgpt.io
- Rate limiting on Lambda
- Usage limits enforced

---

## Browser Support

### Fully Supported
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### Partially Supported
- ⚠️ Mobile Safari (some features limited)
- ⚠️ Chrome Mobile (some features limited)

### Not Supported
- ❌ IE11 and below
- ❌ Opera Mini

---

## Dependencies

### Frontend
- Tailwind CSS 3.x (CDN)
- PDF.js 3.11.174 (CDN)
- jsPDF 2.5.1 (CDN)
- AWS SDK 2.1563.0 (CDN)
- Amazon Cognito Identity JS 6.3.12 (CDN)

### Backend
- AWS Lambda (Python 3.9)
- AWS DynamoDB
- AWS S3
- AWS SES
- AWS API Gateway
- AWS Cognito

---

## License

Proprietary - All rights reserved

---

## Contact

- Website: https://documentgpt.io
- Support: support@documentgpt.io
- Twitter: @documentgpt

---

## Notes

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.
Version numbers follow [Semantic Versioning](https://semver.org/).
