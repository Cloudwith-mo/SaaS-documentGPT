# DocumentGPT Gamification Roadmap

## 🎯 North Star Metric
**Weekly Active Writers (WAW)**: Users who produce ≥1 saved/exported doc (≥200 words) OR upload file with ≥1 Instant Insight accepted

**Activation Event**: First "Aha!" within 10 minutes
- Clarity +15% improvement OR
- ≥1 Instant Insight accepted and saved

**Ethical Guardrails**:
- ✅ Opt-in for streaks/notifications
- ✅ Visible "pause gamification" toggle
- ✅ Session caps with break nudges

---

## 🔄 Core Loop (Hook Model)

**Trigger** → **Action** → **Variable Reward** → **Investment**

1. **Trigger**: Daily prompt "Pick a doc to sharpen"
2. **Action**: Write/upload → Run Instant Insights → Apply 1-3 tips
3. **Variable Reward**: Clarity/Actionable jump + Insight Cards + XP + Mini-Powers
4. **Investment**: Save to Library + Tag doc + Schedule reminder

---

## 📊 Progression Systems

### A) Levels via DocIQ
- **DocIQ as ELO**: Weighted mix of Clarity/Actionable/Complete deltas
- **Levels**: Every ~50 DocIQ points (Researcher 1 → 2 → 3...)
- **Progress Ring**: "+34 DocIQ to Level 4" at editor top

### B) Streaks (Opt-in)
- Count Focus sessions (25-min sprints) or docs improved
- **Streak Freeze**: 1 grace day per week

### C) Insight Cards (Collectibles)
- Each accepted Instant Insight → Card saved to Tips shelf
- **Sets**: Clarity, Structure, Tone (give passive bonuses)
- **Rare Cards**: 1-3% chance for variability

### D) Skill Tree (Unlockables)
**Tracks**: Clarity, Actionability, Structure, Speed

**Mini-Powers**:
- 🎯 Auto-Outline (1-click headings)
- 📚 Evidence Finder (suggest citations)
- 🎨 Tone Dial
- 📝 Boilerplate Snippets

### E) Badges (Challenge-gated)
- "First Export"
- "Three-Insight Combo"
- "From 0 → 60% Clarity"
- "Focus Marathon (5 sessions)"

---

## 🎮 Quests & Challenges

### Day 0-1: Golden Path (5-7 min)
1. Paste/upload file → +50 XP
2. Run Instant Insights → Accept 1 tip → +30 XP
3. Hit Save → +20 XP
4. Complete first Focus sprint (10-15 min) → +50 XP + 1 Insight Card
5. **Reward**: Hit Level 2, unlock Auto-Outline

### Day 2-7: Habit Seed
**Daily Micro-Quests** (choose 2 of 4):
- Raise Clarity +10% on any doc
- Accept 3 tips in one session
- Export an email draft
- Organize 2 docs in Library with tags

**Weekly Quest**: "Improve 3 docs and export 1"
- **Reward**: Rare Insight Card + Tone Dial trial

### Day 8-30: Mastery Arcs
- **Boss Quest**: Take doc from Clarity <40% to >75% in two sessions
- **Speed Run**: Improve doc by +20% in <15 min
- **Collections**: Complete "Actionable Advice" card set → unlock Evidence Finder

---

## 👥 Social & Cooperative (Opt-in)

- **Team Scoreboard**: DocIQ gains, boss-quests cleared, exports shipped
- **Pair Quests**: "You polish mine; I polish yours"
- **Ghost Race**: Race against your past best session
- **Seasonal Events**: Monthly DocJam (48-hour community challenge)

---

## 💰 Rewards & Economy

- **XP**: ~150-250 XP per session → 3-4 sessions per level early
- **DocIQ**: Weighted moving average of improvement metrics
- **Insight Cards**: 1 guaranteed per session if ≥2 tips accepted
- **Cosmetics**: Premium themes/frames only (no pay-to-win)

---

## 📈 In-Session Feedback

**Before**: Baseline gauges greyed with "+X to next level" hint

**During**: Each tip animates progress ring tick + DocIQ +n toast

**After**: Session recap
```
"You raised Clarity +22%, earned 180 XP, unlocked Auto-Outline."
```

**Focus Mode**: Minimal UI + timer chip + "2 to go for streak freeze"

---

## 🔔 Notifications & Prompts (MAP-aligned)

- **Signal** (low effort): "1-click to improve headings on Draft_v3"
- **Spark** (motivation): "You're 30 DocIQ from Researcher 3. One 15-min sprint!"
- **Facilitator** (ability): Surface Auto-Outline when time-pressed

---

## 📊 Measurement Plan

### Core Events
```javascript
doc_uploaded, text_pasted, instant_insights_shown, 
tip_accepted, tip_dismissed, focus_started, focus_completed,
save_clicked, export_clicked, clarity_score, actionable_score,
complete_score, words_counted, doc_tagged, library_opened,
card_awarded, level_up, streak_extended
```

### Properties
```javascript
doc_length, domain, time_in_session, delta_clarity,
delta_actionable, delta_complete, docIQ_before, docIQ_after,
cards_total, streak_length
```

### Dashboards
- Time-to-First-Insight
- % sessions with ≥1 tip accepted
- D1/D7/D30 retention
- NSM funnel
- Streak opt-in rate
- DocIQ delta per feature

---

## 🧪 Experiments to Run

1. **Progress ring vs numeric DocIQ** → measure tip acceptance rate
2. **Streak on by default vs opt-in** → measure D7 retention
3. **Card rarity: 1% vs 3%** → measure session length
4. **Skill tree unlock order** → measure export rate
5. **Prompt types (Signal vs Spark)** → measure session starts

---

## 📅 12-Week Build Plan

### Weeks 1-2: Instrument & Define ✅ (CURRENT)
- [x] Ship analytics events
- [x] NSM dashboard
- [x] DocIQ v0.1 (weighted deltas)
- [ ] Add opt-in for notifications & streaks

### Weeks 3-4: Core Loop ✅ (COMPLETED)
- [x] Instant Insights → Tip acceptance flow
- [x] Session recap with XP + progress ring
- [x] Daily trigger prompt system
- [x] Tip acceptance with Apply buttons
- [x] Variable rewards (Insight Cards)
- [x] Investment (Library with tags)

### Weeks 5-6: Collections & Quests
- [ ] Insight Cards system
- [ ] Golden Path onboarding questline
- [ ] Day 2-7 daily quests

### Weeks 7-8: Focus & Streaks
- [ ] 25-minute Focus timer
- [ ] Streak freeze mechanic
- [ ] Break nudges

### Weeks 9-10: Social
- [ ] Private team scoreboard
- [ ] Pair quests
- [ ] Ghost race

### Weeks 11-12: Balance & A/B
- [ ] Tune XP, rarity, unlock pacing
- [ ] Run 5 experiments
- [ ] Finalize copy

---

## 📝 Copy & Placements

**Editor Header**:
```
DocIQ 143 · Researcher 2 · 34→L3
```

**Right Rail Recap**:
```
+22% Clarity, +13% Actionable. 180 XP earned. New: Auto-Outline.
```

**Card Award Toast**:
```
You found Structure: Pyramid Intro. Add to Tips?
```

**Quest Chip**:
```
Improve any doc by +10% Clarity (1/1) — Reward: 50 XP
```

---

## 🎯 Why This Works

**Hook Model**: Trigger → Action → Variable Reward → Investment (habit loop)

**Fogg Behavior Model**: Prompts match ability × motivation (useful, not naggy)

**Octalysis**: Diversifies motivation beyond points (creativity, accomplishment, social meaning)

---

## 🚀 Current Status

**Implemented**:
- ✅ Basic XP system (+5 new doc, +3 chat, +10 per 100 words)
- ✅ Level progression (100 XP per level)
- ✅ Streak tracking (daily activity)
- ✅ DocIQ scoring (Clarity/Complete/Actionable)
- ✅ XP celebration popups
- ✅ Progress bar in sidebar

**Next Priority** (Week 1-2):
1. Progress ring in editor header
2. Session recap modal
3. Opt-in toggle for gamification
4. Enhanced analytics events
5. DocIQ as weighted moving average

---

## 📚 References

- Hook Model: Nir Eyal
- Fogg Behavior Model: BJ Fogg
- Octalysis Framework: Yu-kai Chou
- NSM: Amplitude Product Analytics
