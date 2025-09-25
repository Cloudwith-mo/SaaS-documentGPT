#!/usr/bin/env node

// Re-index old documents with cost-optimized embeddings
// Run: node reindex-old-docs.js [--dry-run] [--limit=10]

const { S3Client, ListObjectsV2Command, GetObjectCommand } = require('@aws-sdk/client-s3');
const { LambdaClient, InvokeCommand } = require('@aws-sdk/client-lambda');

const s3Client = new S3Client({ region: 'us-east-1' });
const lambdaClient = new LambdaClient({ region: 'us-east-1' });

const BUCKET = 'documentgpt-uploads';
const INDEXER_FUNCTION = 'documentgpt-indexer';

async function findOldDocuments() {
    const command = new ListObjectsV2Command({
        Bucket: BUCKET,
        Prefix: 'derived/',
        Delimiter: '/'
    });
    
    const response = await s3Client.send(command);
    const oldDocs = [];
    
    for (const obj of response.Contents || []) {
        if (obj.Key.endsWith('.index.json')) {
            try {
                const indexResponse = await s3Client.send(new GetObjectCommand({
                    Bucket: BUCKET,
                    Key: obj.Key
                }));
                
                const index = JSON.parse(await indexResponse.Body.transformToString());
                
                // Check if using old embedding model
                if (!index.model || index.model === 'text-embedding-ada-002') {
                    const docId = obj.Key.replace('derived/', '').replace('.index.json', '');
                    oldDocs.push({
                        docId,
                        indexKey: obj.Key,
                        oldModel: index.model || 'text-embedding-ada-002',
                        chunks: index.totalChunks || 0,
                        createdAt: index.createdAt
                    });
                }
            } catch (error) {
                console.log(`⚠️  Could not read index: ${obj.Key}`);
            }
        }
    }
    
    return oldDocs;
}

async function reindexDocument(docId) {
    const payload = {
        docId,
        derivedKey: `derived/${docId}.txt`
    };
    
    const command = new InvokeCommand({
        FunctionName: INDEXER_FUNCTION,
        Payload: JSON.stringify(payload)
    });
    
    const response = await lambdaClient.send(command);
    const result = JSON.parse(new TextDecoder().decode(response.Payload));
    
    return result;
}

async function main() {
    const args = process.argv.slice(2);
    const dryRun = args.includes('--dry-run');
    const limitArg = args.find(arg => arg.startsWith('--limit='));
    const limit = limitArg ? parseInt(limitArg.split('=')[1]) : 10;
    
    console.log('🔄 DocumentGPT Re-indexing Tool');
    console.log('===============================\n');
    
    if (dryRun) {
        console.log('🔍 DRY RUN MODE - No changes will be made\n');
    }
    
    try {
        console.log('📋 Finding documents with old embeddings...');
        const oldDocs = await findOldDocuments();
        
        if (oldDocs.length === 0) {
            console.log('✅ All documents already use cost-optimized embeddings!');
            return;
        }
        
        console.log(`\n📊 Found ${oldDocs.length} documents using expensive embeddings:`);
        console.log('DocId'.padEnd(20) + 'Old Model'.padEnd(25) + 'Chunks'.padEnd(8) + 'Created');
        console.log('-'.repeat(70));
        
        const docsToProcess = oldDocs.slice(0, limit);
        let totalSavings = 0;
        
        for (const doc of docsToProcess) {
            const oldCost = doc.chunks * 0.0001; // ada-002 cost estimate
            const newCost = doc.chunks * 0.00002; // 3-small cost estimate
            const savings = oldCost - newCost;
            totalSavings += savings;
            
            console.log(
                doc.docId.substring(0, 18).padEnd(20) +
                (doc.oldModel || 'ada-002').padEnd(25) +
                doc.chunks.toString().padEnd(8) +
                (doc.createdAt || 'unknown').substring(0, 10)
            );
        }
        
        console.log('-'.repeat(70));
        console.log(`💰 Estimated savings: $${totalSavings.toFixed(4)} per re-index cycle`);
        
        if (dryRun) {
            console.log('\n🔍 DRY RUN: Would re-index these documents');
            console.log('Run without --dry-run to proceed');
            return;
        }
        
        console.log(`\n🚀 Re-indexing ${docsToProcess.length} documents...`);
        
        let processed = 0;
        let errors = 0;
        
        for (const doc of docsToProcess) {
            try {
                console.log(`Processing ${doc.docId}...`);
                const result = await reindexDocument(doc.docId);
                
                if (result.errorMessage) {
                    console.log(`❌ Error: ${result.errorMessage}`);
                    errors++;
                } else {
                    console.log(`✅ Success: ${result.chunks} chunks, model: ${result.model}`);
                    processed++;
                }
                
                // Rate limiting
                await new Promise(resolve => setTimeout(resolve, 2000));
                
            } catch (error) {
                console.log(`❌ Failed: ${error.message}`);
                errors++;
            }
        }
        
        console.log(`\n📈 Re-indexing Complete:`);
        console.log(`✅ Processed: ${processed}`);
        console.log(`❌ Errors: ${errors}`);
        console.log(`💰 Estimated monthly savings: $${(totalSavings * 30).toFixed(2)}`);
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

if (require.main === module) {
    main();
}