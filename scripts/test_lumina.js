// Test script for backup-lumina.html
// Open https://documentgpt.io/backup-lumina.html and paste this in console

console.log('🧪 Testing backup-lumina.html buttons...\n');

const tests = [
    {name: 'Upload Button', id: 'uploadBtn'},
    {name: 'New Button', id: 'newBtn'},
    {name: 'Add Tab Button', id: 'addTabBtn'},
    {name: 'Send Button', id: 'sendBtn'},
    {name: 'Mic Button', id: 'micBtn'},
    {name: 'Find Button', id: 'findBtn'},
    {name: 'History Button', id: 'historyBtn'},
    {name: 'Focus Button', id: 'focusBtn'},
    {name: 'Theme Button', id: 'themeBtn'},
    {name: 'Upgrade Button', id: 'upgradeBtn'},
    {name: 'Login Button', id: 'loginBtn'},
    {name: 'Signup Button', id: 'signupBtn'},
    {name: 'DocIQ Tips', id: 'docIQTips'}
];

let passed = 0, failed = 0;

tests.forEach(({name, id}) => {
    const btn = document.getElementById(id);
    if (!btn) {
        console.error(`❌ ${name} (${id}) - NOT FOUND`);
        failed++;
    } else if (!btn.onclick && !btn.onchange) {
        console.error(`❌ ${name} (${id}) - NO HANDLER`);
        failed++;
    } else {
        console.log(`✅ ${name} (${id})`);
        passed++;
    }
});

// Test format toolbar
const toolbar = document.getElementById('formatToolbar');
if (toolbar && toolbar.onclick) {
    console.log('✅ Format Toolbar');
    passed++;
} else {
    console.error('❌ Format Toolbar - NO HANDLER');
    failed++;
}

// Test editor
const editor = document.getElementById('editor');
if (editor && editor.oninput) {
    console.log('✅ Editor Input Handler');
    passed++;
} else {
    console.error('❌ Editor Input Handler - MISSING');
    failed++;
}

// Test chat input
const chatInput = document.getElementById('chatInput');
if (chatInput && chatInput.onkeydown) {
    console.log('✅ Chat Input Enter Handler');
    passed++;
} else {
    console.error('❌ Chat Input Enter Handler - MISSING');
    failed++;
}

console.log('\n' + '='.repeat(50));
console.log(`Total: ${tests.length + 3} tests`);
console.log(`Passed: ${passed} ✅`);
console.log(`Failed: ${failed} ❌`);
console.log('='.repeat(50));

if (failed === 0) {
    console.log('\n🎉 ALL TESTS PASSED!');
} else {
    console.log('\n⚠️ SOME TESTS FAILED');
}

// Quick functional test
console.log('\n🔬 Running functional tests...\n');

// Test 1: New document
try {
    const initialCount = state.docs.length;
    document.getElementById('newBtn').click();
    if (state.docs.length > initialCount) {
        console.log('✅ New document creation works');
    } else {
        console.error('❌ New document not created');
    }
} catch (e) {
    console.error('❌ New document test failed:', e.message);
}

// Test 2: Editor typing
try {
    const editor = document.getElementById('editor');
    editor.textContent = 'Test content for DocumentGPT';
    editor.dispatchEvent(new Event('input', {bubbles: true}));
    setTimeout(() => {
        const wordCount = document.getElementById('wordCount').textContent;
        if (wordCount !== '0') {
            console.log('✅ Editor input works, word count:', wordCount);
        } else {
            console.error('❌ Word count not updating');
        }
    }, 100);
} catch (e) {
    console.error('❌ Editor test failed:', e.message);
}

// Test 3: Theme toggle
try {
    const initial = document.body.getAttribute('data-theme');
    document.getElementById('themeBtn').click();
    setTimeout(() => {
        const after = document.body.getAttribute('data-theme');
        if (initial !== after) {
            console.log('✅ Theme toggle works:', initial, '→', after);
        } else {
            console.error('❌ Theme did not change');
        }
    }, 100);
} catch (e) {
    console.error('❌ Theme test failed:', e.message);
}

console.log('\n✅ Test complete! Check results above.');
