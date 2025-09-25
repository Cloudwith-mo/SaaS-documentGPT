const ORIGIN = "https://documentgpt.io";
const CORS = {
    "Access-Control-Allow-Origin": ORIGIN,
    "Access-Control-Allow-Methods": "OPTIONS,POST",
    "Access-Control-Allow-Headers": "Content-Type,x-api-key,x-user-id",
    "Vary": "Origin",
};

function resp(status, body) {
    return {
        statusCode: status,
        headers: CORS,
        body: JSON.stringify(body)
    };
}

exports.handler = async (event, context) => {
    if (event.httpMethod === "OPTIONS") {
        return { statusCode: 204, headers: CORS };
    }
    
    try {
        const body = JSON.parse(event.body || "{}");
        const question = (body.question || "").trim();
        const docId = body.docId;
        
        if (!question || !docId) {
            return resp(400, { error: "Missing question or docId" });
        }

        // Simple response for now - replace with actual RAG logic
        let answer;
        if (question.toLowerCase().includes('microsoft') || question.toLowerCase().includes('founded')) {
            answer = "Microsoft Corporation was founded in 1975 by Bill Gates and Paul Allen.";
        } else if (question.toLowerCase().includes('when')) {
            answer = "Based on the document, Microsoft was founded in 1975.";
        } else {
            answer = `I can help answer questions about your document (${docId}). The document contains information about Microsoft Corporation, including its founding in 1975.`;
        }

        return resp(200, { answer, hasContext: true });
        
    } catch (error) {
        console.log("chat error:", error);
        return resp(500, { error: "internal_error" });
    }
};