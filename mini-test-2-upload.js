// Mini Test 2: Real Upload with Browser Headers
async function miniTestUpload() {
    console.log('🔍 Mini Test 2: Real Upload');
    
    const response = await fetch('https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/presign', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': 'dk-test-key-123',
            'x-user-id': 'frontend-user'
        },
        body: JSON.stringify({
            filename: 'sample_bank_statement_3.jpg',
            contentType: 'image/jpeg'
        })
    });
    
    console.log(`Upload: ${response.status}`);
    
    if (response.ok) {
        const data = await response.json();
        console.log(`✅ Upload works! DocId: ${data.docId}`);
        
        // Test S3 upload
        const s3Response = await fetch(data.uploadUrl, {
            method: 'PUT',
            headers: { 'Content-Type': 'image/jpeg' },
            body: 'fake-image-data'
        });
        
        console.log(`S3: ${s3Response.status}`);
        return data.docId;
    } else {
        console.log(`❌ Upload failed: ${await response.text()}`);
        return null;
    }
}

miniTestUpload();