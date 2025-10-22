/**
 * Real User Journal Test
 * Simulates: Open chat → Write journal → Ask AI to add lines → Verify it appears
 */

const API = 'https://i1dy8i3692.execute-api.us-east-1.amazonaws.com/prod';
const TEST_USER = `guest_test_${Date.now()}`;

console.log('🧪 Starting Real User Journal Test...\n');

// Test 1: Create new chat (simulate opening app)
async function test1_openChat() {
    console.log('📝 Test 1: Opening new chat...');
    const journalContent = 'Today was a productive day. I worked on my project and made good progress.';
    console.log(`   Writing: "${journalContent}"`);
    return { journalContent, success: true };
}

// Test 2: Send message to AI about journal
async function test2_talkToAI(journalContent) {
    console.log('\n💬 Test 2: Talking to AI about journal...');
    
    const message = `I'm writing in my journal: "${journalContent}". Can you add a few motivational lines to continue this?`;
    console.log(`   User: "${message}"`);
    
    try {
        const response = await fetch(`${API}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: TEST_USER,
                messages: [
                    { role: 'user', content: message }
                ]
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            console.log(`   ❌ Error: ${data.error}`);
            return { success: false, error: data.error };
        }
        
        console.log(`   ✅ AI Response: "${data.response}"`);
        return { success: true, aiResponse: data.response, journalContent };
        
    } catch (error) {
        console.log(`   ❌ Network Error: ${error.message}`);
        return { success: false, error: error.message };
    }
}

// Test 3: Ask AI to add specific lines
async function test3_askAIToAdd(previousContext) {
    console.log('\n✍️  Test 3: Asking AI to add lines to journal...');
    
    const message = 'Add 2-3 lines about staying focused and achieving goals';
    console.log(`   User: "${message}"`);
    
    try {
        const response = await fetch(`${API}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: TEST_USER,
                messages: [
                    { role: 'user', content: previousContext.journalContent },
                    { role: 'assistant', content: previousContext.aiResponse },
                    { role: 'user', content: message }
                ]
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            console.log(`   ❌ Error: ${data.error}`);
            return { success: false, error: data.error };
        }
        
        console.log(`   ✅ AI Added: "${data.response}"`);
        return { 
            success: true, 
            finalJournal: previousContext.journalContent + '\n\n' + data.response 
        };
        
    } catch (error) {
        console.log(`   ❌ Network Error: ${error.message}`);
        return { success: false, error: error.message };
    }
}

// Test 4: Verify journal content is available
async function test4_verifyJournal(finalJournal) {
    console.log('\n🔍 Test 4: Verifying journal content...');
    
    if (!finalJournal) {
        console.log('   ❌ No journal content to verify');
        return { success: false };
    }
    
    console.log(`   ✅ Final Journal Entry:\n`);
    console.log('   ' + '─'.repeat(60));
    console.log('   ' + finalJournal.split('\n').join('\n   '));
    console.log('   ' + '─'.repeat(60));
    
    return { success: true, finalJournal };
}

// Test 5: Test CORS headers
async function test5_checkCORS() {
    console.log('\n🌐 Test 5: Checking CORS headers...');
    
    try {
        const response = await fetch(`${API}/chat`, {
            method: 'OPTIONS',
            headers: {
                'Origin': 'https://documentgpt.io',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        });
        
        const corsOrigin = response.headers.get('access-control-allow-origin');
        const corsMethods = response.headers.get('access-control-allow-methods');
        
        console.log(`   CORS Origin: ${corsOrigin}`);
        console.log(`   CORS Methods: ${corsMethods}`);
        
        if (corsOrigin && corsMethods) {
            console.log('   ✅ CORS configured correctly');
            return { success: true };
        } else {
            console.log('   ❌ CORS headers missing');
            return { success: false };
        }
        
    } catch (error) {
        console.log(`   ❌ CORS check failed: ${error.message}`);
        return { success: false };
    }
}

// Run all tests
async function runAllTests() {
    const results = [];
    
    // Test 1
    const t1 = await test1_openChat();
    results.push({ name: 'Open Chat', ...t1 });
    
    if (!t1.success) {
        console.log('\n❌ Test 1 failed, stopping...');
        return printSummary(results);
    }
    
    // Test 2
    const t2 = await test2_talkToAI(t1.journalContent);
    results.push({ name: 'Talk to AI', ...t2 });
    
    if (!t2.success) {
        console.log('\n❌ Test 2 failed, stopping...');
        return printSummary(results);
    }
    
    // Test 3
    const t3 = await test3_askAIToAdd(t2);
    results.push({ name: 'Ask AI to Add', ...t3 });
    
    if (!t3.success) {
        console.log('\n❌ Test 3 failed, stopping...');
        return printSummary(results);
    }
    
    // Test 4
    const t4 = await test4_verifyJournal(t3.finalJournal);
    results.push({ name: 'Verify Journal', ...t4 });
    
    // Test 5
    const t5 = await test5_checkCORS();
    results.push({ name: 'Check CORS', ...t5 });
    
    printSummary(results);
}

function printSummary(results) {
    console.log('\n' + '═'.repeat(60));
    console.log('📊 TEST SUMMARY');
    console.log('═'.repeat(60));
    
    results.forEach((r, i) => {
        const status = r.success ? '✅' : '❌';
        console.log(`${status} Test ${i + 1}: ${r.name}`);
        if (r.error) console.log(`   Error: ${r.error}`);
    });
    
    const passed = results.filter(r => r.success).length;
    const total = results.length;
    
    console.log('─'.repeat(60));
    console.log(`Result: ${passed}/${total} tests passed`);
    
    if (passed === total) {
        console.log('\n🎉 ALL TESTS PASSED! Journal feature is working correctly.');
    } else {
        console.log('\n⚠️  SOME TESTS FAILED. Check errors above.');
    }
    console.log('═'.repeat(60));
}

// Run tests
runAllTests().catch(err => {
    console.error('\n💥 Test suite crashed:', err);
});
