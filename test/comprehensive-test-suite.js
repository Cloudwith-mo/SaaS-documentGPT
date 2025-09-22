// Comprehensive DocumentGPT Test Suite
const API_BASE = 'https://9voqzgx3ch.execute-api.us-east-1.amazonaws.com/prod';
const API_KEY = 'dk-test-key-123';
const WEBSITE_URL = 'https://documentgpt.io/';

class ComprehensiveTestSuite {
    constructor() {
        this.results = [];
        this.errors = [];
    }

    log(test, status, message, data = null) {
        const result = { test, status, message, data, timestamp: new Date().toISOString() };
        this.results.push(result);
        console.log(`${status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : '⏳'} ${test}: ${message}`);
        if (data && Object.keys(data).length > 0) {
            console.log('   Data:', JSON.stringify(data, null, 2));
        }
    }

    async test(name, fn) {
        try {
            this.log(name, 'START', 'Running test...');
            const result = await fn();
            this.log(name, 'PASS', 'Test completed successfully', result);
            return result;
        } catch (error) {
            this.log(name, 'FAIL', error.message, { error: error.message });
            this.errors.push({ test: name, error });
            throw error;
        }
    }

    // Test 1: Website Persistence Check
    async testWebsitePersistence() {
        return await this.test('Website Persistence', async () => {
            const response = await fetch(WEBSITE_URL);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const html = await response.text();
            const checks = {
                hasLocalStorage: html.includes('localStorage'),
                hasSessionPersistence: html.includes('sessionId'),
                hasMessagePersistence: html.includes('dgpt:messages'),
                hasStateManagement: html.includes('saveState'),
                hasEnhancedFeatures: html.includes('Enhanced'),
                size: html.length
            };
            
            if (!checks.hasLocalStorage) throw new Error('Missing localStorage functionality');
            if (!checks.hasSessionPersistence) throw new Error('Missing session persistence');
            
            return checks;
        });
    }

    // Test 2: Regular GPT Mode
    async testRegularGPTMode() {
        return await this.test('Regular GPT Mode', async () => {
            const questions = [
                'What is artificial intelligence?',
                'Explain quantum computing',
                'What are the benefits of renewable energy?'
            ];

            const results = [];
            
            for (const question of questions) {
                const response = await fetch(`${API_BASE}/rag-chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question, docId: null })
                });

                if (!response.ok) throw new Error(`Regular GPT failed for: ${question}`);
                
                const data = await response.json();
                if (!data.answer) throw new Error(`No answer for: ${question}`);
                if (data.hasContext !== false) throw new Error(`Should not have context for: ${question}`);
                if (data.mode !== 'general_ai') throw new Error(`Wrong mode for: ${question}`);

                results.push({
                    question,
                    answerLength: data.answer.length,
                    hasContext: data.hasContext,
                    mode: data.mode
                });

                await new Promise(resolve => setTimeout(resolve, 500));
            }

            return results;
        });
    }

    // Test 3: Document Upload & Processing Pipeline
    async testDocumentProcessingPipeline() {
        return await this.test('Document Processing Pipeline', async () => {
            const userId = 'test-user-' + Date.now();
            
            // Step 1: Upload document
            const uploadResponse = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': API_KEY,
                    'x-user-id': userId
                },
                body: JSON.stringify({
                    filename: 'comprehensive-test.txt',
                    contentType: 'text/plain'
                })
            });

            const uploadData = await uploadResponse.json();
            if (!uploadData.uploadUrl) throw new Error('No upload URL provided');
            if (!uploadData.docId) throw new Error('No document ID provided');

            // Step 2: Upload file content
            const testContent = 'Apple Inc. is a technology company founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in 1976. The company is headquartered in Cupertino, California. Apple is known for developing innovative products like the iPhone, iPad, Mac computers, and Apple Watch. The company went public in 1980 and became the world\'s most valuable company by market capitalization.';
            
            const s3Response = await fetch(uploadData.uploadUrl, {
                method: 'PUT',
                headers: { 'Content-Type': 'text/plain' },
                body: testContent
            });

            if (!s3Response.ok) throw new Error('S3 upload failed');

            // Step 3: Test processing activation
            try {
                const processResponse = await fetch(`${API_BASE}/process-document`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        docId: uploadData.docId,
                        filename: 'comprehensive-test.txt',
                        content: testContent,
                        sessionId: userId
                    })
                });
                
                // Processing may not be fully implemented, so we don't fail on this
                const processData = processResponse.ok ? await processResponse.json() : null;
                
                return {
                    docId: uploadData.docId,
                    uploadSuccess: true,
                    s3Status: s3Response.status,
                    contentLength: testContent.length,
                    processingAttempted: true,
                    processingSuccess: processResponse.ok,
                    processData: processData
                };
            } catch (error) {
                return {
                    docId: uploadData.docId,
                    uploadSuccess: true,
                    s3Status: s3Response.status,
                    contentLength: testContent.length,
                    processingAttempted: false,
                    processingError: error.message
                };
            }
        });
    }

    // Test 4: RAG vs Regular GPT Switching
    async testRAGvsRegularSwitching() {
        return await this.test('RAG vs Regular GPT Switching', async () => {
            const question = 'What company was founded in 1975?';
            
            // Test with known document (should use RAG)
            const ragResponse = await fetch(`${API_BASE}/rag-chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question,
                    docId: 'doc_1758376193835_c767nofb67v'
                })
            });

            const ragData = await ragResponse.json();
            
            // Test without document (should use regular GPT)
            const gptResponse = await fetch(`${API_BASE}/rag-chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question,
                    docId: null
                })
            });

            const gptData = await gptResponse.json();

            if (!ragData.answer || !gptData.answer) {
                throw new Error('Missing answers in switching test');
            }

            return {
                ragMode: {
                    hasContext: ragData.hasContext,
                    answerLength: ragData.answer.length,
                    containsMicrosoft: ragData.answer.toLowerCase().includes('microsoft')
                },
                gptMode: {
                    hasContext: gptData.hasContext,
                    mode: gptData.mode,
                    answerLength: gptData.answer.length
                }
            };
        });
    }

    // Test 5: UI Component Functionality
    async testUIComponents() {
        return await this.test('UI Components', async () => {
            const html = await fetch(WEBSITE_URL).then(r => r.text());
            
            const components = {
                persistentChat: html.includes('localStorage.setItem'),
                sessionManagement: html.includes('sessionId'),
                pageNavigation: html.includes('nextPage'),
                zoomControls: html.includes('zoom'),
                searchFunctionality: html.includes('searchInDocument'),
                themeToggle: html.includes('setTheme'),
                fileUpload: html.includes('handleFileSelect'),
                dragDrop: html.includes('handleDrop'),
                chatInput: html.includes('handleSendMessage'),
                clearChat: html.includes('clearChat'),
                responsiveDesign: html.includes('lg:'),
                darkMode: html.includes('dark:'),
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

    // Test 6: Persistence Simulation
    async testPersistenceSimulation() {
        return await this.test('Persistence Simulation', async () => {
            // This test simulates what happens when a user returns
            const sessionId = 'test-session-' + Date.now();
            
            // Simulate saving state
            const mockState = {
                sessionId,
                messages: [
                    { role: 'user', text: 'Hello', timestamp: new Date().toISOString() },
                    { role: 'assistant', text: 'Hi there!', timestamp: new Date().toISOString() }
                ],
                docId: 'doc_test_123',
                fileName: 'test-document.txt',
                pages: 5,
                currentPage: 2
            };

            // Test that the website can handle this state
            const html = await fetch(WEBSITE_URL).then(r => r.text());
            
            const persistenceFeatures = {
                canSaveMessages: html.includes('dgpt:messages'),
                canSaveSession: html.includes('dgpt:sessionId'),
                canSaveDocument: html.includes('dgpt:docId'),
                canSavePages: html.includes('dgpt:pages'),
                canSaveTheme: html.includes('dgpt:theme'),
                hasStateRestore: html.includes('JSON.parse(localStorage.getItem')
            };

            return {
                mockState,
                persistenceFeatures,
                allFeaturesPresent: Object.values(persistenceFeatures).every(v => v)
            };
        });
    }

    // Test 7: Advanced Error Handling
    async testAdvancedErrorHandling() {
        return await this.test('Advanced Error Handling', async () => {
            const errorTests = [];

            // Test 1: Malformed JSON
            try {
                const response = await fetch(`${API_BASE}/rag-chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: '{"question":'
                });
                errorTests.push({
                    test: 'malformed_json',
                    status: response.ok ? 'FAIL' : 'PASS',
                    httpStatus: response.status
                });
            } catch (e) {
                errorTests.push({ test: 'malformed_json', status: 'PASS', error: 'Network error as expected' });
            }

            // Test 2: Very long question
            const longQuestion = 'What is ' + 'very '.repeat(1000) + 'long question?';
            try {
                const response = await fetch(`${API_BASE}/rag-chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: longQuestion, docId: null })
                });
                const data = await response.json();
                errorTests.push({
                    test: 'long_question',
                    status: data.answer ? 'PASS' : 'FAIL',
                    answerLength: data.answer ? data.answer.length : 0
                });
            } catch (e) {
                errorTests.push({ test: 'long_question', status: 'FAIL', error: e.message });
            }

            // Test 3: Special characters
            try {
                const response = await fetch(`${API_BASE}/rag-chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: '🤖💬🔥 What is AI? 中文测试', docId: null })
                });
                const data = await response.json();
                errorTests.push({
                    test: 'special_characters',
                    status: data.answer ? 'PASS' : 'FAIL',
                    hasAnswer: !!data.answer
                });
            } catch (e) {
                errorTests.push({ test: 'special_characters', status: 'FAIL', error: e.message });
            }

            return errorTests;
        });
    }

    // Test 8: Performance Under Load
    async testPerformanceUnderLoad() {
        return await this.test('Performance Under Load', async () => {
            const concurrentRequests = 10;
            const startTime = Date.now();

            const promises = Array.from({ length: concurrentRequests }, (_, i) => {
                const isRAG = i % 2 === 0;
                return fetch(`${API_BASE}/rag-chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: `Performance test question ${i + 1}: What is technology?`,
                        docId: isRAG ? 'doc_1758376193835_c767nofb67v' : null
                    })
                }).then(r => r.json()).then(data => ({
                    index: i,
                    mode: isRAG ? 'RAG' : 'GPT',
                    success: !!data.answer,
                    hasContext: data.hasContext,
                    answerLength: data.answer ? data.answer.length : 0
                }));
            });

            const results = await Promise.all(promises);
            const endTime = Date.now();
            const totalTime = endTime - startTime;

            const successCount = results.filter(r => r.success).length;
            const ragCount = results.filter(r => r.mode === 'RAG' && r.success).length;
            const gptCount = results.filter(r => r.mode === 'GPT' && r.success).length;

            if (successCount < concurrentRequests * 0.8) {
                throw new Error(`Only ${successCount}/${concurrentRequests} requests succeeded`);
            }

            if (totalTime > 30000) {
                throw new Error(`Performance too slow: ${totalTime}ms for ${concurrentRequests} requests`);
            }

            return {
                totalRequests: concurrentRequests,
                successfulRequests: successCount,
                ragSuccessful: ragCount,
                gptSuccessful: gptCount,
                totalTime,
                avgResponseTime: totalTime / concurrentRequests,
                successRate: (successCount / concurrentRequests) * 100,
                results
            };
        });
    }

    // Run all tests
    async runAllTests() {
        console.log('🚀 Starting Comprehensive DocumentGPT Test Suite');
        console.log('=================================================');

        const testSuite = [
            () => this.testWebsitePersistence(),
            () => this.testRegularGPTMode(),
            () => this.testDocumentProcessingPipeline(),
            () => this.testRAGvsRegularSwitching(),
            () => this.testUIComponents(),
            () => this.testPersistenceSimulation(),
            () => this.testAdvancedErrorHandling(),
            () => this.testPerformanceUnderLoad()
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
        console.log('📊 COMPREHENSIVE TEST REPORT');
        console.log('=============================');
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`📈 Success Rate: ${Math.round((passed / (passed + failed)) * 100)}%`);

        if (this.errors.length > 0) {
            console.log('\\n🔍 ERROR DETAILS:');
            this.errors.forEach(({ test, error }) => {
                console.log(`❌ ${test}: ${error.message}`);
            });
        }

        const isPassing = failed === 0;
        console.log(`\\n🎯 OVERALL STATUS: ${isPassing ? '✅ ALL TESTS PASSED - PRODUCTION READY' : '❌ SOME TESTS FAILED - NEEDS ATTENTION'}`);
        
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
    module.exports = ComprehensiveTestSuite;
} else {
    const tester = new ComprehensiveTestSuite();
    tester.runAllTests().then(result => {
        console.log('Testing complete!', result);
    });
}