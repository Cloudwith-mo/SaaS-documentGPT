// Mini Test 1: API Endpoint Health
async function testAPIHealth() {
    console.log('🔍 Mini Test 1: API Endpoint Health');
    
    const endpoints = [
        'https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/upload',
        'https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/status',
        'https://kufufm7r9a.execute-api.us-east-1.amazonaws.com/prod/chat'
    ];
    
    for (const endpoint of endpoints) {
        try {
            const response = await fetch(endpoint, {
                method: 'OPTIONS',
                headers: {
                    'Origin': 'https://documentgpt.io'
                }
            });
            console.log(`${endpoint}: ${response.status} ${response.statusText}`);
        } catch (error) {
            console.log(`${endpoint}: ERROR - ${error.message}`);
        }
    }
}

testAPIHealth();