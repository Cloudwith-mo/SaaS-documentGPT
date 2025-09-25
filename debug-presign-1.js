// Debug Step 1: Identify the Gap - What's causing 500 error?
async function debugPresignGap() {
    console.log('🔍 Debug Step 1: Identify the Gap');
    
    // Test 1: Check if function is being invoked at all
    console.log('Testing presign endpoint...');
    const response = await fetch('https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/presign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: 'debug.txt', contentType: 'text/plain' })
    });
    
    console.log(`Response: ${response.status}`);
    
    // Test 2: Check logs immediately after
    setTimeout(async () => {
        console.log('Checking logs...');
        // We'll check logs manually after this runs
    }, 2000);
}

debugPresignGap();