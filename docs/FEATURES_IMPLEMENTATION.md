# DocumentGPT Features Implementation Guide

## 🎯 R1: Enhanced Smart Highlights (PRIORITY 1)

### What It Does
- **5 highlight colors**: Yellow (facts), Blue (dates), Green (names), Red (important), Purple (ideas)
- **Floating toolbar**: Appears when text is selected
- **Legend sidebar**: Shows all highlights with categories
- **Click to edit**: Click highlight to change category/color
- **Export**: Generate document with all highlights

### Implementation Steps

1. **Add CSS** (in `<style>` section before `</style>`):
```css
/* R1: Enhanced Smart Highlights */
.highlight-yellow { background: linear-gradient(120deg, #fef3c7 0%, #fde68a 100%); padding: 2px 4px; border-radius: 3px; cursor: pointer; }
.highlight-blue { background: linear-gradient(120deg, #dbeafe 0%, #bfdbfe 100%); padding: 2px 4px; border-radius: 3px; cursor: pointer; }
.highlight-green { background: linear-gradient(120deg, #d1fae5 0%, #a7f3d0 100%); padding: 2px 4px; border-radius: 3px; cursor: pointer; }
.highlight-red { background: linear-gradient(120deg, #fecaca 0%, #fca5a5 100%); padding: 2px 4px; border-radius: 3px; cursor: pointer; }
.highlight-purple { background: linear-gradient(120deg, #e9d5ff 0%, #d8b4fe 100%); padding: 2px 4px; border-radius: 3px; cursor: pointer; }

#selectionToolbar {
    position: absolute;
    display: none;
    background: rgba(255,255,255,0.98);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(16,185,129,0.25);
    border-radius: 12px;
    padding: 8px;
    box-shadow: 0 8px 28px rgba(16,185,129,0.2);
    z-index: 1001;
    gap: 4px;
}
#selectionToolbar.visible { display: flex; }
#selectionToolbar button {
    padding: 6px 10px;
    border-radius: 8px;
    border: 1px solid rgba(16,185,129,0.2);
    background: white;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}
#selectionToolbar button:hover {
    background: #f0fdf4;
    transform: translateY(-1px);
}

#highlightLegend {
    position: fixed;
    right: 420px;
    top: 80px;
    width: 280px;
    max-height: 500px;
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(16,185,129,0.2);
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(16,185,129,0.15);
    overflow: hidden;
    display: none;
    flex-direction: column;
    z-index: 85;
}
#highlightLegend.visible { display: flex; }
.legend-item {
    padding: 10px 12px;
    border-bottom: 1px solid rgba(16,185,129,0.1);
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 8px;
}
.legend-item:hover { background: rgba(16,185,129,0.05); }
.legend-color {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    flex-shrink: 0;
}
.legend-text {
    flex: 1;
    font-size: 12px;
    line-height: 1.4;
}
.legend-actions {
    display: flex;
    gap: 4px;
}
.legend-actions button {
    padding: 2px 6px;
    font-size: 10px;
    border-radius: 4px;
    border: 1px solid rgba(16,185,129,0.3);
    background: white;
    cursor: pointer;
}
.legend-actions button:hover { background: #f0fdf4; }
```

2. **Add HTML** (before `<!-- Progress Bar -->`):
```html
<!-- R1: Selection Toolbar -->
<div id="selectionToolbar">
    <button onclick="highlightSelection('yellow')" title="Facts">💛</button>
    <button onclick="highlightSelection('blue')" title="Dates">💙</button>
    <button onclick="highlightSelection('green')" title="Names">💚</button>
    <button onclick="highlightSelection('red')" title="Important">❤️</button>
    <button onclick="highlightSelection('purple')" title="Ideas">💜</button>
    <button onclick="removeHighlight()" title="Remove">🚫</button>
</div>

<!-- R1: Highlight Legend -->
<div id="highlightLegend">
    <div class="px-4 py-3 border-b flex items-center justify-between" style="background: linear-gradient(135deg, rgba(16,185,129,0.08), rgba(6,182,212,0.08));">
        <span class="text-sm font-bold text-emerald-700">🎨 Highlights</span>
        <button onclick="toggleHighlightLegend()" class="text-emerald-600 text-xl opacity-80 hover:opacity-100">×</button>
    </div>
    <div id="legendContent" class="flex-1 overflow-auto p-2"></div>
    <div class="px-4 py-3 border-t flex gap-2">
        <button onclick="exportHighlights()" class="flex-1 text-xs px-3 py-2 rounded-lg border border-emerald-500 text-emerald-600 hover:bg-emerald-50">📥 Export</button>
        <button onclick="clearAllHighlights()" class="flex-1 text-xs px-3 py-2 rounded-lg border border-red-500 text-red-600 hover:bg-red-50">🗑️ Clear</button>
    </div>
</div>
```

3. **Add Button to Right Sidebar** (after `focusBtn`):
```html
<button id="highlightLegendBtn" class="text-xs px-2 py-1 rounded-lg border hover:bg-gray-50" data-tooltip="Highlights" title="Show highlights">🎨</button>
```

4. **Add JavaScript** (before `// Initialize` at the end):
```javascript
// === R1: ENHANCED SMART HIGHLIGHTS ===
if (!state.userHighlights) state.userHighlights = {};

function handleTextSelection() {
    setTimeout(() => {
        const sel = window.getSelection();
        const toolbar = document.getElementById('selectionToolbar');
        
        if (!sel || sel.isCollapsed || sel.toString().trim().length === 0) {
            toolbar.classList.remove('visible');
            return;
        }
        
        const editor = document.getElementById('editor');
        if (!editor.contains(sel.anchorNode)) {
            toolbar.classList.remove('visible');
            return;
        }
        
        const range = sel.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        
        toolbar.style.left = `${rect.left + (rect.width / 2) - 150}px`;
        toolbar.style.top = `${rect.top - 50}px`;
        toolbar.classList.add('visible');
    }, 10);
}

window.highlightSelection = (color) => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) return;
    
    const text = sel.toString().trim();
    if (!text) return;
    
    const range = sel.getRangeAt(0);
    const span = document.createElement('span');
    span.className = `highlight-${color}`;
    span.setAttribute('data-highlight-id', Date.now());
    span.setAttribute('data-color', color);
    
    try {
        range.surroundContents(span);
    } catch (e) {
        const fragment = range.extractContents();
        span.appendChild(fragment);
        range.insertNode(span);
    }
    
    if (!state.userHighlights[state.activeId]) state.userHighlights[state.activeId] = [];
    state.userHighlights[state.activeId].push({
        id: span.getAttribute('data-highlight-id'),
        text: text,
        color: color,
        timestamp: Date.now()
    });
    
    saveState();
    updateHighlightLegend();
    document.getElementById('selectionToolbar').classList.remove('visible');
    toast(`✨ Highlighted in ${color}`, true);
};

window.removeHighlight = () => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) return;
    
    let node = sel.anchorNode;
    while (node && node !== document.getElementById('editor')) {
        if (node.nodeType === 1 && node.className && node.className.includes('highlight-')) {
            const id = node.getAttribute('data-highlight-id');
            const parent = node.parentNode;
            while (node.firstChild) {
                parent.insertBefore(node.firstChild, node);
            }
            parent.removeChild(node);
            
            if (state.userHighlights[state.activeId]) {
                state.userHighlights[state.activeId] = state.userHighlights[state.activeId].filter(h => h.id !== id);
            }
            
            saveState();
            updateHighlightLegend();
            toast('Highlight removed', true);
            break;
        }
        node = node.parentNode;
    }
    
    document.getElementById('selectionToolbar').classList.remove('visible');
};

window.toggleHighlightLegend = () => {
    const legend = document.getElementById('highlightLegend');
    legend.classList.toggle('visible');
    if (legend.classList.contains('visible')) {
        updateHighlightLegend();
    }
};

function updateHighlightLegend() {
    const highlights = state.userHighlights[state.activeId] || [];
    const content = document.getElementById('legendContent');
    
    if (highlights.length === 0) {
        content.innerHTML = '<div class="text-center py-8 text-sm text-gray-500">No highlights yet.<br>Select text to highlight.</div>';
        return;
    }
    
    const colorNames = {
        yellow: '💛 Facts',
        blue: '💙 Dates',
        green: '💚 Names',
        red: '❤️ Important',
        purple: '💜 Ideas'
    };
    
    content.innerHTML = highlights.map(h => `
        <div class="legend-item" onclick="scrollToHighlight('${h.id}')">
            <div class="legend-color highlight-${h.color}"></div>
            <div class="legend-text">
                <div class="font-semibold text-xs text-gray-700">${colorNames[h.color] || h.color}</div>
                <div class="text-xs text-gray-600 truncate">${h.text.substring(0, 50)}${h.text.length > 50 ? '...' : ''}</div>
            </div>
            <div class="legend-actions">
                <button onclick="event.stopPropagation(); deleteHighlight('${h.id}')" title="Delete">×</button>
            </div>
        </div>
    `).join('');
}

window.scrollToHighlight = (id) => {
    const editor = document.getElementById('editor');
    const highlight = editor.querySelector(`[data-highlight-id="${id}"]`);
    if (highlight) {
        highlight.scrollIntoView({behavior: 'smooth', block: 'center'});
        highlight.style.outline = '2px solid #10b981';
        highlight.style.outlineOffset = '2px';
        setTimeout(() => {
            highlight.style.outline = 'none';
        }, 2000);
    }
};

window.deleteHighlight = (id) => {
    const editor = document.getElementById('editor');
    const highlight = editor.querySelector(`[data-highlight-id="${id}"]`);
    if (highlight) {
        const parent = highlight.parentNode;
        while (highlight.firstChild) {
            parent.insertBefore(highlight.firstChild, highlight);
        }
        parent.removeChild(highlight);
    }
    
    if (state.userHighlights[state.activeId]) {
        state.userHighlights[state.activeId] = state.userHighlights[state.activeId].filter(h => h.id !== id);
    }
    
    saveState();
    updateHighlightLegend();
    toast('Highlight deleted', true);
};

window.exportHighlights = () => {
    const highlights = state.userHighlights[state.activeId] || [];
    if (highlights.length === 0) {
        toast('No highlights to export');
        return;
    }
    
    const doc = state.docs.find(d => d.id === state.activeId);
    const colorNames = {
        yellow: 'Facts',
        blue: 'Dates',
        green: 'Names',
        red: 'Important',
        purple: 'Ideas'
    };
    
    let text = `Highlights from: ${doc.name}\n`;
    text += `Exported: ${new Date().toLocaleString()}\n\n`;
    
    highlights.forEach((h, i) => {
        text += `${i + 1}. [${colorNames[h.color]}] ${h.text}\n\n`;
    });
    
    const blob = new Blob([text], {type: 'text/plain'});
    downloadBlob(blob, `${doc.name}-highlights.txt`);
    toast('📥 Highlights exported', true);
};

window.clearAllHighlights = () => {
    if (!confirm('Clear all highlights? This cannot be undone.')) return;
    
    const editor = document.getElementById('editor');
    const highlights = editor.querySelectorAll('[data-highlight-id]');
    highlights.forEach(h => {
        const parent = h.parentNode;
        while (h.firstChild) {
            parent.insertBefore(h.firstChild, h);
        }
        parent.removeChild(h);
    });
    
    state.userHighlights[state.activeId] = [];
    saveState();
    updateHighlightLegend();
    toast('All highlights cleared', true);
};

// Add event listeners in attachAllEvents()
document.addEventListener('mouseup', handleTextSelection);
document.addEventListener('selectionchange', handleTextSelection);

// Add button handler
const highlightLegendBtn = document.getElementById('highlightLegendBtn');
if (highlightLegendBtn) highlightLegendBtn.onclick = toggleHighlightLegend;
```

---

## 📋 Next Priority Features

### Journal Mode Features (Quick Wins)
1. **Daily Journal Prompts** - AI-generated prompts based on mood/time
2. **Mood Tracker** - Emoji mood selector with analytics
3. **Writing Timer** - Pomodoro timer for focused sessions
4. **Word Sprint Mode** - Timed writing challenges
5. **Auto-Save Drafts** - Already implemented, enhance with visual feedback
6. **Journal Templates** - Gratitude, dream, bullet journal formats

### Research Mode Features (Quick Wins)
1. **Citation Generator** - Extract and format citations
2. **Fact Checker** - Verify claims against sources
3. **Cross-Reference** - Link related sections
4. **Document Comparison** - Side-by-side diff view
5. **Table Extraction** - Pull tables from PDFs
6. **Image OCR** - Extract text from images
7. **Audio Transcription** - Upload audio, get transcripts

### Research Tools (Medium Complexity)
1. **Research Board** - Kanban-style organization
2. **Mind Map View** - Visual concept connections
3. **Bibliography Manager** - Organize sources
4. **Annotation Layers** - Multiple highlight colors (DONE with R1!)
5. **Document Outliner** - Auto-generate outline
6. **Reading Progress** - Track % read, time remaining
7. **Bookmarks** - Save specific pages/sections

---

## 🚀 Implementation Priority Order

### Phase 1: Core Highlighting (DONE)
- ✅ R1: Enhanced Smart Highlights

### Phase 2: Journal Enhancements (1-2 days)
- Daily Prompts Generator
- Mood Tracker with emoji selector
- Writing Timer (Pomodoro)
- Journal Templates

### Phase 3: Research Tools (2-3 days)
- Citation Generator
- Document Outliner
- Reading Progress Tracker
- Bookmarks System

### Phase 4: Advanced Features (3-5 days)
- Mind Map View
- Research Board (Kanban)
- Bibliography Manager
- Document Comparison

---

## 📝 Testing Checklist

### R1: Enhanced Smart Highlights
- [ ] Select text → toolbar appears
- [ ] Click yellow → text highlights yellow
- [ ] Click blue → text highlights blue
- [ ] Click green → text highlights green
- [ ] Click red → text highlights red
- [ ] Click purple → text highlights purple
- [ ] Click 🎨 button → legend opens
- [ ] Legend shows all highlights
- [ ] Click highlight in legend → scrolls to text
- [ ] Click × on highlight → removes it
- [ ] Export button → downloads .txt file
- [ ] Clear button → removes all highlights
- [ ] Highlights persist after page reload
- [ ] Highlights work across multiple documents

---

## 💡 Quick Implementation Tips

1. **Always test in backup.html first**
2. **Use browser DevTools to debug**
3. **Check console for errors**
4. **Test on mobile viewport**
5. **Verify localStorage persistence**
6. **Test with multiple documents**
7. **Check performance with 100+ highlights**

---

## 🎯 Success Metrics

- Highlight creation time: < 100ms
- Legend update time: < 50ms
- Export generation: < 500ms
- Storage size per document: < 50KB
- No memory leaks after 1000 operations
