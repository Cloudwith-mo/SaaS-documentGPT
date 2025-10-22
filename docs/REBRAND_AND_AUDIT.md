# Rebrand + Current State Audit + First 100 Users Plan

---

## 🎯 NEW BRAND NAME OPTIONS (2 syllables, demure, no "GPT")

### Top 3 Recommendations:
1. **Docly** (doc-lee) - Simple, friendly, memorable
2. **Notely** (note-lee) - Academic, note-taking focus
3. **Readly** (read-lee) - Action-oriented, clear value

### Alternatives:
- **Lumina** (loo-min-ah) - Light/insight theme
- **Claros** (clar-os) - Clarity theme
- **Nexus** (nex-us) - Connection theme
- **Prism** (priz-um) - Analysis/insight theme

**Recommendation: Go with "Docly"**
- Available domain: docly.io ($12/year)
- Clean, modern, memorable
- Works globally (easy to pronounce)
- Not taken on social (@docly available on most platforms)

---

## 📊 CURRENT STATE AUDIT

### ✅ ENGINEERING (What You Have)

#### Frontend (backup.html)
- [x] Dual-mode editor (Journal/Research)
- [x] Tab autocomplete (600-800ms, 30-75 tokens)
- [x] AI Chat with document context
- [x] PDF upload & analysis
- [x] 6 AI Agents (email, CSV, calendar, save, export, summary)
- [x] Smart highlights (clarity, actionable, complete)
- [x] DocIQ scoring
- [x] Instant Insights panel
- [x] Lightning menu (⚡)
- [x] Responsive design (mobile-friendly)

#### Backend (Lambda)
- [x] Single Lambda function (docgpt-chat)
- [x] `/chat` endpoint (OpenAI gpt-4o-mini)
- [x] `/autocomplete` endpoint (fast completions)
- [x] DynamoDB cache (1hr TTL)
- [x] Stripe integration (webhooks)
- [x] Cognito auth (email/password)

#### Infrastructure
- [x] S3 static hosting
- [x] CloudFront CDN (E2O361IH9ALLK6)
- [x] API Gateway (prod stage)
- [x] DynamoDB tables (docgpt, subscriptions, usage)
- [x] AWS SES (email sending)

#### Environments
- [x] Dev: backup.html
- [x] Staging: staging-v2.html
- [x] Prod: app.html (currently = index.html landing page)

**ISSUE:** You have 3 frontend envs but only 1 backend (prod Lambda). Need staging Lambda.

---

### ❌ MARKETING (What You're Missing)

#### Website
- [x] Landing page (index.html) - EXISTS but needs work
- [ ] Demo video (15 sec)
- [ ] Social proof (user count, testimonials)
- [ ] Use case pages (students, consultants, researchers)
- [ ] Pricing page (clear tiers)
- [ ] Blog (0 posts)
- [ ] Help center (0 articles)
- [ ] Changelog (0 entries)

#### SEO
- [ ] 0 template pages (Jenni has 10+)
- [ ] 0 blog posts
- [ ] No sitemap
- [ ] No schema markup
- [ ] No backlinks

#### Social Media
- [ ] 0 TikTok videos
- [ ] 0 Instagram posts
- [ ] 0 YouTube videos
- [ ] 0 Twitter/X posts
- [ ] No social accounts created

#### Distribution
- [ ] 0 paid ads
- [ ] 0 affiliates
- [ ] 0 community posts
- [ ] No Chrome extension
- [ ] No Product Hunt launch

---

## 🆚 DOCLY vs JENNI AI - GAP ANALYSIS

### What Jenni Has That You Don't:

#### Product
- [ ] Web Importer (Chrome extension to clip sources)
- [ ] Literature Review Generator
- [ ] In-text citations (2,600+ styles)
- [ ] LaTeX export
- [ ] Team plans
- [ ] Version history
- [ ] Outline builder (you removed it)
- [ ] PDF search (you removed it)

#### Marketing
- [ ] 50+ blog posts
- [ ] 10+ feature pages
- [ ] Help center (100+ articles)
- [ ] Changelog (updated weekly)
- [ ] YouTube channel (tutorials)
- [ ] Case studies (universities)
- [ ] Academy (training resources)

#### Distribution
- [ ] Chrome extension (10k+ users)
- [ ] Social media presence (TikTok, Instagram, YouTube)
- [ ] SEO (ranks for "AI essay writer", "paraphrasing tool")
- [ ] Paid ads (Google, Meta)
- [ ] Affiliate program

### What You Have That Jenni Doesn't:

#### Product
- [x] 6 AI Agents (Jenni has 0)
- [x] DocIQ scoring (unique)
- [x] Smart highlights (unique)
- [x] Dual modes (Journal/Research)
- [x] Ultra-lean architecture (84% cost savings)

#### Pricing
- [x] Cheaper ($9.99 vs $12-30)
- [x] Better free tier (10 chats vs Jenni's limits)

### Your Competitive Edge:
1. **Agents** - Interactive workflows (email, CSV, calendar)
2. **Price** - 40% cheaper than Jenni
3. **Simplicity** - Clean UX, not academic-heavy
4. **Speed** - Ultra-lean Lambda (600-800ms)

---

## 🏗️ INFRASTRUCTURE FIX (3 Environments)

### Current Problem:
- Frontend: 3 envs (dev, staging, prod)
- Backend: 1 env (prod Lambda)
- **Risk:** Testing on prod = potential user impact

### Solution: Add Staging Lambda

```bash
# Create staging Lambda
aws lambda create-function \
  --function-name docgpt-chat-staging \
  --runtime python3.9 \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --handler simple_handler.lambda_handler \
  --zip-file fileb://lambda.zip

# Create staging API Gateway
aws apigatewayv2 create-api \
  --name docgpt-api-staging \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:ACCOUNT:function:docgpt-chat-staging

# Update staging-v2.html to use staging API
const API = 'https://STAGING_API_ID.execute-api.us-east-1.amazonaws.com/staging';
```

### 3-Environment Setup:
- **Dev (backup.html):** Points to staging Lambda, daily deploys
- **Staging (staging-v2.html):** Points to staging Lambda, weekly deploys
- **Prod (app.html):** Points to prod Lambda, monthly deploys

---

## 📋 YOUR CURRENT LINKS (vs Jenni's 30+ links)

### What You Have:
1. https://documentgpt.io/ (landing page)
2. https://documentgpt.io/backup.html (dev app)
3. https://documentgpt.io/staging-v2.html (staging app)
4. https://documentgpt.io/app.html (prod app - currently broken, shows landing)
5. https://documentgpt.io/landing-page.html (marketing page)

### What You Need (to match Jenni):
- [ ] /pricing
- [ ] /about
- [ ] /blog
- [ ] /help
- [ ] /changelog
- [ ] /ai-chat
- [ ] /summarizer
- [ ] /essay-writer
- [ ] /paraphrasing-tool
- [ ] /terms
- [ ] /privacy
- [ ] /refund-policy

**Gap: You have 5 links, Jenni has 30+. Need 25 more pages.**

---

## 🎯 PLAN TO FIRST 100 USERS (Strangers, Not Friends)

### Phase 1: Foundation (Week 1) - 10 users

#### Day 1: Rebrand
- [ ] Buy docly.io domain ($12)
- [ ] Update all files (backup.html, staging, prod)
- [ ] Create social accounts (@docly on TikTok, Instagram, X, YouTube)
- [ ] Update Stripe product names

#### Day 2: Analytics
- [ ] Add PostHog (4 events: signup, upload, export, upgrade)
- [ ] Deploy to staging → test → prod

#### Day 3: Demo Video
- [ ] Record 15-sec demo (upload → ask → answer → export)
- [ ] Add to landing page hero section
- [ ] Post to social media (first content)

**Target: 10 signups from friends/family (beta testers)**

---

### Phase 2: Content Blitz (Week 2-3) - 50 users

#### Video Content (15 shorts/week)
**Week 2:**
- [ ] Mon: "Stop reading 100-page PDFs" (TikTok, Reels, Shorts, X)
- [ ] Tue: "I analyzed 50 papers in 10 minutes"
- [ ] Wed: "Turn any PDF into study notes"
- [ ] Thu: "This AI reads PDFs so you don't have to"
- [ ] Fri: "From 100 pages to 5 key points"

**Week 3:**
- [ ] Mon: "How students use Docly for research"
- [ ] Tue: "Chat with your PDFs like ChatGPT"
- [ ] Wed: "Export your notes in 1 click"
- [ ] Thu: "Free forever, upgrade for unlimited"
- [ ] Fri: "Docly vs reading PDFs manually"

**Target: 1,000 video views → 100 visits → 50 signups**

---

### Phase 3: SEO Foundation (Week 4-5) - 100 users

#### Template Pages (10 pages)
1. /pdf-summarizer
2. /research-paper-analyzer
3. /essay-outline-generator
4. /study-guide-creator
5. /literature-review-tool
6. /pdf-to-notes
7. /document-chat
8. /ai-writing-assistant
9. /paraphrasing-tool
10. /citation-generator

**Each page:**
- Hero: "Free [Tool Name] - Upload & Get Results in 30 Seconds"
- Demo video
- CTA: "Try Free →"
- SEO: Title, meta, schema markup

**Target: 500 organic visits → 25 signups → 100 total users**

---

### Phase 4: Paid Ads Test (Week 6) - 150 users

#### Google Search Ads ($100 budget)
**Keywords:**
- "chat with pdf" ($0.50 CPC)
- "pdf summarizer free" ($0.30 CPC)
- "research paper analyzer" ($0.40 CPC)

**Budget allocation:**
- $50 on "chat with pdf" (100 clicks)
- $30 on "pdf summarizer" (100 clicks)
- $20 on "research paper analyzer" (50 clicks)

**Expected:**
- 250 clicks → 12 signups (5% conversion) → 1 paid user

**Target: 50 more signups → 150 total users**

---

## 💰 $100 AD BUDGET BREAKDOWN

### Option 1: Google Search Only
- $100 on Google Search Ads
- Target: "chat with pdf", "pdf summarizer"
- Expected: 200-300 clicks → 10-15 signups → 1-2 paid users
- **Best for:** Immediate conversions

### Option 2: Mixed (Recommended)
- $50 Google Search (high intent)
- $30 TikTok Ads (brand awareness)
- $20 Reddit Ads (r/GradSchool, r/AskAcademia)
- Expected: 500 impressions + 100 clicks → 15-20 signups → 2-3 paid users
- **Best for:** Testing multiple channels

### Option 3: Content Boost
- $0 on ads
- $100 on Fiverr creators (10 creators × $10 each to post your video)
- Expected: 5,000 views → 200 visits → 20 signups → 2 paid users
- **Best for:** Viral potential

**Recommendation: Option 2 (Mixed) - Test multiple channels with $100**

---

## 🚀 IMMEDIATE ACTION PLAN (Next 7 Days)

### Day 1 (Today)
- [ ] Choose brand name (Docly recommended)
- [ ] Buy domain ($12)
- [ ] Create social accounts (@docly)
- [ ] Update README.md with new name

### Day 2
- [ ] Add PostHog analytics (4 events)
- [ ] Deploy to staging → test → prod
- [ ] Create staging Lambda (separate from prod)

### Day 3
- [ ] Record 15-sec demo video
- [ ] Add to landing page
- [ ] Post to TikTok, Instagram, X, YouTube

### Day 4-7
- [ ] Record 5 shorts (1 per day)
- [ ] Post to all platforms
- [ ] Text 10 friends/family for beta testing
- [ ] Get first 10 users

**By Day 7: 10 users, 5 videos posted, analytics tracking, staging env live**

---

## 📊 SUCCESS METRICS (First 100 Users)

### Week 1: 10 users (friends/family)
- 10 signups
- 5 activations (upload + 3 Qs + export)
- 1 paid user ($9.99)

### Week 2-3: 50 users (video content)
- 1,000 video views
- 100 website visits
- 50 signups
- 5 paid users

### Week 4-5: 100 users (SEO + organic)
- 500 organic visits
- 25 signups
- 10 paid users

### Week 6: 150 users (paid ads)
- $100 ad spend
- 250 clicks
- 15 signups
- 3 paid users

**Total: 150 users, 19 paid ($189 MRR), $100 spent = $5.26 CAC**

---

## ✅ CHECKLIST (Copy-Paste)

```
Rebrand + First 100 Users
[ ] Choose name (Docly recommended)
[ ] Buy domain ($12)
[ ] Create social accounts
[ ] Add staging Lambda (separate from prod)
[ ] Add PostHog analytics
[ ] Record 15-sec demo video
[ ] Post to landing page
[ ] Record 5 shorts (Week 1)
[ ] Text 10 friends for beta (10 users)
[ ] Create 10 template pages (SEO)
[ ] Launch $100 ad campaign (mixed)
[ ] Hit 100 users milestone
[ ] Get 10+ paying users ($100 MRR)
```

**Next milestone: 1,000 users, $1,000 MRR (Month 3)**
