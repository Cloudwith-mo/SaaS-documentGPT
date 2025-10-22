# Manual Test Checklist for DocumentGPT

## Test URL
https://documentgpt.io/backup.html

## Critical User Flows

### 1. Document Management ✓
- [ ] Click "New" button → Creates new document
- [ ] Click "Upload" button → Opens file picker
- [ ] Click document in sidebar → Switches to that document
- [ ] Click X on tab → Deletes document (with confirmation)

### 2. Editor Functionality ✓
- [ ] Type in editor → Word count updates
- [ ] Click Bold (B) → Text becomes bold
- [ ] Click Italic (I) → Text becomes italic
- [ ] Click Underline (U) → Text becomes underlined
- [ ] Select font size → Text size changes
- [ ] Click bullet list → Creates bullet list
- [ ] Click numbered list → Creates numbered list

### 3. Chat & AI ✓
- [ ] Type message in chat → Click send → Message appears
- [ ] Chat shows loading indicator while processing
- [ ] Bot response appears after API call
- [ ] Quick actions appear after bot response

### 4. AI Agents ✓
- [ ] Click 📝 (Summary) → Shows summary request
- [ ] Click 📧 (Email) → Shows email agent
- [ ] Click 📊 (Sheets) → Shows CSV extraction
- [ ] Click 📅 (Calendar) → Shows calendar event
- [ ] Click 💾 (Save) → Saves document
- [ ] Click 📤 (Export) → Shows export options

### 5. UI Controls ✓
- [ ] Click theme button (🌞/🌙) → Toggles dark/light mode
- [ ] Click focus button (👁️) → Hides sidebars
- [ ] Click + zoom → Editor zooms in
- [ ] Click - zoom → Editor zooms out
- [ ] Click ⌘K button → Opens command palette
- [ ] Click ⚙️ button → Opens settings modal
- [ ] Click 📊 button → Opens health dashboard

### 6. Search & Navigation ✓
- [ ] Type in find box → Click 🔍 → Highlights matches
- [ ] Type in doc search → Filters document list
- [ ] Click version history (🕐) → Shows versions

### 7. Modals & Overlays ✓
- [ ] Click "Upgrade" → Shows pricing modal
- [ ] Click "Login" → Shows login modal
- [ ] Click "Sign Up" → Shows signup modal
- [ ] Press Escape → Closes any open modal
- [ ] Press ? → Shows keyboard shortcuts

### 8. Mobile Responsiveness ✓
- [ ] Resize to mobile → Hamburger menu appears
- [ ] Click hamburger → Sidebar slides in
- [ ] Click outside → Sidebar closes

## Automated Test

Run this in browser console:

```javascript
// Copy contents of test_user_flow.js and paste here
```

## Expected Results

All buttons should:
1. Be clickable (cursor changes to pointer)
2. Show visual feedback on hover
3. Execute their intended action
4. Not throw console errors

## Common Issues to Check

- [ ] No console errors on page load
- [ ] All buttons have hover effects
- [ ] Modals open and close properly
- [ ] State persists in localStorage
- [ ] Chat messages appear correctly
- [ ] Editor is editable (not read-only)

## Performance Checks

- [ ] Page loads in < 2 seconds
- [ ] No layout shifts on load
- [ ] Smooth animations (no jank)
- [ ] Autosave works (check "Saved" status)

## Browser Compatibility

Test in:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile Safari (iOS)
- [ ] Mobile Chrome (Android)

## Notes

- Guest users have 50 chat limit, 10 doc limit
- Some features require backend API (may show errors if API is down)
- PDF uploads require valid PDF files
- Export requires jsPDF library to be loaded
