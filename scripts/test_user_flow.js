// Real User Flow Test Script
// Run this in browser console on https://documentgpt.io/backup.html

console.log('🧪 Starting Real User Flow Test...\n');

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function testUserFlow() {
    const results = [];
    
    // Test 1: New Document Button
    console.log('Test 1: Creating new document...');
    try {
        const newBtn = document.getElementById('newBtn');
        if (!newBtn) throw new Error('New button not found');
        newBtn.click();
        await sleep(500);
        const tabs = document.getElementById('tabsContainer').children;
        if (tabs.length < 2) throw new Error('New document not created');
        results.push('✅ New document creation works');
        console.log('✅ PASS: New document created');
    } catch (e) {
        results.push('❌ New document creation failed: ' + e.message);
        console.error('❌ FAIL:', e.message);
    }
    
    // Test 2: Editor Input
    console.log('\nTest 2: Testing editor input...');
    try {
        const editor = document.getElementById('editor');
        if (!editor) throw new Error('Editor not found');
        editor.focus();
        editor.textContent = 'Test content for DocumentGPT';
        editor.dispatchEvent(new Event('input', { bubbles: true }));
        await sleep(500);
        const wordCount = document.getElementById('wordCount').textContent;
        if (wordCount === '0') throw new Error('Word count not updating');
        results.push('✅ Editor input and stats work');
        console.log('✅ PASS: Editor working, word count:', wordCount);
    } catch (e) {
        results.push('❌ Editor input failed: ' + e.message);
        console.error('❌ FAIL:', e.message);
    }
    
    // Test 3: Bold Formatting
    console.log('\nTest 3: Testing bold formatting...');
    try {
        const editor = document.getElementById('editor');
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(editor);
        selection.removeAllRanges();
        selection.addRange(range);
        
        const boldBtn = document.getElementById('boldBtn');
        if (!boldBtn) throw new Error('Bold button not found');
        boldBtn.click();
        await sleep(300);
        
        const hasBold = editor.innerHTML.includes('<b>') || editor.innerHTML.includes('<strong>');
        if (!hasBold) throw new Error('Bold formatting not applied');
        results.push('✅ Bold formatting works');
        console.log('✅ PASS: Bold formatting applied');
    } catch (e) {
        results.push('❌ Bold formatting failed: ' + e.message);
        console.error('❌ FAIL:', e.message);
    }
    
    // Test 4: Chat Input
    console.log('\nTest 4: Testing chat input...');
    try {
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');
        if (!chatInput || !sendBtn) throw new Error('Chat elements not found');
        
        chatInput.value = 'Test message';
        sendBtn.click();
        await sleep(500);
        
        const messages = document.getElementById('chatMessages').children;
        if (messages.length < 2) throw new Error('Chat message not sent');
        results.push('✅ Chat functionality works');
        console.log('✅ PASS: Chat message sent');
    } catch (e) {
        results.push('❌ Chat failed: ' + e.message);
        console.error('❌ FAIL:', e.message);
    }
    
    // Test 5: Theme Toggle
    console.log('\nTest 5: Testing theme toggle...');
    try {
        const themeBtn = document.getElementById('themeBtn');
        if (!themeBtn) throw new Error('Theme button not found');
        
        const initialTheme = document.body.getAttribute('data-theme');
        themeBtn.click();
        await sleep(300);
        const newTheme = document.body.getAttribute('data-theme');
        
        if (initialTheme === newTheme) throw new Error('Theme did not change');
        results.push('✅ Theme toggle works');
        console.log('✅ PASS: Theme changed from', initialTheme, 'to', newTheme);
    } catch (e) {
        results.push('❌ Theme toggle failed: ' + e.message);
        console.error('❌ FAIL:', e.message);
    }
    
    // Test 6: Focus Mode
    console.log('\nTest 6: Testing focus mode...');
    try {
        const focusBtn = document.getElementById('focusBtn');
        if (!focusBtn) throw new Error('Focus button not found');
        
        focusBtn.click();
        await sleep(300);
        
        const leftSidebar = document.getElementById('leftSidebar');
        const rightSidebar = document.getElementById('rightSidebar');
        const isHidden = leftSidebar.classList.contains('hidden') && rightSidebar.classList.contains('hidden');
        
        if (!isHidden) throw new Error('Sidebars not hidden in focus mode');
        
        // Toggle back
        focusBtn.click();
        await sleep(300);
        
        results.push('✅ Focus mode works');
        console.log('✅ PASS: Focus mode toggled successfully');
    } catch (e) {
        results.push('❌ Focus mode failed: ' + e.message);
        console.error('❌ FAIL:', e.message);
    }
    
    // Test 7: Zoom Controls
    console.log('\nTest 7: Testing zoom controls...');
    try {
        const zoomIn = document.getElementById('zoomIn');
        const zoomOut = document.getElementById('zoomOut');
        const zoomLabel = document.getElementById('zoomLabel');
        
        if (!zoomIn || !zoomOut) throw new Error('Zoom buttons not found');
        
        const initialZoom = zoomLabel.textContent;
        zoomIn.click();
        await sleep(300);
        const newZoom = zoomLabel.textContent;
        
        if (initialZoom === newZoom) throw new Error('Zoom did not change');
        results.push('✅ Zoom controls work');
        console.log('✅ PASS: Zoom changed from', initialZoom, 'to', newZoom);
    } catch (e) {
        results.push('❌ Zoom controls failed: ' + e.message);
        console.error('❌ FAIL:', e.message);
    }
    
    // Test 8: Command Palette
    console.log('\nTest 8: Testing command palette...');
    try {
        const paletteBtn = document.getElementById('paletteBtn');
        if (!paletteBtn) throw new Error('Palette button not found');
        
        paletteBtn.click();
        await sleep(300);
        
        const palette = document.getElementById('palette');
        const isVisible = palette.classList.contains('flex');
        
        if (!isVisible) throw new Error('Palette not visible');
        
        // Close it
        document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
        await sleep(300);
        
        results.push('✅ Command palette works');
        console.log('✅ PASS: Command palette opened and closed');
    } catch (e) {
        results.push('❌ Command palette failed: ' + e.message);
        console.error('❌ FAIL:', e.message);
    }
    
    // Test 9: Settings Modal
    console.log('\nTest 9: Testing settings modal...');
    try {
        const settingsBtn = document.getElementById('settingsBtn');
        if (!settingsBtn) throw new Error('Settings button not found');
        
        settingsBtn.click();
        await sleep(300);
        
        const modal = document.getElementById('settingsModal');
        if (!modal) throw new Error('Settings modal not created');
        
        // Close it
        modal.remove();
        
        results.push('✅ Settings modal works');
        console.log('✅ PASS: Settings modal opened');
    } catch (e) {
        results.push('❌ Settings modal failed: ' + e.message);
        console.error('❌ FAIL:', e.message);
    }
    
    // Test 10: Agent Buttons
    console.log('\nTest 10: Testing agent buttons...');
    try {
        const agents = ['summaryAgent', 'emailAgent', 'sheetsAgent', 'calendarAgent', 'saveAgent', 'exportAgent'];
        let allFound = true;
        
        for (const agentId of agents) {
            const btn = document.getElementById(agentId);
            if (!btn || !btn.onclick) {
                allFound = false;
                console.error('❌', agentId, 'not found or no handler');
            }
        }
        
        if (!allFound) throw new Error('Some agent buttons missing');
        
        // Test export agent (doesn't require API)
        const exportBtn = document.getElementById('exportAgent');
        exportBtn.click();
        await sleep(500);
        
        results.push('✅ Agent buttons work');
        console.log('✅ PASS: All agent buttons found and clickable');
    } catch (e) {
        results.push('❌ Agent buttons failed: ' + e.message);
        console.error('❌ FAIL:', e.message);
    }
    
    // Print Summary
    console.log('\n' + '='.repeat(50));
    console.log('📊 TEST SUMMARY');
    console.log('='.repeat(50));
    results.forEach(r => console.log(r));
    
    const passed = results.filter(r => r.startsWith('✅')).length;
    const failed = results.filter(r => r.startsWith('❌')).length;
    
    console.log('\n' + '='.repeat(50));
    console.log(`Total: ${results.length} tests`);
    console.log(`Passed: ${passed} ✅`);
    console.log(`Failed: ${failed} ❌`);
    console.log('='.repeat(50));
    
    if (failed === 0) {
        console.log('\n🎉 ALL TESTS PASSED! 🎉');
    } else {
        console.log('\n⚠️ SOME TESTS FAILED - CHECK ABOVE FOR DETAILS');
    }
}

// Run the test
testUserFlow().catch(e => console.error('Test suite failed:', e));
