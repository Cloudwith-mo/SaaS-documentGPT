#!/bin/bash
# Apply R1: Enhanced Smart Highlights to backup.html

FILE="web/backup.html"

# Step 1: Add CSS before closing </style>
sed -i.tmp '/<\/style>/i\
/* R1: Enhanced Smart Highlights */\
.highlight-yellow{background:linear-gradient(120deg,#fef3c7 0%,#fde68a 100%);padding:2px 4px;border-radius:3px;cursor:pointer}\
.highlight-blue{background:linear-gradient(120deg,#dbeafe 0%,#bfdbfe 100%);padding:2px 4px;border-radius:3px;cursor:pointer}\
.highlight-green{background:linear-gradient(120deg,#d1fae5 0%,#a7f3d0 100%);padding:2px 4px;border-radius:3px;cursor:pointer}\
.highlight-red{background:linear-gradient(120deg,#fecaca 0%,#fca5a5 100%);padding:2px 4px;border-radius:3px;cursor:pointer}\
.highlight-purple{background:linear-gradient(120deg,#e9d5ff 0%,#d8b4fe 100%);padding:2px 4px;border-radius:3px;cursor:pointer}\
#selectionToolbar{position:absolute;display:none;background:rgba(255,255,255,0.98);backdrop-filter:blur(20px);border:1px solid rgba(16,185,129,0.25);border-radius:12px;padding:8px;box-shadow:0 8px 28px rgba(16,185,129,0.2);z-index:1001;gap:4px}\
#selectionToolbar.visible{display:flex}\
#selectionToolbar button{padding:6px 10px;border-radius:8px;border:1px solid rgba(16,185,129,0.2);background:white;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s}\
#selectionToolbar button:hover{background:#f0fdf4;transform:translateY(-1px)}\
#highlightLegend{position:fixed;right:420px;top:80px;width:280px;max-height:500px;background:rgba(255,255,255,0.95);backdrop-filter:blur(20px);border:1px solid rgba(16,185,129,0.2);border-radius:16px;box-shadow:0 8px 32px rgba(16,185,129,0.15);overflow:hidden;display:none;flex-direction:column;z-index:85}\
#highlightLegend.visible{display:flex}\
.legend-item{padding:10px 12px;border-bottom:1px solid rgba(16,185,129,0.1);cursor:pointer;transition:all 0.2s;display:flex;align-items:center;gap:8px}\
.legend-item:hover{background:rgba(16,185,129,0.05)}\
.legend-color{width:20px;height:20px;border-radius:4px;flex-shrink:0}\
.legend-text{flex:1;font-size:12px;line-height:1.4}\
.legend-actions{display:flex;gap:4px}\
.legend-actions button{padding:2px 6px;font-size:10px;border-radius:4px;border:1px solid rgba(16,185,129,0.3);background:white;cursor:pointer}\
.legend-actions button:hover{background:#f0fdf4}
' "$FILE"

echo "✅ R1: Enhanced Smart Highlights CSS added"
echo "📝 Manual steps remaining:"
echo "1. Add HTML elements (selection toolbar & legend)"
echo "2. Add highlight button to right sidebar"
echo "3. Add JavaScript functions"
echo "4. Deploy: aws s3 cp web/backup.html s3://documentgpt-website-prod/backup.html"
