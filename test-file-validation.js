// Test file validation logic
function testFileValidation() {
    const allowedTypes = ['pdf', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'md', 'json', 'csv'];
    
    const testFiles = [
        { name: 'document.pdf', size: 1024, expected: 'PASS' },
        { name: 'image.jpg', size: 2048, expected: 'PASS' },
        { name: 'malware.exe', size: 1024, expected: 'FAIL' },
        { name: 'document.docx', size: 1024, expected: 'FAIL' },
        { name: 'large.pdf', size: 60 * 1024 * 1024, expected: 'FAIL' },
        { name: 'text.txt', size: 512, expected: 'PASS' }
    ];
    
    console.log('🧪 File Validation Tests:');
    
    testFiles.forEach(file => {
        const fileExt = file.name.split('.').pop().toLowerCase();
        const typeValid = allowedTypes.includes(fileExt);
        const sizeValid = file.size <= 50 * 1024 * 1024;
        const result = (typeValid && sizeValid) ? 'PASS' : 'FAIL';
        
        const status = result === file.expected ? '✅' : '❌';
        console.log(`${status} ${file.name} (${fileExt}): ${result} (expected ${file.expected})`);
    });
}

testFileValidation();