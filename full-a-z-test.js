// Full A-Z Test: Complete User Journey
async function fullAZTest() {
    console.log('🚀 Full A-Z Test: Complete User Journey');
    console.log('=====================================');
    
    let testResults = {
        siteLoad: false,
        apiHealth: false,
        upload: false,
        s3Upload: false,
        processing: false,
        status: false,
        chat: false
    };
    
    // Test 1: Site Load
    console.log('\n1. 🌐 Testing site load...');
    try {
        const siteResponse = await fetch('https://documentgpt.io/');
        testResults.siteLoad = siteResponse.ok;
        console.log(`   ✅ Site loads: ${siteResponse.status}`);
    } catch (error) {
        console.log(`   ❌ Site load failed: ${error.message}`);
    }
    
    // Test 2: API Health Check
    console.log('\n2. 🔌 Testing API health...');
    try {
        const apiResponse = await fetch('https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/upload', {
            method: 'OPTIONS'
        });
        testResults.apiHealth = apiResponse.status === 204;
        console.log(`   ✅ API Gateway responds: ${apiResponse.status}`);
    } catch (error) {
        console.log(`   ❌ API health failed: ${error.message}`);
    }
    
    // Test 3: Upload Endpoint
    console.log('\n3. 📤 Testing upload endpoint...');
    let docId, uploadUrl, downloadUrl;
    try {
        const uploadResponse = await fetch('https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/upload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': 'dk-test-key-123',
                'x-user-id': 'frontend-user'
            },
            body: JSON.stringify({
                filename: 'full-test.txt',
                contentType: 'text/plain'
            })\n        });\n        \n        if (uploadResponse.ok) {\n            const uploadData = await uploadResponse.json();\n            docId = uploadData.docId;\n            uploadUrl = uploadData.uploadUrl;\n            downloadUrl = uploadData.downloadUrl;\n            testResults.upload = !!(docId && uploadUrl);\n            console.log(`   ✅ Upload endpoint works: ${docId}`);\n        } else {\n            const errorText = await uploadResponse.text();\n            console.log(`   ❌ Upload failed: ${uploadResponse.status} - ${errorText}`);\n        }\n    } catch (error) {\n        console.log(`   ❌ Upload error: ${error.message}`);\n    }\n    \n    // Test 4: S3 Upload\n    if (uploadUrl) {\n        console.log('\n4. ☁️  Testing S3 upload...');\n        try {\n            const s3Response = await fetch(uploadUrl, {\n                method: 'PUT',\n                headers: { 'Content-Type': 'text/plain' },\n                body: 'This is a comprehensive test document for DocumentGPT.\\n\\nIt tests the full A-Z user journey from upload to chat.'\n            });\n            \n            testResults.s3Upload = s3Response.ok;\n            console.log(`   ✅ S3 upload: ${s3Response.status}`);\n        } catch (error) {\n            console.log(`   ❌ S3 upload error: ${error.message}`);\n        }\n    }\n    \n    // Test 5: Processing Wait\n    if (testResults.s3Upload) {\n        console.log('\n5. ⏳ Waiting for processing...');\n        await new Promise(resolve => setTimeout(resolve, 8000));\n        testResults.processing = true;\n        console.log('   ✅ Processing wait completed');\n    }\n    \n    // Test 6: Status Check\n    if (docId && testResults.processing) {\n        console.log('\n6. 📊 Testing status endpoint...');\n        try {\n            const statusResponse = await fetch(`https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/status?docId=${docId}`, {\n                headers: {\n                    'x-api-key': 'dk-test-key-123',\n                    'x-user-id': 'frontend-user'\n                }\n            });\n            \n            if (statusResponse.ok) {\n                const statusData = await statusResponse.json();\n                testResults.status = true;\n                console.log(`   ✅ Status check: ${statusData.phase} - ${statusData.message}`);\n            } else {\n                const errorText = await statusResponse.text();\n                console.log(`   ❌ Status failed: ${statusResponse.status} - ${errorText}`);\n            }\n        } catch (error) {\n            console.log(`   ❌ Status error: ${error.message}`);\n        }\n    }\n    \n    // Test 7: Chat\n    if (docId && testResults.status) {\n        console.log('\n7. 💬 Testing chat endpoint...');\n        try {\n            const chatResponse = await fetch('https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/chat', {\n                method: 'POST',\n                headers: {\n                    'Content-Type': 'application/json',\n                    'x-api-key': 'dk-test-key-123',\n                    'x-user-id': 'frontend-user'\n                },\n                body: JSON.stringify({\n                    question: 'What is this document about?',\n                    docId: docId\n                })\n            });\n            \n            if (chatResponse.ok) {\n                const chatData = await chatResponse.json();\n                testResults.chat = true;\n                console.log(`   ✅ Chat works: ${chatData.answer ? 'Got response' : 'No response'}`);\n            } else {\n                const errorText = await chatResponse.text();\n                console.log(`   ❌ Chat failed: ${chatResponse.status} - ${errorText}`);\n            }\n        } catch (error) {\n            console.log(`   ❌ Chat error: ${error.message}`);\n        }\n    }\n    \n    // Summary\n    console.log('\\n📋 TEST SUMMARY');\n    console.log('================');\n    const passed = Object.values(testResults).filter(Boolean).length;\n    const total = Object.keys(testResults).length;\n    \n    Object.entries(testResults).forEach(([test, result]) => {\n        console.log(`${result ? '✅' : '❌'} ${test}`);\n    });\n    \n    console.log(`\\n🎯 Overall: ${passed}/${total} tests passed`);\n    \n    if (passed === total) {\n        console.log('🎉 ALL TESTS PASSED - System is working!');\n    } else {\n        console.log('⚠️  Some tests failed - Issues need fixing');\n    }\n}\n\nfullAZTest();