# PRD Enhancement Plan

## Current Status

**PRD (index.html)** already has:
- ✅ Open Graph meta tags
- ✅ Twitter Card tags  
- ✅ Transparent loading overlay
- ✅ Settings modal with journalMode
- ✅ ARIA labels on some buttons
- ✅ Smart highlights
- ✅ Version history
- ✅ All 6 AI agents

## Missing from PRD (Available in DEV)

### Phase 1 - Frontend
- ❌ Google Analytics tracking
- ❌ Enhanced mobile responsive CSS
- ❌ Reduced motion support

### Phase 2 - Marketing
- ✅ Already has Open Graph (DONE)
- ✅ Already has Twitter Cards (DONE)

### Phase 3 - Backend
- ❌ Retry logic for failed requests (2x with backoff)
- ❌ File size validation (10MB limit)
- ❌ Analytics event tracking (gtag events)
- ❌ Better error logging (console.error)

### Phase 4 - Polish
- ❌ More ARIA labels (mic, agents menu)
- ❌ aria-expanded states
- ❌ aria-live for toasts
- ❌ Reduced motion CSS

## Smart Processing Comparison

| Feature | DEV | PRD | Notes |
|---------|-----|-----|-------|
| **DocIQ Score** | ✅ | ❌ | DEV shows DocIQ in bottom bar |
| **Mode Toggle** | ✅ | ✅ | Both have Journal/Research |
| **Voice Input** | ✅ | ❌ | DEV has mic button |
| **Retry Logic** | ✅ | ❌ | DEV auto-retries failed requests |
| **Analytics** | ✅ | ❌ | DEV tracks events |
| **File Validation** | ✅ | ❌ | DEV checks 10MB limit |

## Recommendation

**Add to PRD:**
1. Google Analytics (gtag)
2. Retry logic in sendChat()
3. File size validation in handleFileUpload()
4. DocIQ score display
5. Voice input button
6. Enhanced ARIA labels
7. Reduced motion CSS

**Keep in PRD (don't remove):**
- All existing modals
- Full formatting toolbar
- Zoom controls
- Command palette
- All current features

## Implementation Strategy

**Option 1: Selective Enhancement (RECOMMENDED)**
- Add only Phase 1-4 improvements to PRD
- Keep PRD's full feature set
- Result: PRD = Full features + DEV enhancements

**Option 2: Replace with DEV**
- Copy DEV to PRD
- Lose: Modals, advanced formatting, zoom
- Gain: Cleaner UI, smaller file size
- Result: PRD = Lumina UI only

**I recommend Option 1** - Keep PRD's power features, add DEV's polish.

## Files to Modify

1. `web/index.html` - Add enhancements
2. Deploy to S3 production

## Estimated Changes

- ~50 lines of code
- Add Google Analytics script
- Add retry logic to sendChat()
- Add file validation to handleFileUpload()
- Add ARIA labels
- Add reduced motion CSS
- Add DocIQ display (optional)
- Add voice input (optional)

## Testing Checklist

After adding to PRD:
- [ ] Google Analytics fires
- [ ] Retry logic works (test offline)
- [ ] File size validation works
- [ ] ARIA labels present
- [ ] Reduced motion works
- [ ] All existing features still work
- [ ] No console errors
