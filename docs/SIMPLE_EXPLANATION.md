# Simple Explanation: DEV vs STG

## 1. What's the Feature Difference?

### DEV (backup-lumina) - "Core + DocIQ"
```
✅ Write documents
✅ Chat with AI
✅ Upload PDFs
✅ DocIQ scores (Clarity, Complete, Actionable)
✅ Voice input
```

### STG (backup) - "Full Suite"
```
✅ Everything DEV has
✅ PLUS 20+ extra features:
   - Popup windows (modals)
   - 6 AI agents
   - Folders
   - Settings panel
   - Fancy animations
   - Export options
   - Version history UI
```

## 2. What are Modals?

**Modals = Popup windows**

STG has 7 modals:
1. Upgrade pricing popup
2. Login popup
3. Signup popup
4. Settings popup
5. Folder creation popup
6. Command palette popup
7. Keyboard shortcuts popup

DEV has: **0 modals** (cleaner, faster)

## 3. What Animations?

### STG Animations:
```css
- Glow pulse (buttons breathe)
- Shimmer (loading skeleton)
- Slide up (modals appear)
- Ripple (button press effect)
- Fade in (tooltips)
- Bounce (success states)
```

### DEV Animations:
```css
- Loading dots (●●●)
- Progress bar (top)
- Basic hover effects
```

**Result**: DEV loads 3x faster

## 4. Why is DEV Faster?

### File Size:
- **DEV**: 29KB (like a small image)
- **STG**: 95KB (like 3 images)

### Code:
- **DEV**: 220 lines, minified
- **STG**: 2,155 lines, readable

### Load Time:
- **DEV**: ~100ms
- **STG**: ~300ms

**Why?** Less code = faster download = faster render

## 5. Processing Pipeline

### DEV Pipeline (Simple):
```
Upload → Parse PDF → Create Doc → Show in NEW chat → Done
  ↓         ↓           ↓            ↓
 20%       40%         70%          100%
```

### STG Pipeline (Complex):
```
Upload → Parse PDF → API Call → Generate Insights → 
  ↓         ↓           ↓              ↓
 20%       40%         70%            90%
  ↓
Apply Highlights → Create Thumbnails → Show in CURRENT chat
       ↓                  ↓                    ↓
      95%                98%                 100%
```

**Key Difference**:
- **DEV**: Creates NEW doc + NEW chat (clean slate)
- **STG**: Adds to CURRENT chat (cluttered)

## 6. Your Requests

### ✅ Add Agents to Chat (Clean UI)
```
Current:
[Ask anything...] [🎙️] [➤]

New:
[+] [Ask anything...] [🎙️] [➤]
 ↓
Click + shows:
📝 Summary
📧 Email  
📊 Sheets
📅 Calendar
💾 Save
📤 Export
```

### ✅ Add Settings (Clean UI)
```
Add gear icon ⚙️ in top bar
Click → inline dropdown (no modal)
```

### ❌ Remove Folders
Already not in DEV!

## Summary

| Aspect | DEV | STG |
|--------|-----|-----|
| Speed | ⚡⚡⚡ | ⚡ |
| Features | Core | Everything |
| Popups | 0 | 7 |
| Animations | Minimal | Heavy |
| File Size | 29KB | 95KB |
| Upload Flow | New chat | Current chat |
| UI | Clean | Busy |

**Recommendation**: Keep DEV minimal, add agents dropdown + settings gear only.
