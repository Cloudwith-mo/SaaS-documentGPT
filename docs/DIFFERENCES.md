# Differences: backup-lumina (dev) vs backup (stg)

## File Stats
- **backup-lumina.html**: 29KB, 220 lines (DEV - minimalist)
- **backup.html**: 95KB, 2,155 lines (STG - full-featured)

## Key Differences

### 1. Code Size & Complexity
**backup-lumina (dev)**:
- Ultra-compact, minified JavaScript
- Minimal CSS (inline only)
- ~70% smaller file size

**backup (stg)**:
- Extensive CSS animations & effects
- Detailed comments & documentation
- Full feature set with modals

### 2. Features Present in STG (backup.html) ONLY

#### UI Components:
- ✅ Folders system (create/manage folders)
- ✅ Command palette (⌘K)
- ✅ Settings modal (theme, autosave, DND, journal mode)
- ✅ Health dashboard button
- ✅ Upgrade modal with 3 pricing tiers
- ✅ Login/Signup modals with full auth flow
- ✅ Keyboard shortcuts overlay
- ✅ Version history with restore
- ✅ Insights panel with drag & drop
- ✅ Highlight navigation (prev/next)
- ✅ Quick actions (shorter, longer, explain, copy)
- ✅ PDF page thumbnails menu
- ✅ Zoom controls (+/-)
- ✅ Find/replace functionality
- ✅ 6 AI agents (summary, email, sheets, calendar, save, export)
- ✅ Export format selection (PDF/TXT/HTML)
- ✅ Undo delete (5s window)
- ✅ Mobile hamburger menu
- ✅ Offline banner
- ✅ Error boundary

#### Styling:
- ✅ Advanced animations (glow, pulse, shimmer, slideUp)
- ✅ Tooltips on hover
- ✅ Button ripple effects
- ✅ Progress bar for operations
- ✅ Loading skeletons
- ✅ Dark mode support
- ✅ Mobile responsive breakpoints
- ✅ PDF reader styling

### 3. Features in BOTH

#### Core Functionality:
- ✅ Document creation/deletion
- ✅ Editor with formatting (bold, italic, underline, lists)
- ✅ Chat with AI
- ✅ File upload (PDF/TXT/DOCX)
- ✅ Usage tracking (chats/docs)
- ✅ Tab management
- ✅ Search documents
- ✅ Theme toggle
- ✅ Focus mode
- ✅ Autosave
- ✅ LocalStorage persistence
- ✅ Cloud sync (for logged-in users)

### 4. Features in DEV (backup-lumina.html) ONLY

#### DocIQ Metrics:
- ✅ Clarity percentage
- ✅ Completeness percentage  
- ✅ Actionability percentage
- ✅ Tips button (shows improvement suggestions)

#### Voice Input:
- ✅ Microphone button (🎙️)
- ✅ Speech recognition support

#### Enhanced Upload Flow (NEW):
- ✅ Creates new document immediately
- ✅ Shows loading in NEW chat (not current)
- ✅ Pro PDF view with better styling
- ✅ Cleaner error handling

### 5. Architecture Differences

**backup-lumina (dev)**:
```javascript
// Minified, single-line functions
// No modals, inline everything
// Minimal dependencies
// Fast load time
```

**backup (stg)**:
```javascript
// Readable, well-commented code
// Modular functions
// Multiple modal systems
// Feature-rich but heavier
```

## Summary Table

| Feature | backup-lumina (dev) | backup (stg) |
|---------|---------------------|--------------|
| File Size | 29KB | 95KB |
| Load Speed | ⚡ Fast | 🐢 Slower |
| Features | 🎯 Core + DocIQ | 🎨 Full Suite |
| Modals | ❌ None | ✅ 7+ modals |
| Animations | ⚡ Minimal | 🎭 Extensive |
| Mobile | ✅ Basic | ✅ Advanced |
| Voice Input | ✅ Yes | ❌ No |
| DocIQ Metrics | ✅ Yes | ❌ No |
| Folders | ❌ No | ✅ Yes |
| Agents | ❌ No | ✅ 6 agents |
| Settings | ❌ No | ✅ Full modal |
| Version History | ✅ Basic | ✅ Advanced |

## Recommendation

**Use backup-lumina (dev) for**:
- Fast prototyping
- Mobile-first experience
- Minimal feature set
- Quick load times
- DocIQ testing

**Use backup (stg) for**:
- Production deployment
- Full feature showcase
- Desktop experience
- Marketing/demos
- Complete user workflows

## Migration Path

To bring STG features to DEV:
1. Add modals system (lightweight)
2. Add AI agents (6 buttons)
3. Add folders (optional)
4. Keep DocIQ metrics (unique to DEV)
5. Keep voice input (unique to DEV)
6. Maintain small file size (<50KB)
