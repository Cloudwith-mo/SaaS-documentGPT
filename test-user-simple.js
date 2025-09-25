const https = require('https');
const fs = require('fs');

async function testUserFlow() {
    console.log('🚀 Testing DocumentGPT user flow...');
    
    // Test 1: Check site loads
    console.log('1. Testing site availability...');
    try {
        const response = await fetch('https://documentgpt.io/');
        console.log(`✅ Site loads: ${response.status}`);
    } catch (error) {
        console.log(`❌ Site error: ${error.message}`);
    }
    
    // Test 2: Test upload endpoint
    console.log('2. Testing upload endpoint...');
    try {
        const uploadResponse = await fetch('https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/upload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': 'dk-test-key-123',
                'x-user-id': 'test-user'
            },
            body: JSON.stringify({
                filename: 'test.txt',
                contentType: 'text/plain'
            })
        });
        
        if (uploadResponse.ok) {
            const data = await uploadResponse.json();
            console.log(`✅ Upload endpoint works: ${data.docId}`);
            
            // Test 3: Test status endpoint with the docId
            console.log('3. Testing status endpoint...');
            const statusResponse = await fetch(`https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/status?docId=${data.docId}`, {
                headers: {
                    'x-api-key': 'dk-test-key-123',
                    'x-user-id': 'test-user'
                }
            });
            
            if (statusResponse.ok) {
                const statusData = await statusResponse.json();
                console.log(`✅ Status endpoint works: ${statusData.phase}`);
            } else {
                console.log(`❌ Status endpoint failed: ${statusResponse.status}`);
            }
            
        } else {
            console.log(`❌ Upload endpoint failed: ${uploadResponse.status}`);
        }
    } catch (error) {
        console.log(`❌ API error: ${error.message}`);
    }
    
    // Test 4: Test chat endpoint
    console.log('4. Testing chat endpoint...');
    try {
        const chatResponse = await fetch('https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': 'dk-test-key-123',
                'x-user-id': 'test-user'
            },
            body: JSON.stringify({
                question: 'Hello, test question',
                docId: 'test-doc-123'
            })
        });
        
        if (chatResponse.ok) {
            const chatData = await chatResponse.json();
            console.log(`✅ Chat endpoint works`);
        } else {
            console.log(`❌ Chat endpoint failed: ${chatResponse.status}`);
        }
    } catch (error) {
        console.log(`❌ Chat error: ${error.message}`);
    }
    
    console.log('🎉 User flow test completed!');
}

testUserFlow();