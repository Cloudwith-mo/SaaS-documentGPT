// Fix Test 2: Find Working API Gateway
async function findWorkingAPI() {
    console.log('🔍 Fix Test 2: Find Working API Gateway');
    
    const apiIds = ['9voqzgx3ch', 'brepwqlzqc', 'ns7ycm3h04'];
    
    for (const apiId of apiIds) {
        console.log(`\nTesting API: ${apiId}`);
        
        try {
            // Test upload endpoint
            const uploadUrl = `https://${apiId}.execute-api.us-east-1.amazonaws.com/prod/upload`;
            const response = await fetch(uploadUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': 'dk-test-key-123',
                    'x-user-id': 'test'
                },
                body: JSON.stringify({
                    filename: 'test.txt',
                    contentType: 'text/plain'
                })
            });
            
            console.log(`  Upload: ${response.status} ${response.statusText}`);
            
            if (response.ok) {
                const data = await response.json();
                console.log(`  ✅ Working API found: ${apiId}`);
                console.log(`  DocId: ${data.docId}`);
                return apiId;
            } else if (response.status !== 503) {
                const errorText = await response.text();
                console.log(`  Response: ${errorText}`);
            }
            
        } catch (error) {
            console.log(`  Error: ${error.message}`);
        }
    }
    
    console.log('\n❌ No working API found');
    return null;
}

findWorkingAPI();