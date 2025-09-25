// Mini Test 4: Documents Endpoint CORS
async function miniTestDocumentsCORS() {
    console.log('🔍 Mini Test 4: Documents Endpoint CORS');
    
    // Test OPTIONS for documents endpoint
    const optionsResponse = await fetch('https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/documents', {
        method: 'OPTIONS',
        headers: {
            'Origin': 'https://documentgpt.io',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'x-api-key,x-user-id'
        }
    });
    
    console.log(`Documents OPTIONS: ${optionsResponse.status}`);
    console.log(`Allow-Headers: ${optionsResponse.headers.get('Access-Control-Allow-Headers')}`);
    console.log(`Allow-Methods: ${optionsResponse.headers.get('Access-Control-Allow-Methods')}`);
}

miniTestDocumentsCORS();