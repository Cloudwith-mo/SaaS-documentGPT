// Debug Chat Endpoint in Node.js
async function debugChat() {
    console.log('🔍 Debug Chat in Node.js');
    
    try {
        const response = await fetch('https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod/rag-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: 'Test question',
                docId: 'test-doc-123'
            })
        });
        
        console.log(`Status: ${response.status}`);
        console.log(`Headers: ${JSON.stringify([...response.headers])}`);
        
        const text = await response.text();
        console.log(`Response: ${text}`);
        
        if (response.ok) {
            const data = JSON.parse(text);
            console.log(`✅ Answer: ${data.answer}`);
        }
        
    } catch (error) {
        console.log(`❌ Error: ${error.message}`);
        console.log(`Stack: ${error.stack}`);
    }
}

debugChat();