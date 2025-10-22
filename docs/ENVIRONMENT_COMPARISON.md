# Environment Feature Comparison

## 📊 File Stats

| Environment | File | Size | Lines | IDs | Status |
|------------|------|------|-------|-----|--------|
| **DEV** | backup-unified.html | 40KB | 288 | 49 | ❌ BROKEN |
| **STG** | backup.html | 95KB | 2,199 | 90 | ✅ WORKING |
| **PRD** | index.html | 95KB | 2,188 | 90 | ✅ WORKING |

## 🐛 DEV Issues Found

### Critical Bug
- **Error**: References `darkModeToggle` element that doesn't exist
- **Line**: `document.getElementById('darkModeToggle').checked=isDark;`
- **Impact**: JavaScript crashes on page load
- **Fix**: Remove this line (theme toggle works via themeBtn)

## 🎯 Feature Differences

### DEV (backup-unified.html) - Lumina UI
**Has:**
- ✅ Lumina clean UI design
- ✅ DocIQ metrics (Clarity/Complete/Actionable)
- ✅ Mode toggle (Journal/Research)
- ✅ Voice input (mic button)
- ✅ Transparent loading overlay
- ✅ Agent dropdown menu
- ✅ Settings modal
- ✅ Google Analytics
- ✅ Open Graph meta tags
- ✅ Retry logic
- ✅ ARIA labels
- ✅ File size validation

**Missing:**
- ❌ Login/Signup modals
- ❌ Upgrade modal
- ❌ Folders modal
- ❌ Command Palette (⌘K)
- ❌ Keyboard shortcuts modal
- ❌ Advanced formatting (align, colors)
- ❌ Zoom controls
- ❌ Full version history UI

**Simplified:**
- Fewer buttons (cleaner UI)
- Consolidated agents into dropdown
- Minimal modals

### STG (backup.html) - Full Featured
**Has:**
- ✅ All DEV features PLUS:
- ✅ Full modal system (7 modals)
- ✅ Login/Signup/Upgrade flows
- ✅ Folder management
- ✅ Command Palette (⌘K)
- ✅ Keyboard shortcuts help
- ✅ Advanced formatting toolbar
- ✅ Zoom controls (80-150%)
- ✅ Full version history UI
- ✅ More comprehensive settings

**Trade-offs:**
- More complex UI
- More buttons
- Larger file size (95KB vs 40KB)

### PRD (index.html) - Production Stable
**Same as STG** but:
- Missing Phase 1-4 improvements
- No Google Analytics
- No Open Graph tags
- No retry logic
- No ARIA labels
- No file size validation

## 🎨 UI Philosophy

### DEV (Lumina)
- **Goal**: Simplicity is king
- **Approach**: Minimal buttons, clean design
- **Target**: Individual productivity focus
- **Size**: Ultra-lean (40KB)

### STG/PRD (Full)
- **Goal**: Feature completeness
- **Approach**: All features available
- **Target**: Power users
- **Size**: Full-featured (95KB)

## 🚀 Recommendation

**Option 1: Fix DEV Bug, Keep Lumina**
- Remove `darkModeToggle` reference
- Keep clean Lumina UI
- Add missing critical features only

**Option 2: Merge STG → DEV**
- Copy STG to DEV
- Add Phase 1-4 improvements to STG
- Abandon Lumina UI

**Option 3: Two Product Lines**
- DEV = Lumina (simple, 40KB)
- STG/PRD = Full (complete, 95KB)
- Maintain both separately

## 🔧 Quick Fix for DEV

```javascript
// REMOVE this line (line ~288):
document.getElementById('darkModeToggle').checked=isDark;

// Theme toggle already works via themeBtn
```

## 📋 Next Steps

1. **Immediate**: Fix DEV bug
2. **Decide**: Which UI philosophy to pursue?
3. **Test**: Verify DEV works after fix
4. **Promote**: Move working version to STG
