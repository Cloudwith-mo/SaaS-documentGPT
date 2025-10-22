// OUTLINE BUILDER + PDF SEARCH FEATURES
// Add this code to backup.html before closing </script> tag

// === OUTLINE BUILDER ===
if (!state.outlines) state.outlines = {};
let currentOutline = [];

function extractOutline() {
    const editor = document.getElementById('editor');
    const text = editor.textContent;
    const headings = [];
    const lines = text.split('\n');
    
    lines.forEach((line, idx) => {
        const trimmed = line.trim();
        if (trimmed.match(/^#{1,3}\s+/)) {
            const level = (trimmed.match(/^#+/) || [''])[0].length;
            headings.push({text: trimmed.replace(/^#+\s*/, ''), line: idx, level});
        } else if (trimmed.match(/^[A-Z][^.!?]{5,50}:$/)) {
            headings.push({text: trimmed, line: idx, level: 1});
        }
    });
    
    return headings;
}

function showOutlineBuilder() {
    const outline = extractOutline();
    currentOutline = outline;
    
    const modal = document.createElement('div');
    modal.id = 'outlineModal';
    modal.className = 'fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center';
    modal.style.zIndex = '100';
    
    modal.innerHTML = `
        <div class="bg-white rounded-2xl shadow-2xl w-[600px] max-h-[80vh] flex flex-col">
            <div class="px-4 py-3 border-b flex items-center justify-between">
                <h2 class="text-lg font-bold">📋 Document Outline</h2>
                <div class="flex gap-2">
                    <button onclick="generateAIOutline()" class="text-xs px-3 py-1 rounded-lg bg-emerald-500 text-white hover:bg-emerald-600">✨ AI Generate</button>
                    <button onclick="document.getElementById('outlineModal').remove()" class="text-2xl opacity-50 hover:opacity-100">×</button>
                </div>
            </div>
            <div class="flex-1 overflow-auto p-4">
                ${outline.length === 0 ? 
                    '<div class="text-center py-8 text-gray-500">No headings found. Add headings to your document or use AI to generate an outline.</div>' :
                    '<div id="outlineList" class="space-y-2">' + outline.map((h, i) => `
                        <div class="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-50 cursor-pointer" onclick="jumpToHeading(${h.line})" style="padding-left: ${h.level * 16}px">
                            <span class="text-sm flex-1">${h.text}</span>
                            <button onclick="event.stopPropagation();editHeading(${i})" class="text-xs px-2 py-1 rounded border hover:bg-gray-100">Edit</button>
                        </div>
                    `).join('') + '</div>'
                }
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
}

function jumpToHeading(lineNum) {
    const editor = document.getElementById('editor');
    const lines = editor.textContent.split('\n');
    let charCount = 0;
    
    for (let i = 0; i < lineNum && i < lines.length; i++) {
        charCount += lines[i].length + 1;
    }
    
    const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT);
    let currentCount = 0;
    let targetNode = null;
    
    while (walker.nextNode()) {
        const node = walker.currentNode;
        if (currentCount + node.length >= charCount) {
            targetNode = node;
            break;
        }
        currentCount += node.length;
    }
    
    if (targetNode && targetNode.parentElement) {
        targetNode.parentElement.scrollIntoView({behavior: 'smooth', block: 'center'});
        toast('📍 Jumped to heading', true);
    }
    
    document.getElementById('outlineModal')?.remove();
}

async function generateAIOutline() {
    const editor = document.getElementById('editor');
    const text = editor.textContent.trim();
    
    if (text.length < 50) {
        toast('Write more content first');
        return;
    }
    
    toast('Generating outline...');
    
    try {
        const res = await fetch(`${API}/chat`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: state.user.sub,
                messages: [{
                    role: 'user',
                    content: `Generate a document outline with 3-5 main headings for this content. Format as "# Heading" (respond with ONLY the headings, one per line):\n\n${text.substring(0, 2000)}`
                }]
            })
        });
        
        if (res.ok) {
            const data = await res.json();
            const headings = data.response.split('\n').filter(l => l.trim());
            
            // Insert headings at top of document
            const currentContent = editor.innerHTML;
            const outlineHTML = headings.map(h => `<h2>${h.replace(/^#+\s*/, '')}</h2>`).join('');
            editor.innerHTML = outlineHTML + '<br>' + currentContent;
            
            handleEditorInput();
            toast('✨ Outline generated', true);
            document.getElementById('outlineModal')?.remove();
            showOutlineBuilder();
        }
    } catch (e) {
        toast('Failed to generate outline');
    }
}

// === PDF SEARCH & ANNOTATIONS ===
let pdfSearchResults = [];
let currentSearchIndex = 0;
let pdfAnnotations = {};

function showPDFSearch() {
    const doc = state.docs.find(d => d.id === state.activeId);
    if (!doc || !doc.isPdf) {
        toast('PDF search only works with PDF documents');
        return;
    }
    
    const existing = document.getElementById('pdfSearchBar');
    if (existing) {
        existing.remove();
        return;
    }
    
    const searchBar = document.createElement('div');
    searchBar.id = 'pdfSearchBar';
    searchBar.className = 'fixed top-20 right-4 bg-white rounded-xl shadow-lg p-3 border border-emerald-200 flex items-center gap-2';
    searchBar.style.zIndex = '1000';
    
    searchBar.innerHTML = `
        <input id="pdfSearchInput" placeholder="Search in PDF..." class="border rounded px-2 py-1 text-sm w-48" />
        <button onclick="searchInPDF()" class="px-2 py-1 rounded bg-emerald-500 text-white hover:bg-emerald-600 text-sm">🔍</button>
        <span id="searchResults" class="text-xs text-gray-600">0 of 0</span>
        <button onclick="prevSearchResult()" class="px-2 py-1 rounded border hover:bg-gray-50 text-sm">←</button>
        <button onclick="nextSearchResult()" class="px-2 py-1 rounded border hover:bg-gray-50 text-sm">→</button>
        <button onclick="document.getElementById('pdfSearchBar').remove()" class="text-gray-400 hover:text-gray-600">×</button>
    `;
    
    document.body.appendChild(searchBar);
    document.getElementById('pdfSearchInput').focus();
    
    document.getElementById('pdfSearchInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') searchInPDF();
    });
}

function searchInPDF() {
    const query = document.getElementById('pdfSearchInput')?.value.trim();
    if (!query) return;
    
    const editor = document.getElementById('editor');
    const text = editor.textContent;
    
    // Clear previous highlights
    editor.innerHTML = editor.innerHTML.replace(/<mark class="search-result"[^>]*>(.*?)<\/mark>/gi, '$1');
    
    // Find all matches
    const regex = new RegExp(query, 'gi');
    const matches = [];
    let match;
    
    while ((match = regex.exec(text)) !== null) {
        matches.push({index: match.index, text: match[0]});
    }
    
    pdfSearchResults = matches;
    currentSearchIndex = 0;
    
    if (matches.length === 0) {
        document.getElementById('searchResults').textContent = 'Not found';
        toast(`No results for "${query}"`);
        return;
    }
    
    // Highlight all results
    let html = editor.innerHTML;
    const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    html = html.replace(
        new RegExp(`(${escaped})`, 'gi'),
        '<mark class="search-result" style="background: yellow; padding: 2px;">$1</mark>'
    );
    editor.innerHTML = html;
    
    document.getElementById('searchResults').textContent = `1 of ${matches.length}`;
    scrollToSearchResult(0);
    toast(`Found ${matches.length} result${matches.length > 1 ? 's' : ''}`);
}

function scrollToSearchResult(index) {
    const results = document.querySelectorAll('.search-result');
    if (results.length === 0) return;
    
    results.forEach((r, i) => {
        if (i === index) {
            r.style.background = 'orange';
            r.style.outline = '2px solid #10b981';
            r.scrollIntoView({behavior: 'smooth', block: 'center'});
        } else {
            r.style.background = 'yellow';
            r.style.outline = 'none';
        }
    });
}

function nextSearchResult() {
    if (pdfSearchResults.length === 0) return;
    currentSearchIndex = (currentSearchIndex + 1) % pdfSearchResults.length;
    document.getElementById('searchResults').textContent = `${currentSearchIndex + 1} of ${pdfSearchResults.length}`;
    scrollToSearchResult(currentSearchIndex);
}

function prevSearchResult() {
    if (pdfSearchResults.length === 0) return;
    currentSearchIndex = (currentSearchIndex - 1 + pdfSearchResults.length) % pdfSearchResults.length;
    document.getElementById('searchResults').textContent = `${currentSearchIndex + 1} of ${pdfSearchResults.length}`;
    scrollToSearchResult(currentSearchIndex);
}

// Add to lightning menu
window.showOutlineBuilder = showOutlineBuilder;
window.showPDFSearch = showPDFSearch;
window.jumpToHeading = jumpToHeading;
window.generateAIOutline = generateAIOutline;
window.searchInPDF = searchInPDF;
window.nextSearchResult = nextSearchResult;
window.prevSearchResult = prevSearchResult;

console.log('✅ Outline Builder + PDF Search loaded');
