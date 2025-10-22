# Week 1 Tasks - Foundation Sprint
**Goal:** Ship analytics, student plan, and start growth engine  
**Timeline:** 7 days  
**Owner:** Solo founder (you)

---

## Day 1 (Monday): Analytics Foundation

### Morning (3 hours)
- [ ] Sign up for PostHog (free tier, 1M events/month)
- [ ] Add PostHog snippet to backup.html (before `</head>`)
- [ ] Test event firing in PostHog dashboard

### Afternoon (4 hours)
- [ ] Add 6 core events:
  ```javascript
  posthog.capture('signup', {email, plan: 'free'})
  posthog.capture('upload_doc', {doc_id, doc_type: 'pdf'})
  posthog.capture('ask_question', {question_length})
  posthog.capture('export_doc', {format: 'pdf'})
  posthog.capture('upgrade', {plan: 'premium', price: 9.99})
  posthog.capture('cancel', {reason, days_active})
  ```
- [ ] Deploy to staging
- [ ] Test all 6 events manually

### Evening (1 hour)
- [ ] Create PostHog dashboard with 4 funnels:
  1. Visit → Signup → Upload → Ask → Export
  2. Signup → Activation (upload + 3 Qs + export)
  3. Activation → Upgrade
  4. Upgrade → Day 30 retention

---

## Day 2 (Tuesday): Student Plan

### Morning (2 hours)
- [ ] Create Stripe product: "Student Plan" $5.99/mo
- [ ] Add student plan to pricing page
- [ ] Add ".edu email required" badge

### Afternoon (3 hours)
- [ ] Add email verification function:
  ```javascript
  function isStudentEmail(email) {
    return email.endsWith('.edu') || 
           email.endsWith('.ac.uk') ||
           email.endsWith('.edu.au');
  }
  ```
- [ ] Show student plan only if email matches
- [ ] Add "Verify student status" flow

### Evening (2 hours)
- [ ] Test student signup flow
- [ ] Deploy to staging
- [ ] Update pricing page copy

---

## Day 3 (Wednesday): Annual Plan

### Morning (2 hours)
- [ ] Create Stripe product: "Annual Plan" $79/year
- [ ] Add annual toggle to pricing page
- [ ] Show "Save $40/year" badge

### Afternoon (3 hours)
- [ ] Update subscription logic to handle annual billing
- [ ] Test annual checkout flow
- [ ] Add "Most popular" badge to annual plan

### Evening (2 hours)
- [ ] A/B test: Annual vs Monthly default
- [ ] Deploy to staging
- [ ] Monitor conversion rate

---

## Day 4 (Thursday): Growth Dashboard

### Morning (3 hours)
- [ ] Create Google Sheet: "DocumentGPT Growth Dashboard"
- [ ] Add columns: Date, Visitors, Signups, Activations, Paid, Churn, CAC, MRR
- [ ] Connect PostHog data (manual for now, automate later)

### Afternoon (3 hours)
- [ ] Add 4 charts:
  1. Daily signups (line chart)
  2. Activation funnel (bar chart)
  3. MRR growth (line chart)
  4. CAC by channel (bar chart)

### Evening (1 hour)
- [ ] Set up daily email digest (PostHog → Email)
- [ ] Share dashboard with team (if any)

---

## Day 5 (Friday): Video Content Prep

### Morning (3 hours)
- [ ] Write 10 hook scripts:
  1. "Stop reading 100-page PDFs. Upload → Ask → Get answers in 30 seconds."
  2. "I analyzed 50 research papers in 10 minutes using AI."
  3. "How to turn any PDF into a study guide in 60 seconds."
  4. "The AI tool that saved me 20 hours this week."
  5. "Chat with your PDFs like ChatGPT but better."
  6. "I uploaded my thesis and got a 5-bullet summary instantly."
  7. "This AI reads PDFs so you don't have to."
  8. "From 100 pages to 5 key points in 30 seconds."
  9. "The secret tool every student needs for research papers."
  10. "I asked my PDF 10 questions and it answered all of them."

### Afternoon (3 hours)
- [ ] Record 3 shorts (TikTok, Reels, YouTube Shorts)
- [ ] Edit with CapCut (add captions, music, CTA)
- [ ] Add UTM links in bio: `documentgpt.io?utm_source=tiktok&utm_medium=video&utm_campaign=hook1`

### Evening (1 hour)
- [ ] Post to TikTok, Instagram Reels, YouTube Shorts
- [ ] Monitor first 1 hour performance
- [ ] Respond to comments

---

## Day 6 (Saturday): Landing Page Optimization

### Morning (3 hours)
- [ ] Record 15-second demo video:
  - Upload PDF → Ask question → Get answer → Export
- [ ] Add video to hero section (above fold)
- [ ] Add "Upload a doc free" CTA button

### Afternoon (3 hours)
- [ ] Add social proof:
  - "5,000+ documents analyzed"
  - "Trusted by students at 50+ universities"
  - "4.8/5 stars from 200+ users"
- [ ] Add 3 use-case strips:
  1. 📚 Students: "Turn textbooks into study guides"
  2. 💼 Consultants: "Analyze client docs in minutes"
  3. 🔬 Researchers: "Extract insights from papers"

### Evening (1 hour)
- [ ] A/B test: Video vs Static hero
- [ ] Deploy to production
- [ ] Monitor bounce rate

---

## Day 7 (Sunday): Onboarding Flow

### Morning (3 hours)
- [ ] Add onboarding checklist (shows after signup):
  ```
  ✅ Welcome to DocumentGPT!
  [ ] Upload your first document
  [ ] Ask 3 questions
  [ ] Export your notes
  ```
- [ ] Show progress bar (0% → 33% → 66% → 100%)
- [ ] Celebrate completion with confetti 🎉

### Afternoon (3 hours)
- [ ] Write 4 onboarding emails:
  - **Day 0:** "Welcome! Here's how to get started"
  - **Day 2:** "Have you uploaded a doc yet? Here's a template"
  - **Day 5:** "3 ways to use DocumentGPT you might not know"
  - **Day 7:** "Upgrade to Premium and unlock unlimited chats"

### Evening (1 hour)
- [ ] Set up email automation (AWS SES or SendGrid)
- [ ] Test email sequence
- [ ] Monitor open rates

---

## Week 1 Success Metrics

**By end of Week 1, you should have:**
- ✅ Analytics tracking 6 core events
- ✅ Student plan live ($5.99/mo)
- ✅ Annual plan live ($79/year)
- ✅ Growth dashboard with 4 charts
- ✅ 3 video shorts posted (TikTok, Reels, Shorts)
- ✅ Landing page with demo video
- ✅ Onboarding checklist + 4 emails

**Target numbers:**
- 100 visitors/day (from video content)
- 5 signups/day (5% conversion)
- 1 activation/day (20% of signups)
- 0.1 paid users/day (10% of activations)
- $1/day MRR (baseline for growth)

**If you hit these, Week 2 will focus on scaling what works.**

---

## Time Budget (56 hours total)

- **Day 1:** 8 hours (Analytics)
- **Day 2:** 7 hours (Student plan)
- **Day 3:** 7 hours (Annual plan)
- **Day 4:** 7 hours (Dashboard)
- **Day 5:** 7 hours (Video content)
- **Day 6:** 7 hours (Landing page)
- **Day 7:** 7 hours (Onboarding)

**Total:** 50 hours (7 hours/day, 1 day off)

---

## Blockers & Mitigation

**Blocker:** PostHog setup takes too long  
**Mitigation:** Use Google Analytics 4 instead (faster setup)

**Blocker:** Video editing takes 2+ hours per video  
**Mitigation:** Use CapCut templates, batch record 5 videos at once

**Blocker:** Email automation complex  
**Mitigation:** Start with manual emails to first 10 users, automate later

**Blocker:** Student verification requires manual review  
**Mitigation:** Auto-approve .edu emails, manual review for others

---

## Week 1 Checklist (Copy-Paste)

```
Week 1 - Foundation Sprint
[ ] Day 1: PostHog analytics + 6 events
[ ] Day 2: Student plan $5.99/mo
[ ] Day 3: Annual plan $79/year
[ ] Day 4: Growth dashboard (4 charts)
[ ] Day 5: Record 3 video shorts
[ ] Day 6: Landing page demo video
[ ] Day 7: Onboarding checklist + emails
[ ] Deploy to staging → 24hr soak → Production
[ ] Monitor: 100 visitors, 5 signups, 1 activation, 0.1 paid
```

**Next week:** Scale video content (15 shorts/week), start SEO (50 template pages), launch affiliate program.
