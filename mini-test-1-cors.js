// Mini Test 1: Check actual CORS headers from API Gateway
async function miniTestCORS() {
    console.log('🔍 Mini Test 1: CORS Headers');
    
    // Test OPTIONS request (preflight)
    const optionsResponse = await fetch('https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/presign', {
        method: 'OPTIONS',
        headers: {
            'Origin': 'https://documentgpt.io',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type,x-api-key,x-user-id'
        }
    });
    
    console.log(`OPTIONS: ${optionsResponse.status}`);
    console.log(`Allow-Headers: ${optionsResponse.headers.get('Access-Control-Allow-Headers')}`);
    console.log(`Allow-Origin: ${optionsResponse.headers.get('Access-Control-Allow-Origin')}`);
    console.log(`Allow-Methods: ${optionsResponse.headers.get('Access-Control-Allow-Methods')}`);
}

miniTestCORS();