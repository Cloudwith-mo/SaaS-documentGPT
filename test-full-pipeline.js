// Test Full Pipeline with OpenAI Credits Available
async function testFullPipeline() {
    console.log('🎯 Testing Full Pipeline - Credits Available');
    
    // Upload real-test-doc.txt content
    const uploadResponse = await fetch('https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/presign', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'frontend-user'
        },
        body: JSON.stringify({
            filename: 'real-test-doc.txt',
            contentType: 'text/plain'
        })
    });
    
    if (!uploadResponse.ok) {
        console.log(`❌ Upload failed: ${uploadResponse.status}`);
        return;
    }
    
    const uploadData = await uploadResponse.json();
    console.log(`✅ Upload: ${uploadData.docId}`);
    
    if (!uploadData.uploadUrl) {
        console.log(`❌ No upload URL: ${JSON.stringify(uploadData)}`);
        return;
    }
    
    // Upload Microsoft content
    const s3Response = await fetch(uploadData.uploadUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'text/plain' },
        body: 'Microsoft Corporation was founded in 1975 by Bill Gates and Paul Allen. The company is headquartered in Redmond, Washington. Microsoft is known for developing the Windows operating system, Microsoft Office suite, and Azure cloud services. The company went public in 1986 and became one of the most valuable companies in the world.'
    });
    
    console.log(`✅ S3 Upload: ${s3Response.status}`);
    
    // Monitor processing to 100%
    console.log('🔄 Monitoring processing...');
    for (let i = 0; i < 30; i++) {
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        const statusResponse = await fetch(`https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/documents?docId=${uploadData.docId}`, {
            headers: {
                'x-api-key': 'dk-test-key-123',
                'x-user-id': 'frontend-user'
            }
        });
        
        if (statusResponse.ok) {
            const statusData = await statusResponse.json();
            console.log(`Check ${i+1}: ${JSON.stringify(statusData)}`);
            
            if (statusData.documents && statusData.documents.length > 0) {
                const doc = statusData.documents[0];
                if (doc.status === 'ready') {
                    console.log('🎉 Processing Complete - 100%!');
                    
                    // Test chat
                    const chatResponse = await fetch('https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/rag-chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'x-api-key': 'dk-test-key-123',
                            'x-user-id': 'frontend-user'
                        },
                        body: JSON.stringify({
                            question: 'When was Microsoft founded?',
                            docId: uploadData.docId
                        })
                    });
                    
                    if (chatResponse.ok) {
                        const chatData = await chatResponse.json();
                        console.log(`✅ Chat works: ${chatData.answer}`);
                    }
                    
                    return;
                }
            }
        }
    }
    
    console.log('⚠️ Still processing after 90 seconds');
}

testFullPipeline();