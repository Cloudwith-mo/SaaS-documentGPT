// Test Presign Endpoint Directly
async function testPresignEndpoint() {
    console.log('🔍 Testing /presign endpoint directly...');
    
    const response = await fetch('https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/presign', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'frontend-user'
        },
        body: JSON.stringify({
            filename: 'presign-test.txt',
            contentType: 'text/plain'
        })
    });
    
    console.log(`Presign endpoint: ${response.status} ${response.statusText}`);
    
    if (response.ok) {
        const data = await response.json();
        console.log(`✅ Presign works! DocId: ${data.docId}`);
        return data;
    } else {
        const errorText = await response.text();
        console.log(`❌ Presign error: ${errorText}`);
        return null;
    }
}

testPresignEndpoint();