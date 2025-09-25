// Mini Test 4: Debug Upload Response
async function debugUploadResponse() {
    console.log('🔍 Mini Test 4: Debug Upload Response');
    
    const response = await fetch('https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/upload', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'frontend-user'
        },
        body: JSON.stringify({
            filename: 'debug-test.txt',
            contentType: 'text/plain'
        })
    });
    
    console.log(`Response status: ${response.status}`);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));
    
    const responseText = await response.text();
    console.log('Raw response:', responseText);
    
    try {
        const data = JSON.parse(responseText);
        console.log('Parsed data:', data);
    } catch (e) {
        console.log('Failed to parse JSON:', e.message);
    }
}

debugUploadResponse();