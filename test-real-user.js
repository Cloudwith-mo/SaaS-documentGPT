// Real user simulation test
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function testRealUser() {
    const browser = await puppeteer.launch({ 
        headless: false,
        defaultViewport: { width: 1200, height: 800 }
    });
    
    const page = await browser.newPage();
    
    try {
        console.log('🚀 Starting real user simulation...');
        
        // Navigate to site
        await page.goto('https://documentgpt.io/', { waitUntil: 'networkidle0' });
        console.log('✅ Site loaded');
        
        // Test 1: Check zoom functionality
        console.log('🔍 Testing zoom functionality...');
        
        // Upload a test image first
        const fileInput = await page.$('input[type="file"]');
        const testImagePath = path.join(__dirname, 'test_files', 'test.txt');
        
        // Create test file if it doesn't exist
        if (!fs.existsSync(testImagePath)) {
            fs.writeFileSync(testImagePath, 'This is a test document for DocumentGPT.\n\nIt contains multiple lines of text to test the zoom functionality and other features.\n\nThe zoom should make this text larger and smaller when using the +/- buttons.');
        }
        
        await fileInput.uploadFile(testImagePath);
        console.log('📄 Test file uploaded');
        
        // Wait for upload to complete
        await page.waitForTimeout(3000);
        
        // Test zoom buttons
        const zoomIn = await page.$('button:has-text("+")');
        const zoomOut = await page.$('button:has-text("−")');
        
        if (zoomIn && zoomOut) {
            await zoomIn.click();
            await page.waitForTimeout(500);
            await zoomIn.click();
            console.log('✅ Zoom in buttons clicked');
            
            await zoomOut.click();
            console.log('✅ Zoom out button clicked');
        }
        
        // Test 2: Chat functionality
        console.log('💬 Testing chat functionality...');
        
        const chatInput = await page.$('#chatInput');
        if (chatInput) {
            await chatInput.type('What is this document about?');
            
            const sendButton = await page.$('button:has-text("➤")');
            if (sendButton) {
                await sendButton.click();
                console.log('✅ Chat message sent');
                
                // Wait for response
                await page.waitForTimeout(5000);
            }
        }
        
        // Test 3: Check for errors in console
        const logs = [];
        page.on('console', msg => logs.push(msg.text()));
        page.on('pageerror', error => logs.push(`ERROR: ${error.message}`));
        
        await page.waitForTimeout(2000);
        
        const errors = logs.filter(log => log.includes('ERROR') || log.includes('error'));
        if (errors.length > 0) {
            console.log('❌ Console errors found:');
            errors.forEach(error => console.log(`  - ${error}`));
        } else {
            console.log('✅ No console errors detected');
        }
        
        // Test 4: Theme switching
        console.log('🌙 Testing theme switching...');
        const darkModeButton = await page.$('button:has-text("🌙")');
        if (darkModeButton) {
            await darkModeButton.click();
            await page.waitForTimeout(1000);
            console.log('✅ Dark mode toggled');
        }
        
        console.log('🎉 Real user simulation completed!');
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    } finally {
        await browser.close();
    }
}

testRealUser();