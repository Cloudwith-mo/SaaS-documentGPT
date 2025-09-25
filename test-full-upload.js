const fs = require('fs');

async function testFullUpload() {
    console.log('🚀 Testing full upload flow...');
    
    // Step 1: Get upload URL
    console.log('1. Getting upload URL...');
    const uploadResponse = await fetch('https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/upload', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'test-user'
        },
        body: JSON.stringify({
            filename: 'test-document.txt',
            contentType: 'text/plain'
        })
    });
    
    if (!uploadResponse.ok) {
        console.log(`❌ Upload URL failed: ${uploadResponse.status}`);
        return;
    }
    
    const uploadData = await uploadResponse.json();
    console.log(`✅ Got upload URL for docId: ${uploadData.docId}`);
    
    // Step 2: Upload actual file
    console.log('2. Uploading file to S3...');
    const testContent = 'This is a test document for DocumentGPT.\n\nIt contains sample text to test the processing pipeline.';
    
    const s3Response = await fetch(uploadData.uploadUrl, {
        method: 'PUT',
        headers: {
            'Content-Type': 'text/plain'
        },
        body: testContent
    });
    
    if (!s3Response.ok) {
        console.log(`❌ S3 upload failed: ${s3Response.status}`);
        return;
    }
    
    console.log('✅ File uploaded to S3');
    
    // Step 3: Wait for S3 trigger to process
    console.log('3. Waiting for S3 trigger processing...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Step 4: Check status
    console.log('4. Checking document status...');
    const statusResponse = await fetch(`https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/status?docId=${uploadData.docId}`, {
        headers: {
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'test-user'
        }
    });
    
    if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        console.log(`✅ Status check successful: ${statusData.phase} - ${statusData.message}`);
    } else {
        console.log(`❌ Status check failed: ${statusResponse.status}`);
        
        // Try to get error details
        try {
            const errorText = await statusResponse.text();
            console.log(`Error details: ${errorText}`);
        } catch (e) {
            console.log('Could not get error details');
        }
    }
    
    console.log('🎉 Full upload test completed!');
}

testFullUpload().catch(console.error);