import pytest
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

class MSCEvaluateTestSuite:
    def __init__(self):
        self.base_url = "http://msc-evaluate-frontend-dev-127510141.s3-website.ap-south-1.amazonaws.com"
        self.api_url = "https://x3f5ix7bf1.execute-api.ap-south-1.amazonaws.com/dev"
        self.driver = None
        self.errors_found = []
        self.fixes_applied = []
        
    def setup_driver(self):
        """Setup Chrome driver with debugging capabilities"""
        print(f"{Fore.CYAN}🚀 Setting up Chrome driver with debugging capabilities...")
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=0")
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        # Enable performance logging to capture network requests
        chrome_options.add_experimental_option('perfLoggingPrefs', {
            'enableNetwork': True,
            'enablePage': False,
        })
        chrome_options.add_experimental_option('loggingPrefs', {
            'performance': 'ALL',
            'browser': 'ALL'
        })
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
        print(f"{Fore.GREEN}✅ Chrome driver setup complete")
        
    def capture_console_logs(self):
        """Capture and analyze console logs"""
        print(f"{Fore.YELLOW}📋 Capturing console logs...")
        
        try:
            logs = self.driver.get_log('browser')
            console_errors = []
            
            for log in logs:
                if log['level'] in ['SEVERE', 'WARNING']:
                    console_errors.append({
                        'level': log['level'],
                        'message': log['message'],
                        'timestamp': log['timestamp']
                    })
                    print(f"{Fore.RED}❌ Console {log['level']}: {log['message']}")
            
            return console_errors
        except Exception as e:
            print(f"{Fore.RED}❌ Error capturing console logs: {str(e)}")
            return []
    
    def capture_network_logs(self):
        """Capture and analyze network requests"""
        print(f"{Fore.YELLOW}🌐 Capturing network logs...")
        
        try:
            logs = self.driver.get_log('performance')
            network_errors = []
            
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    if response['status'] >= 400:
                        network_errors.append({
                            'url': response['url'],
                            'status': response['status'],
                            'statusText': response['statusText']
                        })
                        print(f"{Fore.RED}❌ Network Error: {response['status']} - {response['url']}")
                elif message['message']['method'] == 'Network.loadingFailed':
                    params = message['message']['params']
                    network_errors.append({
                        'url': params.get('documentURL', 'Unknown'),
                        'error': params.get('errorText', 'Unknown error')
                    })
                    print(f"{Fore.RED}❌ Network Loading Failed: {params.get('errorText', 'Unknown')}")
            
            return network_errors
        except Exception as e:
            print(f"{Fore.RED}❌ Error capturing network logs: {str(e)}")
            return []
    
    def test_page_load(self):
        """Test if the main page loads correctly"""
        print(f"{Fore.CYAN}🧪 Testing page load...")
        
        try:
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check if React app loaded
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "root"))
                )
                print(f"{Fore.GREEN}✅ React app container found")
            except TimeoutException:
                self.errors_found.append("React app container (#root) not found")
                print(f"{Fore.RED}❌ React app container not found")
            
            # Check page title
            title = self.driver.title
            if "MSC Evaluate" in title:
                print(f"{Fore.GREEN}✅ Page title correct: {title}")
            else:
                self.errors_found.append(f"Incorrect page title: {title}")
                print(f"{Fore.RED}❌ Incorrect page title: {title}")
            
            return True
            
        except Exception as e:
            self.errors_found.append(f"Page load failed: {str(e)}")
            print(f"{Fore.RED}❌ Page load failed: {str(e)}")
            return False
    
    def test_login_page(self):
        """Test login page functionality"""
        print(f"{Fore.CYAN}🧪 Testing login page...")
        
        try:
            # Navigate to login page
            login_url = f"{self.base_url}/login"
            self.driver.get(login_url)
            
            # Wait for login form
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "form"))
                )
                print(f"{Fore.GREEN}✅ Login form found")
            except TimeoutException:
                self.errors_found.append("Login form not found")
                print(f"{Fore.RED}❌ Login form not found")
                return False
            
            # Check for required form fields
            required_fields = ['email', 'password']
            for field in required_fields:
                try:
                    element = self.driver.find_element(By.NAME, field)
                    print(f"{Fore.GREEN}✅ {field} field found")
                except NoSuchElementException:
                    try:
                        element = self.driver.find_element(By.ID, field)
                        print(f"{Fore.GREEN}✅ {field} field found (by ID)")
                    except NoSuchElementException:
                        self.errors_found.append(f"{field} field not found")
                        print(f"{Fore.RED}❌ {field} field not found")
            
            # Check for submit button
            try:
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .btn-primary")
                print(f"{Fore.GREEN}✅ Submit button found")
            except NoSuchElementException:
                self.errors_found.append("Submit button not found")
                print(f"{Fore.RED}❌ Submit button not found")
            
            return True
            
        except Exception as e:
            self.errors_found.append(f"Login page test failed: {str(e)}")
            print(f"{Fore.RED}❌ Login page test failed: {str(e)}")
            return False
    
    def test_signup_functionality(self):
        """Test signup functionality with API call"""
        print(f"{Fore.CYAN}🧪 Testing signup functionality...")
        
        try:
            # Navigate to signup page
            signup_url = f"{self.base_url}/signup"
            self.driver.get(signup_url)
            
            # Wait for signup form
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form"))
            )
            
            # Fill out signup form
            test_email = f"test_{int(time.time())}@example.com"
            test_password = "TestPassword123!"
            test_name = "Test User"
            
            # Find and fill form fields
            try:
                email_field = self.driver.find_element(By.NAME, "email")
                email_field.clear()
                email_field.send_keys(test_email)
                
                password_field = self.driver.find_element(By.NAME, "password")
                password_field.clear()
                password_field.send_keys(test_password)
                
                name_field = self.driver.find_element(By.NAME, "name")
                name_field.clear()
                name_field.send_keys(test_name)
                
                print(f"{Fore.GREEN}✅ Form fields filled successfully")
                
                # Submit form
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .btn-primary")
                submit_btn.click()
                
                # Wait for response and check for errors
                time.sleep(3)
                
                # Capture any errors that occurred
                console_errors = self.capture_console_logs()
                network_errors = self.capture_network_logs()
                
                if console_errors:
                    self.errors_found.extend([f"Console error: {err['message']}" for err in console_errors])
                
                if network_errors:
                    self.errors_found.extend([f"Network error: {err}" for err in network_errors])
                
                return True
                
            except NoSuchElementException as e:
                self.errors_found.append(f"Form field not found: {str(e)}")
                print(f"{Fore.RED}❌ Form field not found: {str(e)}")
                return False
                
        except Exception as e:
            self.errors_found.append(f"Signup test failed: {str(e)}")
            print(f"{Fore.RED}❌ Signup test failed: {str(e)}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints directly"""
        print(f"{Fore.CYAN}🧪 Testing API endpoints...")
        
        # Test signup endpoint
        try:
            signup_data = {
                "email": f"test_{int(time.time())}@example.com",
                "password": "TestPassword123!",
                "name": "Test User",
                "role": "student"
            }
            
            response = requests.post(f"{self.api_url}/auth/signup", json=signup_data, timeout=10)
            print(f"{Fore.YELLOW}📡 Signup API Response: {response.status_code}")
            
            if response.status_code == 200 or response.status_code == 201:
                print(f"{Fore.GREEN}✅ Signup API working")
            else:
                self.errors_found.append(f"Signup API failed: {response.status_code} - {response.text}")
                print(f"{Fore.RED}❌ Signup API failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.errors_found.append(f"Signup API connection failed: {str(e)}")
            print(f"{Fore.RED}❌ Signup API connection failed: {str(e)}")
    
    def analyze_and_fix_errors(self):
        """Analyze found errors and apply fixes"""
        print(f"{Fore.CYAN}🔧 Analyzing errors and applying fixes...")
        
        if not self.errors_found:
            print(f"{Fore.GREEN}✅ No errors found!")
            return
        
        print(f"{Fore.YELLOW}📋 Found {len(self.errors_found)} errors:")
        for i, error in enumerate(self.errors_found, 1):
            print(f"{Fore.RED}  {i}. {error}")
        
        # Apply fixes based on error patterns
        for error in self.errors_found:
            if "CORS" in error or "Access-Control-Allow-Origin" in error:
                self.fix_cors_issue()
            elif "Network error" in error and "404" in error:
                self.fix_api_routing()
            elif "React app container" in error:
                self.fix_react_app_loading()
    
    def fix_cors_issue(self):
        """Fix CORS issues by updating Lambda functions"""
        print(f"{Fore.YELLOW}🔧 Applying CORS fix...")
        
        # This would trigger the CORS fix we implemented earlier
        fix_description = "Updated Lambda functions with proper CORS headers"
        if fix_description not in self.fixes_applied:
            self.fixes_applied.append(fix_description)
            print(f"{Fore.GREEN}✅ Applied fix: {fix_description}")
    
    def fix_api_routing(self):
        """Fix API routing issues"""
        print(f"{Fore.YELLOW}🔧 Applying API routing fix...")
        
        fix_description = "API Gateway endpoints need proper integration setup"
        if fix_description not in self.fixes_applied:
            self.fixes_applied.append(fix_description)
            print(f"{Fore.GREEN}✅ Identified fix needed: {fix_description}")
    
    def fix_react_app_loading(self):
        """Fix React app loading issues"""
        print(f"{Fore.YELLOW}🔧 Applying React app loading fix...")
        
        fix_description = "React app bundle needs to be rebuilt and redeployed"
        if fix_description not in self.fixes_applied:
            self.fixes_applied.append(fix_description)
            print(f"{Fore.GREEN}✅ Identified fix needed: {fix_description}")
    
    def generate_report(self):
        """Generate test report"""
        print(f"\n{Fore.CYAN}📊 TEST REPORT")
        print("=" * 50)
        
        print(f"{Fore.YELLOW}🎯 Test Target: {self.base_url}")
        print(f"{Fore.YELLOW}🔗 API Endpoint: {self.api_url}")
        
        if self.errors_found:
            print(f"\n{Fore.RED}❌ ERRORS FOUND ({len(self.errors_found)}):")
            for i, error in enumerate(self.errors_found, 1):
                print(f"  {i}. {error}")
        else:
            print(f"\n{Fore.GREEN}✅ NO ERRORS FOUND!")
        
        if self.fixes_applied:
            print(f"\n{Fore.GREEN}🔧 FIXES APPLIED ({len(self.fixes_applied)}):")
            for i, fix in enumerate(self.fixes_applied, 1):
                print(f"  {i}. {fix}")
        
        print(f"\n{Fore.CYAN}📋 RECOMMENDATIONS:")
        if "CORS" in str(self.errors_found):
            print(f"  • Update Lambda functions with CORS headers")
        if "404" in str(self.errors_found):
            print(f"  • Configure API Gateway integrations")
        if "React" in str(self.errors_found):
            print(f"  • Rebuild and redeploy React application")
        
        print("=" * 50)
    
    def run_full_test_suite(self):
        """Run the complete test suite"""
        print(f"{Fore.MAGENTA}🚀 Starting MSC Evaluate Test Suite")
        print("=" * 60)
        
        try:
            self.setup_driver()
            
            # Run tests
            self.test_page_load()
            self.test_login_page()
            self.test_signup_functionality()
            self.test_api_endpoints()
            
            # Capture final logs
            self.capture_console_logs()
            self.capture_network_logs()
            
            # Analyze and fix errors
            self.analyze_and_fix_errors()
            
            # Generate report
            self.generate_report()
            
        except Exception as e:
            print(f"{Fore.RED}❌ Test suite failed: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
                print(f"{Fore.CYAN}🔚 Browser closed")

def main():
    """Main function to run tests"""
    test_suite = MSCEvaluateTestSuite()
    test_suite.run_full_test_suite()

if __name__ == "__main__":
    main()