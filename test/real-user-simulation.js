const https = require('https');
const fs = require('fs');

// Simulate real user workflow
async function simulateRealUser() {
    console.log('🧪 Simulating real user workflow on https://documentgpt.io/\n');
    
    // Step 1: Test file upload (like user dropping a file)
    console.log('📁 Step 1: Testing file upload...');
    const uploadResult = await testFileUpload();
    
    if (!uploadResult.success) {
        console.log('❌ Upload failed, stopping test');
        return;
    }
    
    console.log('✅ Upload successful!');
    console.log('   DocId:', uploadResult.docId);
    console.log('   Upload URL generated:', uploadResult.uploadUrl ? 'Yes' : 'No');
    
    // Step 2: Test chat without document (general AI mode)
    console.log('\n💬 Step 2: Testing general AI chat...');
    const generalChatResult = await testChat('What is artificial intelligence?', null);
    
    if (generalChatResult.success) {
        console.log('✅ General AI chat working');
        console.log('   Response preview:', generalChatResult.answer.substring(0, 100) + '...');
    } else {
        console.log('❌ General AI chat failed');
    }
    
    // Step 3: Test chat with document (RAG mode)
    console.log('\n📄 Step 3: Testing document-based chat...');
    const ragChatResult = await testChat('Summarize this document', uploadResult.docId);
    
    if (ragChatResult.success) {
        console.log('✅ Document-based chat working');
        console.log('   Response preview:', ragChatResult.answer.substring(0, 100) + '...');
        console.log('   Has context:', ragChatResult.hasContext ? 'Yes' : 'No');
    } else {
        console.log('❌ Document-based chat failed');
    }
    
    console.log('\n🎉 User simulation complete!');
    console.log('Summary:');
    console.log('- Upload:', uploadResult.success ? '✅' : '❌');
    console.log('- General Chat:', generalChatResult.success ? '✅' : '❌');  
    console.log('- Document Chat:', ragChatResult.success ? '✅' : '❌');
}

function testFileUpload() {
    return new Promise((resolve) => {
        const postData = JSON.stringify({
            filename: 'test-document.txt',
            contentType: 'text/plain'
        });

        const options = {
            hostname: '9voqzgx3ch.execute-api.us-east-1.amazonaws.com',
            port: 443,
            path: '/prod/upload',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': postData.length,
                'x-api-key': 'dk-test-key-123',
                'x-user-id': 'test-user-' + Date.now(),
                'Origin': 'https://documentgpt.io'
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    const result = JSON.parse(data);
                    resolve({
                        success: res.statusCode === 200,
                        docId: result.docId,
                        uploadUrl: result.uploadUrl,
                        status: res.statusCode
                    });
                } catch (error) {
                    resolve({ success: false, error: error.message });
                }
            });
        });

        req.on('error', (error) => {
            resolve({ success: false, error: error.message });
        });
        
        req.write(postData);
        req.end();
    });
}

function testChat(question, docId) {
    return new Promise((resolve) => {
        const postData = JSON.stringify({
            question: question,
            docId: docId,
            sessionId: 'test-session-' + Date.now()
        });

        const options = {
            hostname: '9voqzgx3ch.execute-api.us-east-1.amazonaws.com',
            port: 443,
            path: '/prod/rag-chat',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': postData.length,
                'Origin': 'https://documentgpt.io'
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    const result = JSON.parse(data);
                    resolve({
                        success: res.statusCode === 200,
                        answer: result.answer || '',
                        hasContext: result.hasContext,
                        status: res.statusCode
                    });
                } catch (error) {
                    resolve({ success: false, error: error.message });
                }
            });
        });

        req.on('error', (error) => {
            resolve({ success: false, error: error.message });
        });
        
        req.write(postData);
        req.end();
    });
}

// Run the simulation
simulateRealUser().catch(console.error);