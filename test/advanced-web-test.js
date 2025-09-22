// Advanced DocumentGPT Web Testing Suite
const API_BASE = 'https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod';
const API_KEY = 'dk-test-key-123';
const WEBSITE_URL = 'https://documentgpt.io/';

class DocumentGPTTester {
    constructor() {
        this.results = [];
        this.errors = [];
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
            this.log(name, 'FAIL', error.message, { error: error.stack });
            this.errors.push({ test: name, error });
            throw error;
        }
    }

    // Test 1: Website Accessibility
    async testWebsiteLoad() {
        return await this.test('Website Load', async () => {
            const response = await fetch(WEBSITE_URL);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const html = await response.text();
            const checks = {
                hasTitle: html.includes('<title>DocumentsGPT</title>'),
                hasAPI: html.includes('9voqzgx3ch.execute-api'),
                hasUpload: html.includes('Upload'),
                hasChat: html.includes('Ask anything'),
                hasTheme: html.includes('setTheme'),
                size: html.length
            };
            
            if (!checks.hasTitle) throw new Error('Missing title');
            if (!checks.hasAPI) throw new Error('Missing API integration');
            if (!checks.hasUpload) throw new Error('Missing upload functionality');
            
            return checks;
        });
    }

    // Test 2: API Endpoints
    async testAPIEndpoints() {
        return await this.test('API Endpoints', async () => {
            // Test root endpoint
            const rootResponse = await fetch(`${API_BASE}/`);
            if (!rootResponse.ok) throw new Error('Root endpoint failed');

            // Test upload endpoint
            const uploadResponse = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': API_KEY,
                    'x-user-id': 'test-user-' + Date.now()
                },
                body: JSON.stringify({
                    filename: 'test-doc.txt',
                    contentType: 'text/plain'
                })
            });
            
            if (!uploadResponse.ok) throw new Error('Upload endpoint failed');
            const uploadData = await uploadResponse.json();
            if (!uploadData.docId) throw new Error('No docId returned');

            // Test chat endpoint
            const chatResponse = await fetch(`${API_BASE}/rag-chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: 'What is Microsoft?',
                    docId: 'doc_1758376193835_c767nofb67v'
                })
            });
            
            if (!chatResponse.ok) throw new Error('Chat endpoint failed');
            const chatData = await chatResponse.json();
            if (!chatData.answer) throw new Error('No answer returned');

            return {
                upload: { docId: uploadData.docId, status: 'success' },
                chat: { hasContext: chatData.hasContext, answerLength: chatData.answer.length }
            };
        });
    }

    // Test 3: Upload Flow Simulation
    async testUploadFlow() {
        return await this.test('Upload Flow', async () => {
            const userId = 'test-user-' + Date.now();
            
            // Step 1: Request upload URL
            const uploadResponse = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': API_KEY,
                    'x-user-id': userId
                },
                body: JSON.stringify({
                    filename: 'advanced-test.txt',
                    contentType: 'text/plain'
                })
            });

            const uploadData = await uploadResponse.json();
            if (!uploadData.uploadUrl) throw new Error('No upload URL provided');
            if (!uploadData.docId) throw new Error('No document ID provided');

            // Step 2: Simulate file upload to S3
            const testContent = 'This is a test document for advanced testing. It contains information about testing procedures and validation methods.';
            const s3Response = await fetch(uploadData.uploadUrl, {
                method: 'PUT',
                headers: { 'Content-Type': 'text/plain' },
                body: testContent
            });

            if (!s3Response.ok) throw new Error('S3 upload failed');

            // Step 3: Wait for processing (simulate)
            await new Promise(resolve => setTimeout(resolve, 2000));

            return {
                docId: uploadData.docId,
                uploadUrl: uploadData.uploadUrl,
                s3Status: s3Response.status,
                contentLength: testContent.length
            };
        });
    }

    // Test 4: Chat Functionality
    async testChatFunctionality() {
        return await this.test('Chat Functionality', async () => {
            const testQuestions = [
                'What is Microsoft?',
                'When was Microsoft founded?',
                'What services does Microsoft offer?',
                'Where is Microsoft headquartered?'
            ];

            const results = [];
            
            for (const question of testQuestions) {
                const response = await fetch(`${API_BASE}/rag-chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question,
                        docId: 'doc_1758376193835_c767nofb67v'
                    })
                });

                if (!response.ok) throw new Error(`Chat failed for: ${question}`);
                
                const data = await response.json();
                if (!data.answer) throw new Error(`No answer for: ${question}`);

                results.push({
                    question,
                    answerLength: data.answer.length,
                    hasContext: data.hasContext,
                    responseTime: response.headers.get('x-response-time') || 'unknown'
                });

                // Small delay between requests
                await new Promise(resolve => setTimeout(resolve, 500));
            }

            return results;
        });
    }

    // Test 5: Error Handling
    async testErrorHandling() {
        return await this.test('Error Handling', async () => {
            const errorTests = [];

            // Test empty question
            try {
                const response = await fetch(`${API_BASE}/rag-chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: '', docId: 'test' })
                });
                const data = await response.json();
                errorTests.push({
                    test: 'empty_question',
                    status: data.error ? 'PASS' : 'FAIL',
                    error: data.error
                });
            } catch (e) {
                errorTests.push({ test: 'empty_question', status: 'FAIL', error: e.message });
            }

            // Test non-existent document
            try {
                const response = await fetch(`${API_BASE}/rag-chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: 'test', docId: 'non-existent-doc' })
                });
                const data = await response.json();
                errorTests.push({
                    test: 'non_existent_doc',
                    status: data.hasContext === false ? 'PASS' : 'FAIL',
                    hasContext: data.hasContext
                });
            } catch (e) {
                errorTests.push({ test: 'non_existent_doc', status: 'FAIL', error: e.message });
            }

            // Test malformed upload
            try {
                const response = await fetch(`${API_BASE}/upload`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'x-api-key': API_KEY
                    },
                    body: '{"filename":}'
                });
                const data = await response.json();
                errorTests.push({
                    test: 'malformed_upload',
                    status: data.error ? 'PASS' : 'FAIL',
                    error: data.error
                });
            } catch (e) {
                errorTests.push({ test: 'malformed_upload', status: 'PASS', error: 'Request failed as expected' });
            }

            return errorTests;
        });
    }

    // Test 6: Performance & Load
    async testPerformance() {
        return await this.test('Performance & Load', async () => {
            const concurrentRequests = 5;
            const startTime = Date.now();

            const promises = Array.from({ length: concurrentRequests }, (_, i) =>
                fetch(`${API_BASE}/rag-chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: `Performance test question ${i + 1}`,
                        docId: 'doc_1758376193835_c767nofb67v'
                    })
                }).then(r => r.json())
            );

            const results = await Promise.all(promises);
            const endTime = Date.now();
            const totalTime = endTime - startTime;

            const successCount = results.filter(r => r.answer).length;
            const avgResponseTime = totalTime / concurrentRequests;

            if (successCount < concurrentRequests * 0.8) {
                throw new Error(`Only ${successCount}/${concurrentRequests} requests succeeded`);
            }

            if (totalTime > 15000) {
                throw new Error(`Performance too slow: ${totalTime}ms for ${concurrentRequests} requests`);
            }

            return {
                totalRequests: concurrentRequests,
                successfulRequests: successCount,
                totalTime,
                avgResponseTime,
                successRate: (successCount / concurrentRequests) * 100
            };
        });
    }

    // Test 7: UI Component Simulation
    async testUIComponents() {
        return await this.test('UI Components', async () => {
            const html = await fetch(WEBSITE_URL).then(r => r.text());
            
            const components = {
                themeToggle: html.includes('setTheme'),
                uploadButton: html.includes('Upload'),
                chatInput: html.includes('Ask anything'),
                fileInput: html.includes('type="file"'),
                suggestions: html.includes('Summarize'),
                dragDrop: html.includes('ondrop'),
                darkMode: html.includes('dark:'),
                responsive: html.includes('lg:'),
                apiIntegration: html.includes(API_BASE)
            };

            const missingComponents = Object.entries(components)
                .filter(([key, value]) => !value)
                .map(([key]) => key);

            if (missingComponents.length > 0) {
                throw new Error(`Missing components: ${missingComponents.join(', ')}`);
            }

            return components;
        });
    }

    // Run all tests
    async runAllTests() {
        console.log('🚀 Starting Advanced DocumentGPT Testing Suite');
        console.log('================================================');

        const testSuite = [
            () => this.testWebsiteLoad(),
            () => this.testAPIEndpoints(),
            () => this.testUploadFlow(),
            () => this.testChatFunctionality(),
            () => this.testErrorHandling(),
            () => this.testPerformance(),
            () => this.testUIComponents()
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
        console.log('📊 FINAL TEST REPORT');
        console.log('====================');
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`📈 Success Rate: ${Math.round((passed / (passed + failed)) * 100)}%`);

        if (this.errors.length > 0) {
            console.log('\n🔍 ERROR DETAILS:');
            this.errors.forEach(({ test, error }) => {
                console.log(`❌ ${test}: ${error.message}`);
            });
        }

        const isPassing = failed === 0;
        console.log(`\n🎯 OVERALL STATUS: ${isPassing ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
        
        return {
            passed,
            failed,
            successRate: Math.round((passed / (passed + failed)) * 100),
            isPassing,
            results: this.results,
            errors: this.errors
        };
    }
}

// Export for Node.js or run directly
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DocumentGPTTester;
} else {
    // Run tests if in browser
    const tester = new DocumentGPTTester();
    tester.runAllTests().then(result => {
        console.log('Testing complete!', result);
    });
}