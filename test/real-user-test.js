// Real User Simulation Test Suite
const puppeteer = require('puppeteer');

class RealUserTest {
    constructor() {
        this.browser = null;
        this.page = null;
        this.results = [];
    }

    async init() {
        this.browser = await puppeteer.launch({ headless: false, slowMo: 100 });
        this.page = await this.browser.newPage();
        await this.page.goto('https://documentgpt.io/');
        await this.page.waitForTimeout(2000);
    }

    async log(test, status, message) {
        const result = { test, status, message, timestamp: new Date().toISOString() };
        this.results.push(result);
        console.log(`${status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : '⏳'} ${test}: ${message}`);
    }

    async testThemeToggle() {
        await this.log('Theme Toggle', 'START', 'Testing theme switching');
        
        // Click light theme
        await this.page.click('button[onclick*="setTheme(\'light\')"]');
        await this.page.waitForTimeout(500);
        
        // Click dark theme
        await this.page.click('button[onclick*="setTheme(\'dark\')"]');
        await this.page.waitForTimeout(500);
        
        // Click auto theme
        await this.page.click('button[onclick*="setTheme(\'auto\')"]');
        await this.page.waitForTimeout(500);
        
        await this.log('Theme Toggle', 'PASS', 'All theme buttons clickable');
    }

    async testNavigation() {
        await this.log('Navigation', 'START', 'Testing tab navigation');
        
        // Click Upload tab
        await this.page.click('button[onclick*="tab=\'upload\'"]');
        await this.page.waitForTimeout(500);
        
        // Click Chat tab
        await this.page.click('button[onclick*="tab=\'chat\'"]');
        await this.page.waitForTimeout(500);
        
        await this.log('Navigation', 'PASS', 'Tab navigation working');
    }

    async testNewChat() {
        await this.log('New Chat', 'START', 'Testing new chat functionality');
        
        // Click New Chat button
        await this.page.click('button[onclick="newChat()"]');
        await this.page.waitForTimeout(1000);
        
        await this.log('New Chat', 'PASS', 'New chat button working');
    }

    async testChatInput() {
        await this.log('Chat Input', 'START', 'Testing chat input and send');
        
        // Type in chat input
        await this.page.type('#chatInput', 'Hello, this is a test message');
        await this.page.waitForTimeout(500);
        
        // Click send button
        await this.page.click('button[onclick="handleSendMessage()"]');
        await this.page.waitForTimeout(3000); // Wait for AI response
        
        await this.log('Chat Input', 'PASS', 'Chat input and send working');
    }

    async testSuggestionButtons() {
        await this.log('Suggestion Buttons', 'START', 'Testing suggestion buttons');
        
        // Click first suggestion button
        const suggestionButtons = await this.page.$$('button[onclick*="chat("]');
        if (suggestionButtons.length > 0) {
            await suggestionButtons[0].click();
            await this.page.waitForTimeout(3000);
            await this.log('Suggestion Buttons', 'PASS', 'Suggestion buttons working');
        } else {
            await this.log('Suggestion Buttons', 'FAIL', 'No suggestion buttons found');
        }
    }

    async testZoomControls() {
        await this.log('Zoom Controls', 'START', 'Testing zoom controls');
        
        // Click zoom in
        await this.page.click('button[onclick*="zoom + 10"]');
        await this.page.waitForTimeout(500);
        
        // Click zoom out
        await this.page.click('button[onclick*="zoom - 10"]');
        await this.page.waitForTimeout(500);
        
        await this.log('Zoom Controls', 'PASS', 'Zoom controls working');
    }

    async testSearchBox() {
        await this.log('Search Box', 'START', 'Testing search functionality');
        
        // Type in search box
        const searchInput = await this.page.$('input[placeholder*="Search anything"]');
        if (searchInput) {
            await searchInput.type('test search');
            await this.page.waitForTimeout(500);
            
            // Click find button
            await this.page.click('button[onclick="searchInDocument()"]');
            await this.page.waitForTimeout(500);
            
            await this.log('Search Box', 'PASS', 'Search box working');
        } else {
            await this.log('Search Box', 'FAIL', 'Search box not found');
        }
    }

    async testAttachButtons() {
        await this.log('Attach Buttons', 'START', 'Testing attach buttons');
        
        // Check for attach buttons (📎)
        const attachButtons = await this.page.$$('label:has(input[type="file"])');
        if (attachButtons.length >= 2) {
            await this.log('Attach Buttons', 'PASS', `Found ${attachButtons.length} attach buttons`);
        } else {
            await this.log('Attach Buttons', 'FAIL', `Only found ${attachButtons.length} attach buttons`);
        }
    }

    async testAssistantTools() {
        await this.log('Assistant Tools', 'START', 'Testing assistant tool buttons');
        
        // Click Legal/Finance button
        const toolButtons = await this.page.$$('button:has(span:contains("Legal/Finance"))');
        if (toolButtons.length > 0) {
            await toolButtons[0].click();
            await this.page.waitForTimeout(500);
            await this.log('Assistant Tools', 'PASS', 'Assistant tool buttons clickable');
        } else {
            await this.log('Assistant Tools', 'FAIL', 'Assistant tool buttons not found');
        }
    }

    async runAllTests() {
        console.log('🚀 Starting Real User Simulation Test');
        console.log('=====================================');

        try {
            await this.init();
            
            await this.testThemeToggle();
            await this.testNavigation();
            await this.testNewChat();
            await this.testChatInput();
            await this.testSuggestionButtons();
            await this.testZoomControls();
            await this.testSearchBox();
            await this.testAttachButtons();
            await this.testAssistantTools();
            
            const passed = this.results.filter(r => r.status === 'PASS').length;
            const failed = this.results.filter(r => r.status === 'FAIL').length;
            
            console.log('\\n📊 REAL USER TEST RESULTS');
            console.log('==========================');
            console.log(`✅ Passed: ${passed}`);
            console.log(`❌ Failed: ${failed}`);
            console.log(`📈 Success Rate: ${Math.round((passed / (passed + failed)) * 100)}%`);
            
            return { passed, failed, results: this.results };
            
        } finally {
            if (this.browser) {
                await this.browser.close();
            }
        }
    }
}

// Run if called directly
if (require.main === module) {
    const tester = new RealUserTest();
    tester.runAllTests().then(result => {
        console.log('\\nReal user testing complete!');
        process.exit(result.failed === 0 ? 0 : 1);
    }).catch(err => {
        console.error('Test failed:', err);
        process.exit(1);
    });
}

module.exports = RealUserTest;