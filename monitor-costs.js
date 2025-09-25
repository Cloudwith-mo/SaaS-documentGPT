#!/usr/bin/env node

// Cost monitoring script for DocumentGPT
// Run: node monitor-costs.js

const https = require('https');

const OPENAI_API_KEY = process.env.OPENAI_API_KEY || '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';

async function getUsageData() {
    const today = new Date();
    const startDate = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
    const endDate = today.toISOString().split('T')[0];
    
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'api.openai.com',
            port: 443,
            path: `/v1/usage?start_date=${startDate}&end_date=${endDate}`,
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${OPENAI_API_KEY}`,
                'Content-Type': 'application/json'
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(body));
                } catch (e) {
                    reject(e);
                }
            });
        });

        req.on('error', reject);
        req.end();
    });
}

async function main() {
    console.log('📊 DocumentGPT Cost Monitor\n');
    
    try {
        const usage = await getUsageData();
        
        if (usage.error) {
            console.log('❌ Error:', usage.error.message);
            return;
        }
        
        console.log('💰 Current Month Usage:');
        console.log('========================');
        
        let totalCost = 0;
        const modelUsage = {};
        
        usage.data.forEach(day => {
            day.results.forEach(result => {
                const model = result.snapshot_id;
                const cost = result.n_generated_tokens_total * 0.000001; // Rough estimate
                
                if (!modelUsage[model]) {
                    modelUsage[model] = { tokens: 0, cost: 0 };
                }
                
                modelUsage[model].tokens += result.n_generated_tokens_total;
                modelUsage[model].cost += cost;
                totalCost += cost;
            });
        });
        
        // Display by model
        Object.entries(modelUsage)
            .sort((a, b) => b[1].cost - a[1].cost)
            .forEach(([model, data]) => {
                const costStr = `$${data.cost.toFixed(4)}`;
                const tokensStr = data.tokens.toLocaleString();
                console.log(`${model.padEnd(25)} ${costStr.padStart(8)} (${tokensStr} tokens)`);
            });
        
        console.log('------------------------');
        console.log(`Total Estimated Cost: $${totalCost.toFixed(4)}`);
        
        // Cost optimization status
        console.log('\n🎯 Optimization Status:');
        const hasOldEmbedding = Object.keys(modelUsage).some(m => m.includes('ada-002'));
        const hasNewEmbedding = Object.keys(modelUsage).some(m => m.includes('text-embedding-3'));
        const hasGPT4oMini = Object.keys(modelUsage).some(m => m.includes('gpt-4o-mini'));
        
        if (hasNewEmbedding) {
            console.log('✅ Using text-embedding-3-small (5x cheaper)');
        } else if (hasOldEmbedding) {
            console.log('⚠️  Still using ada-002 embeddings (expensive)');
        }
        
        if (hasGPT4oMini) {
            console.log('✅ Using gpt-4o-mini for chat (cost optimized)');
        }
        
        // Recommendations
        console.log('\n💡 Recommendations:');
        if (hasOldEmbedding) {
            console.log('• Switch to text-embedding-3-small for 80% embedding cost reduction');
        }
        if (!hasGPT4oMini) {
            console.log('• Use gpt-4o-mini as default chat model');
        }
        console.log('• Set usage limits in OpenAI dashboard');
        console.log('• Monitor daily for unexpected spikes');
        
    } catch (error) {
        console.error('Error fetching usage:', error.message);
    }
}

main();