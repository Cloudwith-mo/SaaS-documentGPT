// Mini Test 5: Processing Pipeline to 100%
async function miniTestProcessing100() {
    console.log('🔍 Mini Test 5: Processing Pipeline to 100%');
    
    // Upload new document
    const uploadResponse = await fetch('https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/presign', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'frontend-user'
        },
        body: JSON.stringify({
            filename: 'processing-test.txt',
            contentType: 'text/plain'
        })
    });
    
    const uploadData = await uploadResponse.json();
    console.log(`Upload: ${uploadData.docId}`);
    
    // Upload to S3
    await fetch(uploadData.uploadUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'text/plain' },
        body: 'Test document for processing pipeline verification.'
    });
    
    console.log('File uploaded, checking status...');
    
    // Check status multiple times
    for (let i = 0; i < 10; i++) {
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        const statusResponse = await fetch(`https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/documents?docId=${uploadData.docId}`, {
            headers: {
                'x-api-key': 'dk-test-key-123',
                'x-user-id': 'frontend-user'
            }
        });
        
        if (statusResponse.ok) {
            const statusData = await statusResponse.json();
            console.log(`Check ${i+1}: ${JSON.stringify(statusData)}`);
            
            if (statusData.documents && statusData.documents.length > 0) {
                const doc = statusData.documents[0];
                if (doc.status === 'ready' || doc.progress === 100) {
                    console.log('✅ Processing complete!');
                    return;
                }
            }
        } else {
            console.log(`Status error: ${statusResponse.status}`);
        }
    }
    
    console.log('⚠️ Processing still in progress after 30 seconds');
}

miniTestProcessing100();