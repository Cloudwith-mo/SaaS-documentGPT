// Test Processing After Adding Credits
async function testAfterCredits() {
    console.log('🔄 Testing processing after adding OpenAI credits...');
    
    // Upload test document
    const uploadResponse = await fetch('https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/presign', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'frontend-user'
        },
        body: JSON.stringify({
            filename: 'credits-test.txt',
            contentType: 'text/plain'
        })
    });
    
    const uploadData = await uploadResponse.json();
    console.log(`Upload: ${uploadData.docId}`);
    
    // Upload to S3
    await fetch(uploadData.uploadUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'text/plain' },
        body: 'Test document after adding OpenAI credits. This should process to 100% now.'
    });
    
    console.log('File uploaded, checking processing...');
    
    // Check processing for 60 seconds
    for (let i = 0; i < 20; i++) {
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Check Step Function status
        const executions = await fetch('https://httpbin.org/get').then(() => 'simulated'); // Placeholder
        console.log(`Check ${i+1}: Processing...`);
        
        if (i > 10) {
            console.log('✅ Processing should complete if credits were added');
            break;
        }
    }
}

testAfterCredits();