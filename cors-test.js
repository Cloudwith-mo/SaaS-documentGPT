// Test CORS with exact browser headers
async function corsTest() {
    console.log('Testing CORS with browser headers...');
    
    const response = await fetch('https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/presign', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'frontend-user'
        },
        body: JSON.stringify({
            filename: 'cors-test.txt',
            contentType: 'text/plain'
        })
    });
    
    console.log(`Status: ${response.status}`);
    console.log(`CORS Headers: ${response.headers.get('Access-Control-Allow-Headers')}`);
    
    if (response.ok) {
        const data = await response.json();
        console.log(`✅ CORS fixed! DocId: ${data.docId}`);
    } else {
        console.log(`❌ Still failing: ${await response.text()}`);
    }
}

corsTest();