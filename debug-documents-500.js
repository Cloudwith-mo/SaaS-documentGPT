// Debug Documents Endpoint 500 Error
async function debugDocuments500() {
    console.log('🔍 Debug: Documents Endpoint 500 Error');
    
    const docId = 'doc_1758655295800_5e555a66cd20';
    
    const response = await fetch(`https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/documents?docId=${docId}`, {
        headers: {
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'frontend-user'
        }
    });
    
    console.log(`Status: ${response.status}`);
    console.log(`Headers: ${JSON.stringify([...response.headers])}`);
    
    const text = await response.text();
    console.log(`Response: ${text}`);
}

debugDocuments500();