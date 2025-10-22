# DEV Environment Test Plan
**URL**: https://documentgpt.io/backup-unified.html  
**Version**: v1.2.0-dev  
**Date**: 2024-01-15

## 🎯 Phase 1 - Frontend Quick Wins

### Settings Modal
- [ ] Click ⚙️ settings button - modal opens
- [ ] Modal has Theme dropdown (Light/Dark)
- [ ] Modal has Autosave input (ms)
- [ ] Modal has Journal Mode checkbox
- [ ] Click "Save Settings" - settings persist
- [ ] Close modal with X button
- [ ] Theme changes apply immediately
- [ ] Autosave interval changes work

### Google Analytics
- [ ] Open browser DevTools Console
- [ ] Look for gtag initialization message
- [ ] Send a chat message
- [ ] Check console for `chat_sent` event
- [ ] Upload a document
- [ ] Check console for `document_uploaded` event
- [ ] Verify events include metadata (mode, file_type)

### Mobile Responsive
- [ ] Open DevTools, toggle device toolbar
- [ ] Test on iPhone SE (375px)
- [ ] Test on iPad (768px)
- [ ] Sidebar collapses properly
- [ ] Chat panel resizes correctly
- [ ] Buttons remain clickable
- [ ] Text remains readable
- [ ] No horizontal scroll

---

## 🚀 Phase 2 - Marketing Improvements

### SEO Meta Tags
- [ ] View page source (Ctrl+U)
- [ ] Verify `<meta property="og:title">` exists
- [ ] Verify `<meta property="og:description">` exists
- [ ] Verify `<meta property="og:image">` exists
- [ ] Verify `<meta property="twitter:card">` exists
- [ ] All meta tags have proper content

### Social Media Preview
- [ ] Use https://www.opengraph.xyz/ to test
- [ ] Paste https://documentgpt.io/backup-unified.html
- [ ] Verify preview shows title
- [ ] Verify preview shows description
- [ ] Note: Image won't load until og-image.png is created

---

## 🔧 Phase 3 - Backend Improvements

### Retry Logic
- [ ] Open DevTools Network tab
- [ ] Send a chat message
- [ ] Verify request succeeds
- [ ] **Simulate failure**: Turn off WiFi mid-request
- [ ] Verify error message: "Network error. Check connection."
- [ ] Turn WiFi back on
- [ ] Send another message
- [ ] Verify it retries automatically (check Network tab for multiple attempts)

### File Size Validation
- [ ] Try uploading a file >10MB
- [ ] Verify toast: "File too large (max 10MB)"
- [ ] Document should NOT be added to list
- [ ] Try uploading a file <10MB
- [ ] Verify upload succeeds

### Error Handling
- [ ] Open Console
- [ ] Trigger an upload error (invalid file)
- [ ] Check console for `console.error('Upload error:', e)`
- [ ] Verify user sees friendly error message
- [ ] Verify error doesn't crash app

### Analytics Events
- [ ] Open Console
- [ ] Send chat in Journal mode
- [ ] Verify: `gtag('event', 'chat_sent', {mode: 'journal'})`
- [ ] Send chat in Research mode
- [ ] Verify: `gtag('event', 'chat_sent', {mode: 'research'})`
- [ ] Upload PDF
- [ ] Verify: `gtag('event', 'document_uploaded', {file_type: 'application/pdf'})`

---

## ♿ Phase 4 - Polish & Accessibility

### ARIA Labels
- [ ] Right-click Upload button → Inspect
- [ ] Verify `aria-label="Upload document"`
- [ ] Check New button: `aria-label="Create new document"`
- [ ] Check Send button: `aria-label="Send message"`
- [ ] Check Mic button: `aria-label="Voice input"`
- [ ] Check Upgrade button: `aria-label="Upgrade to premium"`

### Keyboard Navigation
- [ ] Press Tab repeatedly
- [ ] Verify focus moves through all buttons
- [ ] Verify focus is visible (outline/highlight)
- [ ] Press Enter on Upload button
- [ ] Verify file picker opens
- [ ] Tab to chat input, type message
- [ ] Press Enter (not Shift+Enter)
- [ ] Verify message sends

### ARIA Expanded States
- [ ] Click + (agents) button
- [ ] Inspect button element
- [ ] Verify `aria-expanded="true"` when open
- [ ] Click again to close
- [ ] Verify `aria-expanded="false"` when closed

### Toast Notifications
- [ ] Trigger any toast (e.g., upload file)
- [ ] Inspect toast element
- [ ] Verify `role="alert"`
- [ ] Verify `aria-live="polite"`

### Reduced Motion
- [ ] Open System Preferences → Accessibility
- [ ] Enable "Reduce motion"
- [ ] Reload page
- [ ] Verify animations are minimal/instant
- [ ] Disable "Reduce motion"
- [ ] Verify animations return

---

## 🧪 Regression Testing (Existing Features)

### Core Functionality
- [ ] Create new document
- [ ] Type in editor
- [ ] Verify autosave (watch "Saved" status)
- [ ] Upload PDF
- [ ] Verify transparent loading overlay
- [ ] Chat with AI
- [ ] Toggle Journal/Research mode
- [ ] Use voice input (mic button)
- [ ] Check DocIQ score updates
- [ ] View version history
- [ ] Switch between documents
- [ ] Search documents
- [ ] Delete document
- [ ] Export document (txt/pdf/html)

### UI Elements
- [ ] Open agents menu (+)
- [ ] Run each agent (Summary, Email, etc.)
- [ ] Toggle dark mode
- [ ] Toggle focus mode
- [ ] Use find & replace
- [ ] Format text (Bold, Italic, Lists)
- [ ] Check usage bars update
- [ ] Click Upgrade button

---

## 🐛 Bug Checks

### Common Issues
- [ ] No console errors on page load
- [ ] No console errors when uploading
- [ ] No console errors when chatting
- [ ] No broken images
- [ ] No layout shifts
- [ ] Buttons don't overlap
- [ ] Text is readable in both themes
- [ ] Modals close properly
- [ ] No memory leaks (check DevTools Memory)

### Edge Cases
- [ ] Upload 0-byte file
- [ ] Upload very long filename
- [ ] Type 10,000 words in editor
- [ ] Send empty chat message (should do nothing)
- [ ] Rapid-click buttons (no duplicate actions)
- [ ] Resize window while modal open
- [ ] Switch tabs while uploading

---

## ✅ Pass Criteria

**Phase 1**: 8/8 tests pass  
**Phase 2**: 6/6 tests pass  
**Phase 3**: 8/8 tests pass  
**Phase 4**: 10/10 tests pass  
**Regression**: 25/25 tests pass  
**Bugs**: 0 critical, <3 minor  

**Overall**: 57/57 tests pass = ✅ Ready for STG

---

## 📝 Test Results

### Tester: _____________
### Date: _____________
### Browser: _____________
### OS: _____________

**Phase 1**: ___/8 ✅  
**Phase 2**: ___/6 ✅  
**Phase 3**: ___/8 ✅  
**Phase 4**: ___/10 ✅  
**Regression**: ___/25 ✅  
**Bugs Found**: ___

### Notes:
```
[Add any issues, observations, or recommendations here]
```

### Decision:
- [ ] ✅ PASS - Promote to STG
- [ ] ⚠️ CONDITIONAL PASS - Minor fixes needed
- [ ] ❌ FAIL - Major issues, needs rework

---

## 🚀 Next Steps After Testing

1. **If PASS**: Copy features to STG (backup.html)
2. **If CONDITIONAL**: Fix minor issues, re-test
3. **If FAIL**: Review bugs, fix, full re-test

**Promotion Command**:
```bash
# After testing passes, promote to STG
aws s3 cp web/backup-unified.html s3://documentgpt-website-prod/backup.html
```
