exports.handler = async (event) => {
    return {
        statusCode: 200,
        headers: {
            'Content-Type': 'text/html',
            'Access-Control-Allow-Origin': '*'
        },
        body: `
<!DOCTYPE html>
<html>
<head><title>DocumentGPT API</title></head>
<body style="font-family:Arial;max-width:600px;margin:50px auto;padding:20px;">
    <h1>🚀 DocumentGPT API</h1>
    <p><strong>Status:</strong> ✅ Online</p>
    
    <h3>📋 Available Endpoints:</h3>
    <ul>
        <li><code>POST /upload</code> - Upload documents</li>
        <li><code>POST /rag-chat</code> - Chat with documents</li>
    </ul>
    
    <h3>💬 Test Chat:</h3>
    <textarea id="q" placeholder="Ask a question..." style="width:100%;height:60px;"></textarea><br>
    <button onclick="chat()" style="padding:10px;background:#007cba;color:white;border:none;">Ask</button>
    <div id="r" style="margin:20px 0;padding:15px;background:#f5f5f5;"></div>
    
    <script>
    async function chat() {
        const q = document.getElementById('q').value;
        if (!q) return;
        
        const res = await fetch('/prod/rag-chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question: q, docId: 'doc_1758376193835_c767nofb67v'})
        });
        
        const data = await res.json();
        document.getElementById('r').innerHTML = data.answer || data.error;
    }
    </script>
</body>
</html>`
    };
};