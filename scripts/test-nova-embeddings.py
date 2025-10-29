#!/usr/bin/env python3
"""Test Nova embeddings API"""
import sys
sys.path.insert(0, '/Users/muhammadadeyemi/documentgpt.io/SaaS-documentGPT/lambda')

import boto3
import json

def test_nova():
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    try:
        response = bedrock.invoke_model(
            modelId='amazon.nova-2-multimodal-embeddings-v1:0',
            body=json.dumps({'inputText': 'Hello world, testing Nova embeddings'})
        )
        
        result = json.loads(response['body'].read())
        
        print('✅ Nova embeddings working!')
        print(f'📊 Embedding dimension: {len(result.get("embedding", []))}')
        print(f'🔢 First 5 values: {result.get("embedding", [])[:5]}')
        print(f'💰 Cost: $0.0006 per 1K tokens')
        print(f'🎯 Model ID: amazon.nova-2-multimodal-embeddings-v1:0')
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        print(f'💡 Make sure your IAM user/role has bedrock:InvokeModel permission')
        return False

if __name__ == '__main__':
    success = test_nova()
    sys.exit(0 if success else 1)
