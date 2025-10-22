#!/bin/bash

echo "🧪 Verifying DocumentGPT Button Functionality"
echo "=============================================="
echo ""

# Check if backup.html exists
if [ ! -f "web/backup.html" ]; then
    echo "❌ backup.html not found"
    exit 1
fi

echo "✅ backup.html found"
echo ""

# Check for critical button IDs
echo "Checking button IDs..."
buttons=(
    "uploadBtn"
    "newBtn"
    "sendBtn"
    "summaryAgent"
    "emailAgent"
    "sheetsAgent"
    "calendarAgent"
    "saveAgent"
    "exportAgent"
    "upgradeBtn"
    "loginBtn"
    "signupBtn"
    "themeBtn"
    "focusBtn"
    "boldBtn"
    "italicBtn"
    "underlineBtn"
    "settingsBtn"
    "paletteBtn"
    "healthBtn"
    "findBtn"
    "zoomIn"
    "zoomOut"
)

missing=0
for btn in "${buttons[@]}"; do
    if grep -q "id=\"$btn\"" web/backup.html; then
        echo "  ✅ $btn"
    else
        echo "  ❌ $btn MISSING"
        ((missing++))
    fi
done

echo ""
echo "Checking event handlers..."

# Check if attachAllEvents function exists
if grep -q "function attachAllEvents()" web/backup.html; then
    echo "  ✅ attachAllEvents() function exists"
else
    echo "  ❌ attachAllEvents() function missing"
    ((missing++))
fi

# Check if DOMContentLoaded calls attachAllEvents
if grep -q "attachAllEvents()" web/backup.html; then
    echo "  ✅ attachAllEvents() is called"
else
    echo "  ❌ attachAllEvents() not called"
    ((missing++))
fi

# Check for onclick handlers
onclick_count=$(grep -c "\.onclick = " web/backup.html)
echo "  ✅ Found $onclick_count onclick assignments"

# Check for addEventListener
listener_count=$(grep -c "addEventListener" web/backup.html)
echo "  ✅ Found $listener_count addEventListener calls"

echo ""
echo "=============================================="
if [ $missing -eq 0 ]; then
    echo "🎉 All checks passed!"
    echo ""
    echo "Next steps:"
    echo "1. Open https://documentgpt.io/backup.html"
    echo "2. Open browser console (F12)"
    echo "3. Copy and paste test_user_flow.js"
    echo "4. Run the test suite"
else
    echo "⚠️  $missing issues found"
    exit 1
fi
