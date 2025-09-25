// Fix Test 3: Test Correct API Gateway
async function testCorrectAPI() {
    console.log('🔍 Fix Test 3: Test Correct API Gateway');
    
    try {
        console.log('Testing upload with correct API...');
        const response = await fetch('https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/upload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': 'dk-test-key-123',
                'x-user-id': 'frontend-user'
            },
            body: JSON.stringify({
                filename: 'fix-test.txt',
                contentType: 'text/plain'
            })
        });
        
        console.log(`Upload: ${response.status} ${response.statusText}`);
        
        if (response.ok) {
            const data = await response.json();
            console.log(`✅ Upload works! DocId: ${data.docId}`);
            
            // Test S3 upload
            if (data.uploadUrl) {
                console.log('Testing S3 upload...');
                const s3Response = await fetch(data.uploadUrl, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'text/plain' },
                    body: 'Test content for fix verification'
                });
                console.log(`S3: ${s3Response.status}`);
                
                // Test status after delay
                console.log('Waiting and testing status...');
                await new Promise(resolve => setTimeout(resolve, 5000));
                
                const statusResponse = await fetch(`https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/status?docId=${data.docId}`, {
                    headers: {
                        'x-api-key': 'dk-test-key-123',
                        'x-user-id': 'frontend-user'
                    }
                });
                console.log(`Status: ${statusResponse.status}`);
                
                if (statusResponse.ok) {
                    const statusData = await statusResponse.json();
                    console.log(`✅ Status works! Phase: ${statusData.phase}`);
                } else {
                    const errorText = await statusResponse.text();
                    console.log(`Status error: ${errorText}`);
                }
            }
        } else {
            const errorText = await response.text();
            console.log(`Upload error: ${errorText}`);
        }
    } catch (error) {
        console.log(`Error: ${error.message}`);
    }
}

testCorrectAPI();