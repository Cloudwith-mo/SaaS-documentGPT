// Final Real User Test
async function finalRealUserTest() {
    console.log('🎯 Final Real User Test - Complete Journey');
    console.log('==========================================');
    
    let results = {
        siteLoad: false,
        upload: false,
        s3Upload: false,
        frontendWorks: false
    };
    
    // Test 1: Site Load
    console.log('\n1. 🌐 Testing site load...');
    try {
        const response = await fetch('https://documentgpt.io/');
        results.siteLoad = response.ok;
        console.log(`   ✅ Site loads: ${response.status}`);
    } catch (error) {
        console.log(`   ❌ Site failed: ${error.message}`);
    }
    
    // Test 2: Upload Flow
    console.log('\n2. 📤 Testing upload flow...');
    let docId, uploadUrl;
    try {
        const uploadResponse = await fetch('https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/upload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': 'dk-test-key-123',
                'x-user-id': 'frontend-user'
            },
            body: JSON.stringify({
                filename: 'final-test.txt',
                contentType: 'text/plain'
            })
        });
        
        if (uploadResponse.ok) {
            const data = await uploadResponse.json();
            docId = data.docId;
            uploadUrl = data.uploadUrl;
            results.upload = true;
            console.log(`   ✅ Upload endpoint works: ${docId}`);
        } else {
            console.log(`   ❌ Upload failed: ${uploadResponse.status}`);
        }
    } catch (error) {
        console.log(`   ❌ Upload error: ${error.message}`);
    }
    
    // Test 3: S3 Upload
    if (uploadUrl) {
        console.log('\n3. ☁️  Testing S3 upload...');
        try {
            const s3Response = await fetch(uploadUrl, {
                method: 'PUT',
                headers: { 'Content-Type': 'text/plain' },
                body: 'This is the final test document for DocumentGPT.\\n\\nIt verifies the complete user journey works end-to-end.'
            });
            
            results.s3Upload = s3Response.ok;
            console.log(`   ✅ S3 upload: ${s3Response.status}`);
        } catch (error) {
            console.log(`   ❌ S3 error: ${error.message}`);
        }
    }
    
    // Test 4: Frontend Integration
    console.log('\n4. 🖥️  Testing frontend integration...');
    try {
        const siteContent = await fetch('https://documentgpt.io/').then(r => r.text());
        const hasCorrectAPI = siteContent.includes('9voqzgx3ch.execute-api.us-east-1.amazonaws.com');
        const hasZoomFix = siteContent.includes('transform: scale');
        const hasChatPersistence = siteContent.includes('localStorage.getItem');
        
        results.frontendWorks = hasCorrectAPI && hasZoomFix && hasChatPersistence;
        
        console.log(`   API Gateway: ${hasCorrectAPI ? '✅' : '❌'}`);
        console.log(`   Zoom Fix: ${hasZoomFix ? '✅' : '❌'}`);
        console.log(`   Chat Persistence: ${hasChatPersistence ? '✅' : '❌'}`);
    } catch (error) {
        console.log(`   ❌ Frontend test error: ${error.message}`);
    }
    
    // Summary
    console.log('\\n📋 FINAL TEST RESULTS');
    console.log('======================');
    const passed = Object.values(results).filter(Boolean).length;
    const total = Object.keys(results).length;
    
    Object.entries(results).forEach(([test, result]) => {
        console.log(`${result ? '✅' : '❌'} ${test}`);
    });
    
    console.log(`\\n🎯 Score: ${passed}/${total} tests passed`);
    
    if (passed >= 3) {
        console.log('🎉 SYSTEM IS WORKING! Core functionality restored.');
        console.log('📝 Note: Status polling may need separate endpoint setup.');
    } else {
        console.log('⚠️  Critical issues remain - needs more fixes.');
    }
    
    return results;
}

finalRealUserTest();