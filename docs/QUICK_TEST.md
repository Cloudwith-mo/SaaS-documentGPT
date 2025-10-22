# Quick Test Checklist (5 Minutes)

**URL**: https://documentgpt.io/backup-unified.html

## 🚀 Critical Path (Must Work)

1. **Page Loads**
   - [ ] No console errors
   - [ ] All UI elements visible

2. **Settings Modal** (Phase 1)
   - [ ] Click ⚙️ → Modal opens
   - [ ] Change theme → Saves

3. **Upload Document** (Phase 3)
   - [ ] Upload small PDF (<10MB)
   - [ ] Transparent loading overlay shows
   - [ ] Document appears in list

4. **Chat** (Phase 3)
   - [ ] Send message
   - [ ] AI responds
   - [ ] Check console for `chat_sent` event

5. **Accessibility** (Phase 4)
   - [ ] Tab through buttons
   - [ ] Focus visible
   - [ ] Upload button has aria-label

6. **Mobile** (Phase 1)
   - [ ] Open DevTools mobile view
   - [ ] Layout doesn't break

## ✅ Result
- [ ] All 6 pass → **READY FOR STG**
- [ ] Any fail → **CHECK DEV_TEST_PLAN.md**
