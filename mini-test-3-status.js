// Mini Test 3: Status Endpoint
async function testStatusEndpoint() {
    console.log('🔍 Mini Test 3: Status Endpoint');
    
    // First create a document
    const uploadResponse = await fetch('https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/upload', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'frontend-user'
        },
        body: JSON.stringify({
            filename: 'status-test.txt',
            contentType: 'text/plain'
        })
    });
    
    const uploadData = await uploadResponse.json();
    console.log(`Created docId: ${uploadData.docId}`);
    
    // Upload file to trigger processing
    await fetch(uploadData.uploadUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'text/plain' },
        body: 'Test content for status check'
    });
    
    console.log('File uploaded, waiting 3 seconds...');
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Test status endpoint
    const statusResponse = await fetch(`https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/status?docId=${uploadData.docId}`, {
        headers: {
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'frontend-user'
        }
    });
    
    console.log(`Status response: ${statusResponse.status} ${statusResponse.statusText}`);
    
    if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        console.log('Status data:', statusData);
    } else {
        const errorText = await statusResponse.text();
        console.log('Status error:', errorText);
    }
}

testStatusEndpoint();