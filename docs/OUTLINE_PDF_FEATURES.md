# Outline Builder + PDF Search Implementation

## Features to Add

### 1. Outline Builder (1-2 days)
- Extract headings automatically from document
- Drag-drop to reorganize sections
- Generate outline from AI suggestions
- Click heading to jump to section

### 2. PDF Search & Annotations (3-4 days)
- In-document search with highlighting
- Click-to-add notes on PDF text
- Export highlights and notes
- Search results navigation

## Implementation Plan

### Outline Builder
```javascript
// Add to state
if (!state.outlines) state.outlines = {};

// Extract outline
function extractOutline() {
    const editor = document.getElementById('editor');
    const text = editor.textContent;
    const headings = [];
    
    // Find headings (markdown # or Title: format)
    const lines = text.split('\n');
    lines.forEach((line, idx) => {
        if (line.match(/^#{1,3}\s+/) || line.match(/^[A-Z][^.!?]{5,50}:$/)) {
            headings.push({text: line.trim(), line: idx});
        }
    });
    
    return headings;
}

// Show outline panel
function showOutlinePanel() {
    const outline = extractOutline();
    // Render in sidebar or modal
}
```

### PDF Search
```javascript
// Add search state
let pdfSearchResults = [];
let currentSearchIndex = 0;

// Search in PDF
function searchInPDF(query) {
    const editor = document.getElementById('editor');
    const text = editor.textContent;
    const regex = new RegExp(query, 'gi');
    const matches = [];
    
    let match;
    while ((match = regex.exec(text)) !== null) {
        matches.push({index: match.index, text: match[0]});
    }
    
    pdfSearchResults = matches;
    highlightSearchResults();
}

// Highlight results
function highlightSearchResults() {
    const editor = document.getElementById('editor');
    let html = editor.innerHTML;
    
    pdfSearchResults.forEach((m, i) => {
        const escaped = m.text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        html = html.replace(
            new RegExp(`(${escaped})`, 'gi'),
            `<mark class="search-result" data-index="${i}">$1</mark>`
        );
    });
    
    editor.innerHTML = html;
}
```

## UI Components

### Outline Panel (Lightning Menu)
```html
<button onclick="showOutlineBuilder()">📋 Outline</button>
```

### PDF Search Bar (for PDFs only)
```html
<div id="pdfSearchBar" style="display:none;">
    <input id="pdfSearchInput" placeholder="Search in document..." />
    <button onclick="searchInPDF()">🔍</button>
    <span id="searchResults">0 of 0</span>
    <button onclick="prevSearchResult()">←</button>
    <button onclick="nextSearchResult()">→</button>
</div>
```

## Deployment
- Add to backup.html
- Test with PDF documents
- Deploy to dev → staging → prod
