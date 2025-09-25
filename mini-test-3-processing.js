// Mini Test 3: Why Processing Stops at 10%
async function miniTestProcessing() {
    console.log('🔍 Mini Test 3: Processing Pipeline');
    
    // Check if S3 trigger exists
    console.log('Checking S3 trigger...');
    
    // Check if documents endpoint works
    const docId = 'doc_1758651347757_d39effad550f';
    const statusResponse = await fetch(`https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/documents?docId=${docId}`, {
        headers: {
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'frontend-user'
        }
    });
    
    console.log(`Status endpoint: ${statusResponse.status}`);
    
    if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        console.log(`Status data:`, statusData);
    } else {
        console.log(`Status error: ${await statusResponse.text()}`);
    }
}

miniTestProcessing();