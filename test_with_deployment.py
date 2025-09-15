#!/usr/bin/env python3
"""
Deploy and test all resources
"""

import subprocess
import time
import requests
import json
from automated_test_suite import DocumentGPTTester

def deploy_resources():
    """Deploy AWS resources"""
    print("🚀 Deploying AWS resources...")
    
    try:
        # Deploy CloudFormation stack
        result = subprocess.run([
            'aws', 'cloudformation', 'deploy',
            '--template-file', 'aws_resources.yml',
            '--stack-name', 'documentgpt-resources',
            '--capabilities', 'CAPABILITY_IAM',
            '--region', 'us-east-1'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ CloudFormation stack deployed")
        else:
            print(f"❌ CloudFormation failed: {result.stderr}")
            return False
            
        # Install serverless if needed
        subprocess.run(['npm', 'install', '-g', 'serverless'], capture_output=True)
        subprocess.run(['npm', 'install', 'serverless-python-requirements'], capture_output=True)
        
        # Deploy serverless functions
        result = subprocess.run(['serverless', 'deploy', '--stage', 'prod'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Serverless functions deployed")
            
            # Extract API Gateway URL
            output = result.stdout
            for line in output.split('\n'):
                if 'ServiceEndpoint:' in line:
                    api_url = line.split(': ')[1].strip()
                    print(f"📡 API URL: {api_url}")
                    return api_url
        else:
            print(f"❌ Serverless deployment failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False
    
    return True

def test_deployed_resources(api_url):
    """Test the deployed resources"""
    print("\n🧪 Testing deployed resources...")
    
    # Wait for deployment to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(30)
    
    # Test endpoints
    endpoints = [
        f"{api_url}/api/agents",
        f"{api_url}/api/v5/health",
        f"{api_url}/api/pdf/search"
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            if 'search' in endpoint:
                response = requests.post(endpoint, json={"query": "test"}, timeout=10)
            else:
                response = requests.get(endpoint, timeout=10)
                
            if response.status_code == 200:
                results.append(f"✅ {endpoint} - Working")
            else:
                results.append(f"❌ {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            results.append(f"❌ {endpoint} - Error: {str(e)}")
    
    for result in results:
        print(result)
    
    return all("✅" in result for result in results)

def run_full_test_suite():
    """Run the complete test suite"""
    print("\n🎯 Running full test suite...")
    
    tester = DocumentGPTTester()
    tester.run_all_tests()
    
    # Check results
    passed = len([r for r in tester.results if r['status'] == 'PASS'])
    total = len([r for r in tester.results if r['status'] != 'SKIP'])
    success_rate = (passed / total * 100) if total > 0 else 0
    
    return success_rate >= 100

def main():
    """Main deployment and testing flow"""
    print("🎯 DocumentGPT Deployment and Testing")
    print("=" * 50)
    
    # Step 1: Deploy resources
    api_url = deploy_resources()
    if not api_url:
        print("❌ Deployment failed")
        return False
    
    # Step 2: Test deployed resources
    if not test_deployed_resources(api_url):
        print("❌ Resource testing failed")
        return False
    
    # Step 3: Run full test suite
    if not run_full_test_suite():
        print("❌ Full test suite failed")
        return False
    
    print("\n🎉 SUCCESS! All resources deployed and tested!")
    print(f"📡 API URL: {api_url}")
    print("✅ 100% test pass rate achieved")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)