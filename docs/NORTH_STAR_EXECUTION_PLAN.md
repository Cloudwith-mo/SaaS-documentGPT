# DocumentGPT North Star Execution Plan

_Last updated: 1 Nov 2025 · 00:23 UTC_

This tracker converts the migration roadmap into actionable, sequential tasks. Update statuses as you progress. Each epic is broken into weekly work packets sized for a single engineer.

Legend: ☐ todo · ☐⚙ in progress · ☑ done

---

**Phase Lock** · Phase 1 & Phase 2 verification flows green as of 1 Nov 2025 00:06 UTC (system-health dashboard + Mini E2E + Health CI).

## Phase 1 · LangChain/MCP Orchestration (Weeks 1–6)

### Epic 1 · Strengthen LangGraph Orchestration Layer
1. ☑ Inventory current Q&A pipeline (handlers, prompt construction, citation logic).
2. ☑ Consolidate Pinecone helpers + doc-filter handling (shared module, context propagation).
3. ☑ Build request-scoped LangGraph adapter under `lambda/agents/` (reduce global state, prep for extensions).
4. ☑ Replace legacy fallback in `/dev/chat` once LangGraph parity is confirmed (feature flag cleanup).
5. ☑ Port citation formatting/tests to shared adapter (unit coverage for success/error paths).

6. ☑ Smoke test (`test-langchain.sh`) against new flow; log parity results.

### Epic 2 · Adopt LangGraph for Multi-Step Reasoning
1. ☑ Design initial LangGraph node graph (retrieve → answer → tool selection).
2. ☑ Implement state management and persistence per request.
3. ☑ Integrate follow-up handling (branching) in graph.
4. ☑ Extend tests (`lambda/tests/test_langgraph_agent.py`) for new branches.
5. ☑ Deploy behind flag, collect session logs, iterate on graph.

### Epic 3 · MCP Integration for Tool Use
1. ☑ Choose MCP transport (Hosted vs Streamable) and record credentials.
2. ☑ Prototype web search MCP tool (query → DDGS/other API).
3. ☑ Wire MCP client into LangGraph agent tool registry.
4. ☑ Add observability (tool invocation logging, error retries).
5. ☑ Security review & rate limiting for external calls.

### Epic 4 · Web Browsing Capability (Pro Feature)
1. ☑ Implement SearchTool (Bing/Serp API integration).
2. ☑ Implement WebReaderTool (fetch + sanitize page text).
3. ☑ Gate tool usage by user tier (Pro) in agent config.
4. ☑ Update frontend to surface “web” citations distinctly.
5. ☑ Run E2E scenario: out-of-domain question → search → cite result.

---

## Phase 2 · Core Lock-In Features (Weeks 7–18)

**Verification**: Run `bash scripts/phase2_verification.sh` (requires `.venv` activated) to validate all completed epics.

### Epic 1 · Voice Memos with Transcription
1. ☑ Build microphone UI component (desktop/mobile).
2. ☑ Create upload Lambda/API route for audio blobs → S3.
3. ☑ Invoke Whisper transcription (sync) and return text to client.
4. ☑ Persist transcript to DynamoDB (tag `#voice`) and enqueue embedding.
5. ☑ Validate searchability; add regression test.

### Epic 2 · Batch Journal Upload
1. ☑ Multi-file upload UI (drag & drop + status).
2. ☑ S3 ingest + Step Functions orchestration template.
3. ☑ File-type parsers (.txt, .md, .docx) with text extraction.
4. ☑ Batch embedding/insertion + progress monitor.
5. ☑ User-facing completion notifications.

### Epic 3 · Real-Time AI Co-Writer
1. ☑ Implement typing pause detection + debounce (frontend).
2. ☑ Create `/suggest` API using GPT prompt tuned to user style.
3. ☑ Render ghost text, Tab accept, Esc dismiss interactions.
4. ☑ Cache suggestions per context to reduce API calls.
5. ☑ Add opt-in toggle & metrics logging.

### Epic 4 · Second Brain Dashboard
1. ☑ Weekly digest Lambda (summaries + stats) scheduler.
2. ☑ Streak tracker (DynamoDB counter, milestone badges).
3. ☑ “On This Day” query + UI component.
4. ☑ Sentiment analysis pipeline + timeline chart.
5. ☑ Theme/topic trend computation + visualization.

### Epic 5 · Smart Backlinks & Auto-Tagging
1. ☑ Auto-tagging prompt/workflow on entry save.
2. ☑ Pinecone similarity query for related entries.
3. ☑ Entry UI updates: related list + tag filters.
4. ☑ Pattern detection job (keyword spikes, repeated phrases).
5. ☑ Surface pattern alerts on dashboard.

---

## Phase 3 · Advanced Intelligence & Knowledge Graph (Weeks 19–30)

### Epic 1 · Temporal Analysis Tools
1. ☐ Monthly topic frequency job + chart.
2. ☐ Enhanced sentiment/emotion classifier + moving averages.
3. ☐ Writing velocity metrics + visualizations.
4. ☐ Rule-based predictive insights (trend extrapolation).

### Epic 2 · Personal Knowledge Graph
1. ☐⚙ Entity extraction pipeline (NER + storage schema).
2. ☐ Auto-link entities in entry renderer (hover → reference list).
3. ☐ Build entity ↔ entry relationship queries.
4. ☐ Graph visualization (D3 or equivalent) MVP.

### Epic 3 · AI Life Wiki
1. ☐ Wiki page generation prompts + storage format.
2. ☐ User edit support with merge-safe sections.
3. ☐ Wiki browser UI + entity/search navigation.
4. ☐ Markdown/Notion export tooling.

---

## Phase 4 · Premium & Collaborative Features (Weeks 31–36)

### Epic 1 · Predictive Journaling & Suggestions
1. ☐ Prompt suggestion engine (template + AI generation).
2. ☐ Mood prediction heuristics + UI messaging safeguards.
3. ☐ Goal tracking extraction + follow-up scheduler.

### Epic 2 · Cross-Document Intelligence
1. ☐ Contradiction detection prototype (document compare flow).
2. ☐ Meta-insight generation pipeline (goal follow-ups, triggers).
3. ☐ UI surfacing (insight cards, notifications).

### Epic 3 · Collaborative Mode (Enterprise)
1. ☐ Multi-workspace data model (DynamoDB/Pinecone namespacing).
2. ☐ Workspace roles & permissions.
3. ☐ SSO integration (Cognito federation).
4. ☐ Team dashboard + shared content flows.

---

## Ongoing · Observability, Security, Cost
1. ☑ Automate smoke tests (Phase 2 verification harness: `scripts/phase2_verification.sh`).
2. ☐ Implement structured tool telemetry + dashboards.
3. ☐ Review AWS/GPT cost metrics monthly; adjust model usage.
4. ☐ Security reviews after each major feature (encryption, IAM least privilege).

**Phase 2 Verification Harness**: `scripts/phase2_verification.sh` orchestrates:
- Voice memo ingestion structure checks
- Node smoke tests on UI/backend
- Batch upload scaffolding validation
- Co-writer regression + live curl tests
- Weekly digest/dashboard pytest coverage
- Known benign warnings: PyPDF2 deprecation (scheduled for dependency sweep in Phase 3).
- Manual API sanity: `curl -fsSL -H "Authorization: Bearer $BEARER" -H "X-DocGPT-State: $(printf '{"'"'"docs"'"'":0,"'"'"tags"'"'":0}' | base64)" "https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/dev/system-health?userId=$TEST_USER"`

---

## Phase 5 · Professional Document Intelligence (Weeks 37–48)

**Strategic Goal**: Build horizontal platform foundation to compete with Luminance (document analysis), Legora (workflow integration), and Jenni AI (AI co-writing). Foundation enables vertical specialization (legal, consulting, research, healthcare) post-completion.

### Epic 1 · Document Analysis Engine (Luminance Parity)
1. ☐ Clause/section extraction (NER + pattern matching for key terms, definitions, obligations).
2. ☐ Document comparison tool (diff algorithm to highlight changes between versions).
3. ☐ Risk flagging system (identify problematic language, missing clauses, compliance issues).
4. ☐ Metadata extraction (auto-detect parties, dates, amounts, document type).
5. ☐ Structured data output (JSON export of extracted entities + relationships).
6. ☐ UI for analysis results (highlight extracted clauses, show risk scores, comparison view).

### Epic 2 · Workflow Integration Layer (Legora Parity)
1. ☐ Google Docs add-on MVP (sidebar with AI chat, insert suggestions directly).
2. ☐ Microsoft Word plugin (VSTO or Office.js integration).
3. ☐ Export engine with formatting (.docx with styles, headers, citations preserved).
4. ☐ Document template library (contracts, proposals, reports, research papers).
5. ☐ Version control system (track document changes, rollback capability).
6. ☐ Browser extension (capture web content, annotate PDFs in-browser).

### Epic 3 · Advanced AI Co-Writing (Jenni Parity)
1. ☐ Style matching engine (analyze user's past writing, mimic tone/voice).
2. ☐ Citation formatter (APA, MLA, Chicago, IEEE with auto-bibliography generation).
3. ☐ Context-aware suggestions (understand document structure, suggest relevant sections).
4. ☐ Multi-language support (detect language, provide suggestions in same language).
5. ☐ Plagiarism detection (optional: compare against web/uploaded docs).
6. ☐ Writing analytics (readability score, word count goals, pacing feedback).

### Epic 4 · Team & Enterprise Features (All Three Have This)
1. ☐ Enhanced multi-workspace (complete Phase 4 Epic 3 if not done).
2. ☐ Advanced permissions (view/edit/admin roles, document-level access control).
3. ☐ Shared template library (team templates, approval workflows).
4. ☐ Activity feed (who edited what, document history, team notifications).
5. ☐ Usage analytics dashboard (team metrics, cost allocation, feature adoption).
6. ☐ API access (programmatic document upload, analysis, export for integrations).

### Epic 5 · Professional Features & Polish
1. ☐ Bulk operations (analyze 100+ documents, batch export, mass tagging).
2. ☐ Custom workflows (if-then rules, auto-routing, approval chains).
3. ☐ Compliance reporting (audit logs, data retention policies, export controls).
4. ☐ White-label capability (custom branding, domain, email templates).
5. ☐ Performance optimization (sub-second response for 1000+ page documents).
6. ☐ Mobile apps (iOS/Android with core features: upload, chat, review).

---

## Phase 6 · Vertical Specialization (Weeks 49+)

**Post-Foundation Strategy**: Once Phase 5 complete, choose vertical based on user data and market opportunity. Foundation supports all verticals with minimal additional work.

### Potential Verticals (Choose One to Start)

**Option A: Legal (Legora's Territory)**
- Contract-specific analysis (clause libraries, standard terms)
- Legal research integration (case law, statutes)
- Matter management (organize by case/client)
- Pricing: $99-299/mo per lawyer

**Option B: Consulting (High-Value Market)**
- Proposal generation (RFP response automation)
- Client project organization (engagement-based folders)
- Deck/report templates (McKinsey-style outputs)
- Pricing: $49-150/mo per consultant

**Option C: Academic Research (Current User Base)**
- Literature review automation (synthesize 100+ papers)
- Citation management (Zotero/Mendeley integration)
- Collaboration tools (co-author workflows)
- Pricing: $20-50/mo per researcher

**Option D: Healthcare Adjacent (No HIPAA Required)**
- Medical research (clinical trial docs, journal articles)
- Pharma R&D (drug development documentation)
- Healthcare consulting (non-PHI analysis)
- Pricing: $79-199/mo per user

### Vertical Launch Checklist (2-4 Weeks Per Vertical)
1. ☐ Analyze current user base (which vertical are they in?)
2. ☐ Create vertical-specific landing page (documentgpt.io/[vertical])
3. ☐ Add 3-5 vertical-specific templates
4. ☐ Build 2-3 vertical-specific features (e.g., legal clause library)
5. ☐ Adjust pricing for vertical (research lower, legal/consulting higher)
6. ☐ Launch targeted marketing campaign (LinkedIn, industry forums)
7. ☐ Measure: conversion rate, retention, feature usage by vertical
8. ☐ Double down on winning vertical or pivot to next option

---

## Competitive Positioning Matrix

| Feature | DocumentGPT (Target) | Luminance | Legora | Jenni AI |
|---------|---------------------|-----------|--------|----------|
| Document Analysis | Phase 5 Epic 1 | ✓ Strong | ✓ Good | ✗ Weak |
| Workflow Integration | Phase 5 Epic 2 | ✗ Weak | ✓ Strong | ✓ Good |
| AI Co-Writing | Phase 5 Epic 3 | ✗ None | ✓ Good | ✓ Strong |
| RAG/Semantic Search | ✓ Strong (Live) | ✓ Strong | ✓ Strong | ✓ Good |
| Team Features | Phase 5 Epic 4 | ✓ Strong | ✓ Strong | ✓ Good |
| Pricing | $15-150/mo | $$$$ | $$$ | $$ |
| Target Market | Horizontal → Vertical | Legal/Consulting | Legal | Academic |

**Competitive Advantage**: Only platform combining all three capabilities (analysis + integration + co-writing) at accessible price point.

---

## Foundation Completion Metrics

Before declaring foundation complete and choosing vertical, validate:

1. **Technical Completeness**
   - ☐ All Phase 5 epics at 80%+ completion
   - ☐ Can analyze 100-page document in <10 seconds
   - ☐ Google Docs/Word plugin functional
   - ☐ Team workspaces support 10+ users

2. **User Validation**
   - ☐ 100+ active users across multiple use cases
   - ☐ 70%+ 30-day retention rate
   - ☐ Users in at least 3 different verticals (legal, consulting, research, etc.)
   - ☐ 10+ users willing to pay $50+/mo

3. **Product-Market Fit Signals**
   - ☐ Users describe product as "document intelligence platform" not "journaling app"
   - ☐ Feature requests cluster around 1-2 verticals (indicates natural fit)
   - ☐ Word-of-mouth referrals from professional users
   - ☐ Inbound interest from teams/enterprises

4. **Business Readiness**
   - ☐ $5K+ MRR (proves willingness to pay)
   - ☐ Cost per user <30% of revenue (unit economics work)
   - ☐ Can onboard new user in <5 minutes (self-serve ready)
   - ☐ Support load <2 hours/week (product is stable)

**Decision Point**: Once all metrics hit, analyze which vertical has highest engagement/revenue/retention and go all-in on that market.

---

Maintain this file as the source of truth for execution status. Update the date header when you make changes.
