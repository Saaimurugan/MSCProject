#!/usr/bin/env python3
"""
Simple MSC Evaluate Testing Script
Tests the application without Selenium for quick debugging
"""

import requests
import json
import time
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

class SimpleMSCTest:
    def __init__(self):
        self.base_url = "http://msc-evaluate-frontend-dev-127510141.s3-website.ap-south-1.amazonaws.com"
        self.api_url = "https://x3f5ix7bf1.execute-api.ap-south-1.amazonaws.com/dev"
        self.errors_found = []
        self.fixes_applied = []
    
    def test_frontend_accessibility(self):
        """Test if frontend is accessible"""
        print(f"{Fore.CYAN}🧪 Testing frontend accessibility...")
        
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200:
                print(f"{Fore.GREEN}✅ Frontend accessible (Status: {response.status_code})")
                
                # Check if it contains React app elements
                if 'id="root"' in response.text:
                    print(f"{Fore.GREEN}✅ React app container found in HTML")
                else:
                    self.errors_found.append("React app container not found in HTML")
                    print(f"{Fore.RED}❌ React app container not found")
                
                if 'MSC Evaluate' in response.text:
                    print(f"{Fore.GREEN}✅ App title found in HTML")
                else:
                    print(f"{Fore.YELLOW}⚠️ App title not found in HTML (might be loaded by JS)")
                
                return True
            else:
                self.errors_found.append(f"Frontend not accessible: {response.status_code}")
                print(f"{Fore.RED}❌ Frontend not accessible: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.errors_found.append(f"Frontend connection failed: {str(e)}")
            print(f"{Fore.RED}❌ Frontend connection failed: {str(e)}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints directly"""
        print(f"{Fore.CYAN}🧪 Testing API endpoints...")
        
        # Test signup endpoint
        print(f"{Fore.YELLOW}📡 Testing signup endpoint...")
        try:
            signup_data = {
                "email": f"test_{int(time.time())}@example.com",
                "password": "TestPassword123!",
                "name": "Test User",
                "role": "student"
            }
            
            response = requests.post(
                f"{self.api_url}/auth/signup", 
                json=signup_data, 
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"{Fore.YELLOW}📡 Signup API Response: {response.status_code}")
            print(f"{Fore.YELLOW}📡 Response Headers: {dict(response.headers)}")
            print(f"{Fore.YELLOW}📡 Response Body: {response.text[:200]}...")
            
            if response.status_code in [200, 201]:
                print(f"{Fore.GREEN}✅ Signup API working")
                
                # Check CORS headers
                if 'Access-Control-Allow-Origin' in response.headers:
                    print(f"{Fore.GREEN}✅ CORS headers present")
                else:
                    self.errors_found.append("CORS headers missing in API response")
                    print(f"{Fore.RED}❌ CORS headers missing")
                    
            elif response.status_code == 404:
                self.errors_found.append("Signup API endpoint not found (404)")
                print(f"{Fore.RED}❌ Signup API endpoint not found (404)")
            elif response.status_code == 500:
                self.errors_found.append(f"Signup API server error: {response.text}")
                print(f"{Fore.RED}❌ Signup API server error: {response.text}")
            else:
                self.errors_found.append(f"Signup API failed: {response.status_code} - {response.text}")
                print(f"{Fore.RED}❌ Signup API failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.errors_found.append(f"Signup API connection failed: {str(e)}")
            print(f"{Fore.RED}❌ Signup API connection failed: {str(e)}")
        
        # Test login endpoint
        print(f"{Fore.YELLOW}📡 Testing login endpoint...")
        try:
            login_data = {
                "email": "test@example.com",
                "password": "test123"
            }
            
            response = requests.post(
                f"{self.api_url}/auth/login", 
                json=login_data, 
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"{Fore.YELLOW}📡 Login API Response: {response.status_code}")
            
            if response.status_code in [200, 401]:  # 401 is expected for invalid credentials
                print(f"{Fore.GREEN}✅ Login API endpoint accessible")
            elif response.status_code == 404:
                self.errors_found.append("Login API endpoint not found (404)")
                print(f"{Fore.RED}❌ Login API endpoint not found (404)")
            else:
                print(f"{Fore.YELLOW}⚠️ Login API response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.errors_found.append(f"Login API connection failed: {str(e)}")
            print(f"{Fore.RED}❌ Login API connection failed: {str(e)}")
    
    def test_lambda_functions_directly(self):
        """Test Lambda functions using AWS CLI if available"""
        print(f"{Fore.CYAN}🧪 Testing Lambda functions...")
        
        import subprocess
        
        try:
            # Test if AWS CLI is available
            result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{Fore.GREEN}✅ AWS CLI available")
                
                # Test Lambda function
                test_payload = {
                    "body": json.dumps({"email": "test@example.com", "password": "test123"}),
                    "httpMethod": "POST",
                    "headers": {"Content-Type": "application/json"}
                }
                
                # Write test payload to file
                with open('test_payload.json', 'w') as f:
                    json.dump(test_payload, f)
                
                # Invoke Lambda function
                result = subprocess.run([
                    'aws', 'lambda', 'invoke',
                    '--function-name', 'msc-evaluate-auth-login-dev',
                    '--region', 'ap-south-1',
                    '--payload', 'file://test_payload.json',
                    'response.json'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"{Fore.GREEN}✅ Lambda function invoked successfully")
                    
                    # Read response
                    try:
                        with open('response.json', 'r') as f:
                            response = json.load(f)
                        print(f"{Fore.YELLOW}📡 Lambda Response: {response}")
                    except:
                        print(f"{Fore.YELLOW}📡 Lambda invoked but couldn't read response")
                else:
                    print(f"{Fore.RED}❌ Lambda invocation failed: {result.stderr}")
                
                # Cleanup
                import os
                try:
                    os.remove('test_payload.json')
                    os.remove('response.json')
                except:
                    pass
                    
            else:
                print(f"{Fore.YELLOW}⚠️ AWS CLI not available for Lambda testing")
                
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Lambda testing skipped: {str(e)}")
    
    def analyze_errors_and_suggest_fixes(self):
        """Analyze errors and suggest fixes"""
        print(f"{Fore.CYAN}🔧 Analyzing errors and suggesting fixes...")
        
        if not self.errors_found:
            print(f"{Fore.GREEN}✅ No errors found!")
            return
        
        print(f"{Fore.YELLOW}📋 Found {len(self.errors_found)} issues:")
        for i, error in enumerate(self.errors_found, 1):
            print(f"{Fore.RED}  {i}. {error}")
        
        # Suggest fixes
        print(f"\n{Fore.CYAN}🔧 Suggested fixes:")
        
        for error in self.errors_found:
            if "404" in error and "API" in error:
                print(f"{Fore.YELLOW}  • API Gateway endpoints need to be configured")
                print(f"    - Add proper integrations between API Gateway and Lambda functions")
                print(f"    - Deploy API Gateway stage")
                
            elif "CORS" in error:
                print(f"{Fore.YELLOW}  • CORS headers need to be added to Lambda responses")
                print(f"    - Update Lambda functions with CORS headers (already done)")
                print(f"    - Redeploy Lambda functions")
                
            elif "connection failed" in error:
                print(f"{Fore.YELLOW}  • Network connectivity issue")
                print(f"    - Check if services are running")
                print(f"    - Verify URLs are correct")
                
            elif "React app container" in error:
                print(f"{Fore.YELLOW}  • React app not loading properly")
                print(f"    - Check if build was successful")
                print(f"    - Verify S3 deployment")
    
    def generate_fix_commands(self):
        """Generate commands to fix the issues"""
        print(f"\n{Fore.CYAN}🛠️ Commands to fix issues:")
        
        if any("API" in error and "404" in error for error in self.errors_found):
            print(f"{Fore.GREEN}# Fix API Gateway integration:")
            print(f"aws apigateway create-deployment --rest-api-id x3f5ix7bf1 --stage-name dev --region ap-south-1")
        
        if any("CORS" in error for error in self.errors_found):
            print(f"{Fore.GREEN}# Redeploy Lambda functions with CORS fixes:")
            print(f"# (Lambda functions already updated with CORS headers)")
            print(f"# Need to repackage and update Lambda functions")
        
        if any("React" in error for error in self.errors_found):
            print(f"{Fore.GREEN}# Rebuild and redeploy React app:")
            print(f"cd frontend && npm run build && aws s3 sync build/ s3://msc-evaluate-frontend-dev-127510141 --delete")
    
    def run_tests(self):
        """Run all tests"""
        print(f"{Fore.MAGENTA}🚀 MSC Evaluate - Simple Test Suite")
        print("=" * 60)
        
        self.test_frontend_accessibility()
        self.test_api_endpoints()
        self.test_lambda_functions_directly()
        
        self.analyze_errors_and_suggest_fixes()
        self.generate_fix_commands()
        
        print(f"\n{Fore.CYAN}📊 TEST SUMMARY")
        print("=" * 30)
        print(f"Errors found: {len(self.errors_found)}")
        print(f"Frontend URL: {self.base_url}")
        print(f"API URL: {self.api_url}")

def main():
    test = SimpleMSCTest()
    test.run_tests()

if __name__ == "__main__":
    main()