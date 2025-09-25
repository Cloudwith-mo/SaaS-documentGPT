async function simpleAZTest() {
    console.log('🚀 Simple A-Z Test');
    
    // Test 1: Upload
    console.log('1. Testing upload...');
    const uploadResponse = await fetch('https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/upload', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'frontend-user'
        },
        body: JSON.stringify({
            filename: 'simple-test.txt',
            contentType: 'text/plain'
        })
    });
    
    console.log(`Upload: ${uploadResponse.status}`);
    
    if (uploadResponse.ok) {
        const data = await uploadResponse.json();
        console.log(`DocId: ${data.docId}`);
        
        // Test 2: S3 Upload
        if (data.uploadUrl) {
            console.log('2. Testing S3 upload...');
            const s3Response = await fetch(data.uploadUrl, {
                method: 'PUT',
                headers: { 'Content-Type': 'text/plain' },
                body: 'Test content'
            });
            console.log(`S3: ${s3Response.status}`);
            
            // Test 3: Status after delay
            console.log('3. Waiting and testing status...');
            await new Promise(resolve => setTimeout(resolve, 5000));
            
            const statusResponse = await fetch(`https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/status?docId=${data.docId}`, {
                headers: {
                    'x-api-key': 'dk-test-key-123',
                    'x-user-id': 'frontend-user'
                }
            });
            console.log(`Status: ${statusResponse.status}`);
            
            if (statusResponse.ok) {
                const statusData = await statusResponse.json();
                console.log(`Phase: ${statusData.phase}`);
            }
        }
    } else {
        const errorText = await uploadResponse.text();
        console.log(`Upload error: ${errorText}`);
    }
}

simpleAZTest();