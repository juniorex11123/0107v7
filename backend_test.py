import requests
import unittest
import sys
from datetime import datetime

class MultiTenantTimeTrackingSystemTest(unittest.TestCase):
    # Class variables to share between test methods
    owner_token = None
    admin_token = None
    test_company_id = None
    test_employee_id = None
    new_company_id = None
    
    def __init__(self, *args, **kwargs):
        super(MultiTenantTimeTrackingSystemTest, self).__init__(*args, **kwargs)
        self.base_url = "http://localhost:8001/api"

    def setUp(self):
        # Nothing to set up before each test
        pass

    def test_01_owner_login(self):
        """Test owner login functionality"""
        print("\n🔍 Testing owner login...")
        
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": "owner", "password": "owner123"}
        )
        
        self.assertEqual(response.status_code, 200, f"Failed to login as owner: {response.text}")
        data = response.json()
        
        self.assertIn("access_token", data, "Token not found in response")
        self.assertIn("user", data, "User data not found in response")
        self.assertEqual(data["user"]["type"], "owner", "User type is not owner")
        
        # Save token for later tests
        MultiTenantTimeTrackingSystemTest.owner_token = data["access_token"]
        print("✅ Owner login successful")

    def test_02_get_companies(self):
        """Test getting companies as owner"""
        print("\n🔍 Testing get companies as owner...")
        
        if not MultiTenantTimeTrackingSystemTest.owner_token:
            self.skipTest("Owner token not available")
        
        headers = {"Authorization": f"Bearer {MultiTenantTimeTrackingSystemTest.owner_token}"}
        response = requests.get(f"{self.base_url}/owner/companies", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to get companies: {response.text}")
        companies = response.json()
        
        self.assertIsInstance(companies, list, "Companies should be a list")
        
        # Find test company
        test_company = next((c for c in companies if c["name"] == "Testowa Firma"), None)
        if test_company:
            MultiTenantTimeTrackingSystemTest.test_company_id = test_company["id"]
            print(f"✅ Found test company: {test_company['name']}")
        else:
            print("⚠️ Test company 'Testowa Firma' not found")
        
        print(f"✅ Retrieved {len(companies)} companies")

    def test_03_create_company(self):
        """Test creating a new company as owner"""
        print("\n🔍 Testing create company as owner...")
        
        if not MultiTenantTimeTrackingSystemTest.owner_token:
            self.skipTest("Owner token not available")
        
        company_data = {
            "name": "Druga Firma Testowa",
            "admin_username": "admin2",
            "admin_email": "admin2@test.com",
            "admin_password": "admin123"
        }
        
        headers = {"Authorization": f"Bearer {MultiTenantTimeTrackingSystemTest.owner_token}"}
        response = requests.post(
            f"{self.base_url}/owner/companies", 
            json=company_data,
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Failed to create company: {response.text}")
        data = response.json()
        
        self.assertIn("company", data, "Company data not found in response")
        self.assertEqual(data["company"]["name"], "Druga Firma Testowa", "Company name mismatch")
        
        # Save company ID for later tests
        MultiTenantTimeTrackingSystemTest.new_company_id = data["company"]["id"]
        print(f"✅ Created new company: {data['company']['name']}")

    def test_04_admin_login(self):
        """Test admin login functionality"""
        print("\n🔍 Testing admin login...")
        
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": "admin2", "password": "admin123"}
        )
        
        self.assertEqual(response.status_code, 200, f"Failed to login as admin: {response.text}")
        data = response.json()
        
        self.assertIn("access_token", data, "Token not found in response")
        self.assertIn("user", data, "User data not found in response")
        self.assertEqual(data["user"]["role"], "admin", "User role is not admin")
        
        # Save token and company ID for later tests
        MultiTenantTimeTrackingSystemTest.admin_token = data["access_token"]
        if not MultiTenantTimeTrackingSystemTest.test_company_id:
            MultiTenantTimeTrackingSystemTest.test_company_id = data["user"]["company_id"]
        
        print("✅ Admin login successful")

    def test_05_get_company_info(self):
        """Test getting company info as admin"""
        print("\n🔍 Testing get company info as admin...")
        
        if not MultiTenantTimeTrackingSystemTest.admin_token:
            self.skipTest("Admin token not available")
        
        headers = {"Authorization": f"Bearer {MultiTenantTimeTrackingSystemTest.admin_token}"}
        response = requests.get(f"{self.base_url}/company/info", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to get company info: {response.text}")
        company = response.json()
        
        self.assertEqual(company["name"], "Druga Firma Testowa", "Company name mismatch")
        print(f"✅ Retrieved company info: {company['name']}")

    def test_06_create_employee(self):
        """Test creating an employee as admin"""
        print("\n🔍 Testing create employee as admin...")
        
        if not MultiTenantTimeTrackingSystemTest.admin_token:
            self.skipTest("Admin token not available")
        
        employee_data = {
            "name": "Jan",
            "surname": "Kowalski",
            "position": "Programista",
            "number": "EMP001"
        }
        
        headers = {"Authorization": f"Bearer {MultiTenantTimeTrackingSystemTest.admin_token}"}
        response = requests.post(
            f"{self.base_url}/employees", 
            json=employee_data,
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Failed to create employee: {response.text}")
        employee = response.json()
        
        self.assertEqual(employee["name"], "Jan", "Employee name mismatch")
        self.assertEqual(employee["surname"], "Kowalski", "Employee surname mismatch")
        self.assertIn("qr_code", employee, "QR code not found in response")
        
        # Save employee ID for later tests
        MultiTenantTimeTrackingSystemTest.test_employee_id = employee["id"]
        print(f"✅ Created employee: {employee['name']} {employee['surname']}")

    def test_07_get_employees(self):
        """Test getting employees as admin"""
        print("\n🔍 Testing get employees as admin...")
        
        if not MultiTenantTimeTrackingSystemTest.admin_token:
            self.skipTest("Admin token not available")
        
        headers = {"Authorization": f"Bearer {MultiTenantTimeTrackingSystemTest.admin_token}"}
        response = requests.get(f"{self.base_url}/employees", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to get employees: {response.text}")
        employees = response.json()
        
        self.assertIsInstance(employees, list, "Employees should be a list")
        print(f"✅ Retrieved {len(employees)} employees")

    def test_08_create_time_entry(self):
        """Test creating a time entry as admin"""
        print("\n🔍 Testing create time entry as admin...")
        
        if not MultiTenantTimeTrackingSystemTest.admin_token or not MultiTenantTimeTrackingSystemTest.test_employee_id:
            self.skipTest("Admin token or employee ID not available")
        
        today = datetime.now().strftime("%Y-%m-%d")
        time_entry_data = {
            "employee_id": MultiTenantTimeTrackingSystemTest.test_employee_id,
            "check_in": "09:00",
            "check_out": "17:00",
            "date": today
        }
        
        headers = {"Authorization": f"Bearer {MultiTenantTimeTrackingSystemTest.admin_token}"}
        response = requests.post(
            f"{self.base_url}/time/entries", 
            json=time_entry_data,
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Failed to create time entry: {response.text}")
        entry = response.json()
        
        self.assertEqual(entry["employee_id"], MultiTenantTimeTrackingSystemTest.test_employee_id, "Employee ID mismatch")
        self.assertEqual(entry["date"], today, "Date mismatch")
        self.assertEqual(entry["status"], "completed", "Status should be completed")
        
        print(f"✅ Created time entry for employee")

    def test_09_get_time_entries(self):
        """Test getting time entries as admin"""
        print("\n🔍 Testing get time entries as admin...")
        
        if not MultiTenantTimeTrackingSystemTest.admin_token:
            self.skipTest("Admin token not available")
        
        headers = {"Authorization": f"Bearer {MultiTenantTimeTrackingSystemTest.admin_token}"}
        response = requests.get(f"{self.base_url}/time/entries", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to get time entries: {response.text}")
        entries = response.json()
        
        self.assertIsInstance(entries, list, "Time entries should be a list")
        print(f"✅ Retrieved {len(entries)} time entries")

    def test_10_delete_company(self):
        """Test deleting a company as owner"""
        print("\n🔍 Testing delete company as owner...")
        
        if not MultiTenantTimeTrackingSystemTest.owner_token or not MultiTenantTimeTrackingSystemTest.new_company_id:
            self.skipTest("Owner token or new company ID not available")
        
        headers = {"Authorization": f"Bearer {MultiTenantTimeTrackingSystemTest.owner_token}"}
        response = requests.delete(
            f"{self.base_url}/owner/companies/{MultiTenantTimeTrackingSystemTest.new_company_id}", 
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Failed to delete company: {response.text}")
        data = response.json()
        
        self.assertIn("message", data, "Message not found in response")
        print(f"✅ Deleted company: {data['message']}")

    def test_11_user_type_access_control(self):
        """Test access control between different user types"""
        print("\n🔍 Testing user type access control...")
        
        if not MultiTenantTimeTrackingSystemTest.admin_token or not MultiTenantTimeTrackingSystemTest.owner_token:
            self.skipTest("Admin or owner token not available")
        
        # Admin should not be able to access owner endpoints
        admin_headers = {"Authorization": f"Bearer {MultiTenantTimeTrackingSystemTest.admin_token}"}
        admin_response = requests.get(f"{self.base_url}/owner/companies", headers=admin_headers)
        self.assertNotEqual(admin_response.status_code, 200, "Admin should not access owner endpoints")
        
        # Owner should not be able to access company-specific endpoints
        owner_headers = {"Authorization": f"Bearer {MultiTenantTimeTrackingSystemTest.owner_token}"}
        owner_response = requests.get(f"{self.base_url}/company/info", headers=owner_headers)
        self.assertNotEqual(owner_response.status_code, 200, "Owner should not access company-specific endpoints")
        
        print("✅ Access control working correctly")

def run_tests():
    """Run all tests"""
    print("🧪 Starting Multi-Tenant Time Tracking System Tests")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add tests in order
    suite.addTest(MultiTenantTimeTrackingSystemTest('test_01_owner_login'))
    suite.addTest(MultiTenantTimeTrackingSystemTest('test_02_get_companies'))
    suite.addTest(MultiTenantTimeTrackingSystemTest('test_03_create_company'))
    suite.addTest(MultiTenantTimeTrackingSystemTest('test_04_admin_login'))
    suite.addTest(MultiTenantTimeTrackingSystemTest('test_05_get_company_info'))
    suite.addTest(MultiTenantTimeTrackingSystemTest('test_06_create_employee'))
    suite.addTest(MultiTenantTimeTrackingSystemTest('test_07_get_employees'))
    suite.addTest(MultiTenantTimeTrackingSystemTest('test_08_create_time_entry'))
    suite.addTest(MultiTenantTimeTrackingSystemTest('test_09_get_time_entries'))
    suite.addTest(MultiTenantTimeTrackingSystemTest('test_10_delete_company'))
    suite.addTest(MultiTenantTimeTrackingSystemTest('test_11_user_type_access_control'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n📊 Test Summary:")
    print(f"Ran {result.testsRun} tests")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return len(result.failures) + len(result.errors) == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)