const https = require('https');

// Test CORS preflight request
function testCORSPreflight() {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: '9voqzgx3ch.execute-api.us-east-1.amazonaws.com',
            port: 443,
            path: '/prod/upload',
            method: 'OPTIONS',
            headers: {
                'Origin': 'https://documentgpt.io',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'content-type,x-api-key,x-user-id'
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                console.log('CORS Preflight Response:');
                console.log('Status:', res.statusCode);
                console.log('Headers:', res.headers);
                resolve({
                    status: res.statusCode,
                    headers: res.headers,
                    allowedHeaders: res.headers['access-control-allow-headers']
                });
            });
        });

        req.on('error', reject);
        req.end();
    });
}

// Test actual upload request
function testUploadRequest() {
    return new Promise((resolve, reject) => {
        const postData = JSON.stringify({
            filename: 'test.txt',
            contentType: 'text/plain'
        });

        const options = {
            hostname: '9voqzgx3ch.execute-api.us-east-1.amazonaws.com',
            port: 443,
            path: '/prod/upload',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': postData.length,
                'x-api-key': 'dk-test-key-123',
                'x-user-id': 'test-user-123',
                'Origin': 'https://documentgpt.io'
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                console.log('\nUpload Request Response:');
                console.log('Status:', res.statusCode);
                console.log('Body:', data);
                resolve({
                    status: res.statusCode,
                    body: data
                });
            });
        });

        req.on('error', reject);
        req.write(postData);
        req.end();
    });
}

async function runTests() {
    try {
        console.log('Testing CORS configuration...\n');
        
        const corsResult = await testCORSPreflight();
        console.log('✓ CORS Preflight completed');
        
        if (corsResult.allowedHeaders && corsResult.allowedHeaders.includes('x-user-id')) {
            console.log('✓ x-user-id header is allowed');
        } else {
            console.log('✗ x-user-id header is NOT allowed');
            console.log('Allowed headers:', corsResult.allowedHeaders);
        }
        
        const uploadResult = await testUploadRequest();
        if (uploadResult.status === 200) {
            console.log('✓ Upload request successful');
        } else {
            console.log('✗ Upload request failed with status:', uploadResult.status);
        }
        
    } catch (error) {
        console.error('Test failed:', error.message);
    }
}

runTests();