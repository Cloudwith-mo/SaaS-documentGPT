// Advanced Simulated User Test
const API_BASE = 'https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod';
const WEBSITE_URL = 'https://documentgpt.io/';

class SimulatedUserTest {
    constructor() {
        this.results = [];
        this.sessionId = 'sim-user-' + Date.now();
    }

    log(test, status, message, data = null) {
        const result = { test, status, message, data, timestamp: new Date().toISOString() };
        this.results.push(result);
        console.log(`${status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : '⏳'} ${test}: ${message}`);
        if (data) console.log('   Data:', JSON.stringify(data, null, 2));
    }

    async test(name, fn) {
        try {
            this.log(name, 'START', 'Running test...');
            const result = await fn();
            this.log(name, 'PASS', 'Test completed successfully', result);
            return result;
        } catch (error) {
            this.log(name, 'FAIL', error.message, { error: error.message });
            throw error;
        }
    }

    // Test 1: UI Enhancement Verification
    async testUIEnhancements() {
        return await this.test('UI Enhancements', async () => {
            const response = await fetch(WEBSITE_URL);
            const html = await response.text();
            
            const enhancements = {
                gpt4oBadge: (html.match(/GPT-4o/g) || []).length,
                newChatButton: (html.match(/New Chat/g) || []).length,
                attachButtons: (html.match(/📎/g) || []).length,
                searchPlaceholder: html.includes('Search anything'),
                suggestionButtons: (html.match(/Summarize the document|key points|important dates|totals with currency/g) || []).length,
                themeToggle: (html.match(/☀️|🌙|🌓/g) || []).length,
                copyButtons: html.includes('Copy'),
                assistantToolsRemoved: !html.includes('Legal/Finance') && !html.includes('Tech/Design')
            };

            // Verify all enhancements are present
            if (enhancements.gpt4oBadge < 2) throw new Error('GPT-4o badge missing');
            if (enhancements.newChatButton < 1) throw new Error('New Chat button missing');
            if (enhancements.attachButtons < 2) throw new Error('Attach buttons missing');
            if (!enhancements.searchPlaceholder) throw new Error('Search placeholder missing');
            if (enhancements.suggestionButtons < 4) throw new Error('Suggestion buttons missing');
            if (enhancements.themeToggle < 3) throw new Error('Theme toggle missing');
            if (!enhancements.copyButtons) throw new Error('Copy buttons missing');
            if (!enhancements.assistantToolsRemoved) throw new Error('Assistant tools not removed');

            return enhancements;
        });
    }

    // Test 2: User Journey - New User Experience
    async testNewUserJourney() {
        return await this.test('New User Journey', async () => {
            // Step 1: User visits site (already tested above)
            
            // Step 2: User tries chat without document
            const chatResponse = await fetch(`${API_BASE}/rag-chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: 'Hello, I\'m a new user. What can you help me with?',
                    docId: null,
                    sessionId: this.sessionId
                })
            });
            
            const chatData = await chatResponse.json();
            if (!chatData.answer) throw new Error('No chat response');
            if (chatData.mode !== 'general_ai') throw new Error('Wrong chat mode');
            
            return {
                chatWorking: true,
                mode: chatData.mode,
                answerLength: chatData.answer.length
            };
        });
    }

    // Test 3: User Journey - Document Upload
    async testDocumentUpload() {
        return await this.test('Document Upload', async () => {
            // Step 1: Request upload URL
            const uploadResponse = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': 'dk-test-key-123',
                    'x-user-id': this.sessionId
                },
                body: JSON.stringify({
                    filename: 'user-test-doc.txt',
                    contentType: 'text/plain'
                })
            });

            if (!uploadResponse.ok) throw new Error('Upload request failed');
            
            const uploadData = await uploadResponse.json();
            if (!uploadData.docId) throw new Error('No document ID returned');
            if (!uploadData.uploadUrl) throw new Error('No upload URL returned');

            // Step 2: Simulate file upload to S3
            const testContent = 'This is a test document uploaded by a simulated user. It contains sample content for testing the document processing and chat functionality.';
            
            const s3Response = await fetch(uploadData.uploadUrl, {
                method: 'PUT',
                headers: { 'Content-Type': 'text/plain' },
                body: testContent
            });

            if (!s3Response.ok) throw new Error('S3 upload failed');

            return {
                docId: uploadData.docId,
                uploadSuccess: true,
                contentLength: testContent.length
            };
        });
    }

    // Test 4: User Journey - Chat with Document
    async testChatWithDocument() {
        return await this.test('Chat with Document', async () => {
            // Use existing processed document for reliable testing
            const docId = 'doc_1758376193835_c767nofb67v';
            
            const questions = [
                'What is this document about?',
                'When was Microsoft founded?',
                'What are Microsoft\'s main products?'
            ];

            const results = [];
            
            for (const question of questions) {
                const response = await fetch(`${API_BASE}/rag-chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question,
                        docId,
                        sessionId: this.sessionId
                    })
                });

                const data = await response.json();
                if (!data.answer) throw new Error(`No answer for: ${question}`);
                
                results.push({
                    question,
                    hasContext: data.hasContext,
                    answerLength: data.answer.length
                });
            }

            return results;
        });
    }

    // Test 5: User Journey - UI Interactions
    async testUIInteractions() {
        return await this.test('UI Interactions', async () => {
            const html = await fetch(WEBSITE_URL).then(r => r.text());
            
            const interactions = {
                canToggleTheme: html.includes('setTheme'),
                canSwitchTabs: html.includes('tab=\'upload\'') && html.includes('tab=\'chat\''),
                canStartNewChat: html.includes('newChat()'),
                canLoadRecentChat: html.includes('loadChat('),
                canZoomDocument: html.includes('zoom + 10') && html.includes('zoom - 10'),
                canSearchDocument: html.includes('searchInDocument()'),
                canUploadFiles: html.includes('handleFileSelect'),
                canSendMessages: html.includes('handleSendMessage'),
                canUseSuggestions: html.includes('onclick="chat(') && html.includes('Summarize the document')
            };

            const missingInteractions = Object.entries(interactions)
                .filter(([key, value]) => !value)
                .map(([key]) => key);

            if (missingInteractions.length > 0) {
                throw new Error(`Missing interactions: ${missingInteractions.join(', ')}`);
            }

            return interactions;
        });
    }

    // Test 6: User Journey - Session Persistence
    async testSessionPersistence() {
        return await this.test('Session Persistence', async () => {
            const html = await fetch(WEBSITE_URL).then(r => r.text());
            
            const persistence = {
                savesMessages: html.includes('dgpt:messages'),
                savesSession: html.includes('dgpt:sessionId'),
                savesTheme: html.includes('dgpt:theme'),
                savesDocument: html.includes('dgpt:docId'),
                savesRecentChats: html.includes('dgpt:recentChats'),
                restoresState: html.includes('localStorage.getItem')
            };

            const missingPersistence = Object.entries(persistence)
                .filter(([key, value]) => !value)
                .map(([key]) => key);

            if (missingPersistence.length > 0) {
                throw new Error(`Missing persistence: ${missingPersistence.join(', ')}`);
            }

            return persistence;
        });
    }

    // Run all tests
    async runAllTests() {
        console.log('🤖 Starting Advanced Simulated User Test');
        console.log('=========================================');

        const testSuite = [
            () => this.testUIEnhancements(),
            () => this.testNewUserJourney(),
            () => this.testDocumentUpload(),
            () => this.testChatWithDocument(),
            () => this.testUIInteractions(),
            () => this.testSessionPersistence()
        ];

        let passed = 0;
        let failed = 0;

        for (const testFn of testSuite) {
            try {
                await testFn();
                passed++;
            } catch (error) {
                failed++;
            }
            console.log(''); // Add spacing between tests
        }

        // Final report
        console.log('📊 SIMULATED USER TEST REPORT');
        console.log('==============================');
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`📈 Success Rate: ${Math.round((passed / (passed + failed)) * 100)}%`);

        const isPassing = failed === 0;
        console.log(`\\n🎯 USER EXPERIENCE: ${isPassing ? '✅ EXCELLENT - Ready for real users' : '❌ NEEDS IMPROVEMENT'}`);
        
        return {
            passed,
            failed,
            successRate: Math.round((passed / (passed + failed)) * 100),
            isPassing,
            results: this.results
        };
    }
}

// Export for Node.js or run directly
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SimulatedUserTest;
} else {
    const tester = new SimulatedUserTest();
    tester.runAllTests().then(result => {
        console.log('Simulated user testing complete!', result);
    });
}