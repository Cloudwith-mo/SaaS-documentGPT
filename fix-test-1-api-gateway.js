// Fix Test 1: Check API Gateway Configuration
async function testAPIGateway() {
    console.log('🔍 Fix Test 1: API Gateway Configuration');
    
    // Test different endpoints to see which are working
    const endpoints = [
        { name: 'upload', path: '/upload', method: 'POST' },
        { name: 'status', path: '/status', method: 'GET' },
        { name: 'chat', path: '/chat', method: 'POST' },
        { name: 'root', path: '/', method: 'GET' }
    ];
    
    for (const endpoint of endpoints) {
        try {
            const url = `https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod${endpoint.path}`;
            const response = await fetch(url, {
                method: 'OPTIONS',
                headers: { 'Origin': 'https://documentgpt.io' }
            });
            console.log(`${endpoint.name}: ${response.status} ${response.statusText}`);
        } catch (error) {
            console.log(`${endpoint.name}: ERROR - ${error.message}`);
        }
    }
}

testAPIGateway();