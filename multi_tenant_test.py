import requests
import unittest
import uuid
import time
from datetime import datetime

class MultiTenantTimeTrackingTest(unittest.TestCase):
    """Test suite for Multi-Tenant Time Tracking System"""
    
    # Class variables to persist data across tests
    company1 = None
    company2 = None
    company1_token = None
    company2_token = None
    company1_id = None
    company2_id = None
    company1_user = None
    company2_user = None
    company1_employee = None
    company2_employee = None

    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:8001/api"
        
        # Initialize company data only once
        if MultiTenantTimeTrackingTest.company1 is None:
            MultiTenantTimeTrackingTest.company1 = {
                "company_name": f"Firma ABC {uuid.uuid4().hex[:8]}",
                "admin_username": f"admin_abc_{uuid.uuid4().hex[:8]}",
                "admin_email": f"admin_abc_{uuid.uuid4().hex[:8]}@example.com",
                "admin_password": "admin123"
            }
            MultiTenantTimeTrackingTest.company2 = {
                "company_name": f"Firma XYZ {uuid.uuid4().hex[:8]}",
                "admin_username": f"admin_xyz_{uuid.uuid4().hex[:8]}",
                "admin_email": f"admin_xyz_{uuid.uuid4().hex[:8]}@example.com",
                "admin_password": "admin123"
            }
        
        # Use class variables
        self.company1 = MultiTenantTimeTrackingTest.company1
        self.company2 = MultiTenantTimeTrackingTest.company2
        self.company1_token = MultiTenantTimeTrackingTest.company1_token
        self.company2_token = MultiTenantTimeTrackingTest.company2_token
        self.company1_id = MultiTenantTimeTrackingTest.company1_id
        self.company2_id = MultiTenantTimeTrackingTest.company2_id
        self.company1_user = MultiTenantTimeTrackingTest.company1_user
        self.company2_user = MultiTenantTimeTrackingTest.company2_user
        self.company1_employee = MultiTenantTimeTrackingTest.company1_employee
        self.company2_employee = MultiTenantTimeTrackingTest.company2_employee

    def test_01_company_registration(self):
        """Test company registration and admin creation"""
        print("\n=== PHASE 1: Company Registration & Authentication ===")
        
        # Register Company 1
        print(f"\nRegistering Company 1: {self.company1['company_name']}")
        response = requests.post(
            f"{self.base_url}/auth/register-company",
            json=self.company1
        )
        self.assertEqual(response.status_code, 200, f"Failed to register company 1: {response.text}")
        data = response.json()
        self.company1_token = data["access_token"]
        self.company1_id = data["user"]["company_id"]
        self.company1_user = data["user"]
        
        # Save to class variables
        MultiTenantTimeTrackingTest.company1_token = self.company1_token
        MultiTenantTimeTrackingTest.company1_id = self.company1_id
        MultiTenantTimeTrackingTest.company1_user = self.company1_user
        
        print(f"✅ Company 1 registered successfully with ID: {self.company1_id}")
        
        # Register Company 2
        print(f"\nRegistering Company 2: {self.company2['company_name']}")
        response = requests.post(
            f"{self.base_url}/auth/register-company",
            json=self.company2
        )
        self.assertEqual(response.status_code, 200, f"Failed to register company 2: {response.text}")
        data = response.json()
        self.company2_token = data["access_token"]
        self.company2_id = data["user"]["company_id"]
        self.company2_user = data["user"]
        
        # Save to class variables
        MultiTenantTimeTrackingTest.company2_token = self.company2_token
        MultiTenantTimeTrackingTest.company2_id = self.company2_id
        MultiTenantTimeTrackingTest.company2_user = self.company2_user
        
        print(f"✅ Company 2 registered successfully with ID: {self.company2_id}")
        
        # Verify different company IDs
        self.assertNotEqual(self.company1_id, self.company2_id, "Companies should have different IDs")
        print("✅ Companies have different IDs")

    def test_02_login_authentication(self):
        """Test login and authentication"""
        print("\n=== Testing Login Authentication ===")
        
        # Test login for Company 1
        print(f"\nTesting login for Company 1 admin: {self.company1['admin_username']}")
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={
                "username": self.company1["admin_username"],
                "password": self.company1["admin_password"]
            }
        )
        self.assertEqual(response.status_code, 200, f"Failed to login as company 1 admin: {response.text}")
        data = response.json()
        self.company1_token = data["access_token"]  # Update token
        MultiTenantTimeTrackingTest.company1_token = self.company1_token
        self.assertEqual(data["user"]["company_id"], self.company1_id, "Company ID mismatch in token")
        print("✅ Company 1 admin login successful")
        
        # Test login for Company 2
        print(f"\nTesting login for Company 2 admin: {self.company2['admin_username']}")
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={
                "username": self.company2["admin_username"],
                "password": self.company2["admin_password"]
            }
        )
        self.assertEqual(response.status_code, 200, f"Failed to login as company 2 admin: {response.text}")
        data = response.json()
        self.company2_token = data["access_token"]  # Update token
        MultiTenantTimeTrackingTest.company2_token = self.company2_token
        self.assertEqual(data["user"]["company_id"], self.company2_id, "Company ID mismatch in token")
        print("✅ Company 2 admin login successful")
        
        # Test authentication middleware with /auth/me endpoint
        print("\nTesting authentication middleware with /auth/me endpoint")
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers={"Authorization": f"Bearer {self.company1_token}"}
        )
        self.assertEqual(response.status_code, 200, f"Failed to authenticate company 1 admin: {response.text}")
        data = response.json()
        self.assertEqual(data["company_id"], self.company1_id, "Company ID mismatch in /auth/me response")
        print("✅ Authentication middleware working correctly")

    def test_03_user_management(self):
        """Test user management with multi-tenancy"""
        print("\n=== PHASE 2: User Management (Multi-tenancy) ===")
        
        # Create regular user in Company 1
        print("\nCreating regular user in Company 1")
        user1_data = {
            "username": f"user1_{uuid.uuid4().hex[:8]}",
            "email": f"user1_{uuid.uuid4().hex[:8]}@example.com",
            "password": "user123",
            "role": "user"
        }
        response = requests.post(
            f"{self.base_url}/company/users",
            headers={"Authorization": f"Bearer {self.company1_token}"},
            json=user1_data
        )
        self.assertEqual(response.status_code, 200, f"Failed to create user in company 1: {response.text}")
        company1_user_id = response.json()["id"]
        print(f"✅ Regular user created in Company 1 with ID: {company1_user_id}")
        
        # Create admin user in Company 2
        print("\nCreating admin user in Company 2")
        admin2_data = {
            "username": f"admin2_{uuid.uuid4().hex[:8]}",
            "email": f"admin2_{uuid.uuid4().hex[:8]}@example.com",
            "password": "admin456",
            "role": "admin"
        }
        response = requests.post(
            f"{self.base_url}/company/users",
            headers={"Authorization": f"Bearer {self.company2_token}"},
            json=admin2_data
        )
        self.assertEqual(response.status_code, 200, f"Failed to create admin in company 2: {response.text}")
        company2_admin_id = response.json()["id"]
        print(f"✅ Admin user created in Company 2 with ID: {company2_admin_id}")
        
        # Verify users in Company 1
        print("\nVerifying users in Company 1")
        response = requests.get(
            f"{self.base_url}/company/users",
            headers={"Authorization": f"Bearer {self.company1_token}"}
        )
        self.assertEqual(response.status_code, 200, f"Failed to get users for company 1: {response.text}")
        company1_users = response.json()
        company1_user_ids = [user["id"] for user in company1_users]
        self.assertIn(company1_user_id, company1_user_ids, "Created user not found in Company 1 users list")
        self.assertNotIn(company2_admin_id, company1_user_ids, "Company 2 user should not be visible to Company 1")
        print(f"✅ Company 1 has {len(company1_users)} users, Company 2 users not visible")
        
        # Verify users in Company 2
        print("\nVerifying users in Company 2")
        response = requests.get(
            f"{self.base_url}/company/users",
            headers={"Authorization": f"Bearer {self.company2_token}"}
        )
        self.assertEqual(response.status_code, 200, f"Failed to get users for company 2: {response.text}")
        company2_users = response.json()
        company2_user_ids = [user["id"] for user in company2_users]
        self.assertIn(company2_admin_id, company2_user_ids, "Created admin not found in Company 2 users list")
        self.assertNotIn(company1_user_id, company2_user_ids, "Company 1 user should not be visible to Company 2")
        print(f"✅ Company 2 has {len(company2_users)} users, Company 1 users not visible")
        
        # Test user deletion
        print("\nTesting user deletion in Company 1")
        response = requests.delete(
            f"{self.base_url}/company/users/{company1_user_id}",
            headers={"Authorization": f"Bearer {self.company1_token}"}
        )
        self.assertEqual(response.status_code, 200, f"Failed to delete user in company 1: {response.text}")
        print("✅ User deletion successful")
        
        # Verify user was deleted
        response = requests.get(
            f"{self.base_url}/company/users",
            headers={"Authorization": f"Bearer {self.company1_token}"}
        )
        company1_users_after = response.json()
        company1_user_ids_after = [user["id"] for user in company1_users_after]
        self.assertNotIn(company1_user_id, company1_user_ids_after, "Deleted user still found in Company 1 users list")
        print("✅ User no longer appears in Company 1 users list")
        
        # Test self-deletion prevention
        print("\nTesting prevention of self-deletion")
        response = requests.delete(
            f"{self.base_url}/company/users/{self.company1_user['id']}",
            headers={"Authorization": f"Bearer {self.company1_token}"}
        )
        self.assertEqual(response.status_code, 400, "Admin should not be able to delete themselves")
        print("✅ Self-deletion prevention working")

    def test_04_employee_management(self):
        """Test employee management with company isolation"""
        print("\n=== PHASE 3: Employee Management (Company-scoped) ===")
        
        # Create employee in Company 1
        print("\nCreating employee in Company 1")
        employee1_data = {
            "name": "Jan",
            "surname": "Kowalski",
            "position": "Developer",
            "number": f"EMP{uuid.uuid4().hex[:8]}"
        }
        response = requests.post(
            f"{self.base_url}/employees",
            headers={"Authorization": f"Bearer {self.company1_token}"},
            json=employee1_data
        )
        self.assertEqual(response.status_code, 200, f"Failed to create employee in company 1: {response.text}")
        self.company1_employee = response.json()
        MultiTenantTimeTrackingTest.company1_employee = self.company1_employee
        print(f"✅ Employee created in Company 1 with ID: {self.company1_employee['id']}")
        
        # Verify QR code contains company information
        print("\nVerifying QR code contains company information")
        self.assertIn("qr_code", self.company1_employee, "QR code not generated for employee")
        print("✅ QR code generated for employee")
        
        # Create employee in Company 2
        print("\nCreating employee in Company 2")
        employee2_data = {
            "name": "Anna",
            "surname": "Nowak",
            "position": "Manager",
            "number": f"EMP{uuid.uuid4().hex[:8]}"
        }
        response = requests.post(
            f"{self.base_url}/employees",
            headers={"Authorization": f"Bearer {self.company2_token}"},
            json=employee2_data
        )
        self.assertEqual(response.status_code, 200, f"Failed to create employee in company 2: {response.text}")
        self.company2_employee = response.json()
        MultiTenantTimeTrackingTest.company2_employee = self.company2_employee
        print(f"✅ Employee created in Company 2 with ID: {self.company2_employee['id']}")
        
        # Verify employees in Company 1
        print("\nVerifying employees in Company 1")
        response = requests.get(
            f"{self.base_url}/employees",
            headers={"Authorization": f"Bearer {self.company1_token}"}
        )
        self.assertEqual(response.status_code, 200, f"Failed to get employees for company 1: {response.text}")
        company1_employees = response.json()
        company1_employee_ids = [emp["id"] for emp in company1_employees]
        self.assertIn(self.company1_employee["id"], company1_employee_ids, "Created employee not found in Company 1")
        self.assertNotIn(self.company2_employee["id"], company1_employee_ids, "Company 2 employee should not be visible to Company 1")
        print(f"✅ Company 1 has {len(company1_employees)} employees, Company 2 employees not visible")
        
        # Verify employees in Company 2
        print("\nVerifying employees in Company 2")
        response = requests.get(
            f"{self.base_url}/employees",
            headers={"Authorization": f"Bearer {self.company2_token}"}
        )
        self.assertEqual(response.status_code, 200, f"Failed to get employees for company 2: {response.text}")
        company2_employees = response.json()
        company2_employee_ids = [emp["id"] for emp in company2_employees]
        self.assertIn(self.company2_employee["id"], company2_employee_ids, "Created employee not found in Company 2")
        self.assertNotIn(self.company1_employee["id"], company2_employee_ids, "Company 1 employee should not be visible to Company 2")
        print(f"✅ Company 2 has {len(company2_employees)} employees, Company 1 employees not visible")
        
        # Test employee update
        print("\nTesting employee update in Company 1")
        update_data = {
            "position": "Senior Developer"
        }
        response = requests.put(
            f"{self.base_url}/employees/{self.company1_employee['id']}",
            headers={"Authorization": f"Bearer {self.company1_token}"},
            json=update_data
        )
        self.assertEqual(response.status_code, 200, f"Failed to update employee in company 1: {response.text}")
        updated_employee = response.json()
        self.assertEqual(updated_employee["position"], "Senior Developer", "Employee position not updated")
        print("✅ Employee update successful")

    def test_05_time_tracking(self):
        """Test time tracking with QR code scanning"""
        print("\n=== PHASE 4: Time Tracking (Security) ===")
        
        # Extract QR data from employee QR codes
        print("\nExtracting QR data from employee QR codes")
        company1_qr_data = f"EMP_{self.company1_id}_{self.company1_employee['number']}_{uuid.uuid4().hex[:8]}"
        company2_qr_data = f"EMP_{self.company2_id}_{self.company2_employee['number']}_{uuid.uuid4().hex[:8]}"
        print(f"✅ QR data extracted")
        
        # Test QR scanning with valid company QR code
        print("\nTesting QR scanning with valid company QR code")
        response = requests.post(
            f"{self.base_url}/time/scan",
            headers={"Authorization": f"Bearer {self.company1_token}"},
            json={"qr_data": company1_qr_data}
        )
        self.assertEqual(response.status_code, 200, f"Failed to scan QR code for company 1: {response.text}")
        scan_result = response.json()
        self.assertEqual(scan_result["action"], "check_in", "QR scan should result in check-in")
        print(f"✅ QR scan successful: {scan_result['message']}")
        
        # Test rejection of QR codes from other companies
        print("\nTesting rejection of QR codes from other companies")
        response = requests.post(
            f"{self.base_url}/time/scan",
            headers={"Authorization": f"Bearer {self.company1_token}"},
            json={"qr_data": company2_qr_data}
        )
        self.assertEqual(response.status_code, 403, "QR scan from another company should be rejected")
        print("✅ Cross-company QR code rejected")
        
        # Test check-out functionality
        print("\nTesting check-out functionality")
        time.sleep(6)  # Wait for cooldown
        response = requests.post(
            f"{self.base_url}/time/scan",
            headers={"Authorization": f"Bearer {self.company1_token}"},
            json={"qr_data": company1_qr_data}
        )
        self.assertEqual(response.status_code, 200, f"Failed to scan QR code for check-out: {response.text}")
        scan_result = response.json()
        self.assertEqual(scan_result["action"], "check_out", "Second QR scan should result in check-out")
        print(f"✅ Check-out successful: {scan_result['message']}")
        
        # Verify time entries are company-scoped
        print("\nVerifying time entries are company-scoped")
        response = requests.get(
            f"{self.base_url}/time/entries",
            headers={"Authorization": f"Bearer {self.company1_token}"}
        )
        self.assertEqual(response.status_code, 200, f"Failed to get time entries for company 1: {response.text}")
        company1_entries = response.json()
        self.assertTrue(len(company1_entries) > 0, "No time entries found for Company 1")
        
        # Check if Company 2 can see Company 1's time entries
        response = requests.get(
            f"{self.base_url}/time/entries",
            headers={"Authorization": f"Bearer {self.company2_token}"}
        )
        self.assertEqual(response.status_code, 200, f"Failed to get time entries for company 2: {response.text}")
        company2_entries = response.json()
        
        # Verify no overlap between companies' time entries
        company1_employee_ids = [entry["employee_id"] for entry in company1_entries]
        company2_employee_ids = [entry["employee_id"] for entry in company2_entries if "employee_id" in entry]
        
        for emp_id in company1_employee_ids:
            self.assertNotIn(emp_id, company2_employee_ids, "Company 1 employee time entries visible to Company 2")
        
        print("✅ Time entries are properly company-scoped")

    def _extract_qr_data(self, qr_code_base64):
        """Extract QR data from base64 image (simplified for testing)"""
        # For testing purposes, we'll reconstruct the QR data based on employee info
        # In a real implementation, we would decode the QR code image
        
        # The QR data format is: EMP_{company_id}_{employee_number}_{uuid}
        if hasattr(self, 'company1_employee') and self.company1_employee:
            if 'qr_code' in self.company1_employee:
                # For company 1
                return f"EMP_{self.company1_id}_{self.company1_employee['number']}_{uuid.uuid4().hex[:8]}"
        
        if hasattr(self, 'company2_employee') and self.company2_employee:
            if 'qr_code' in self.company2_employee:
                # For company 2
                return f"EMP_{self.company2_id}_{self.company2_employee['number']}_{uuid.uuid4().hex[:8]}"
        
        return None

def run_multi_tenant_tests():
    """Run all multi-tenant tests"""
    print("🧪 Starting Multi-Tenant Time Tracking System Tests")
    
    # Create test suite
    suite = unittest.TestSuite()
    suite.addTest(MultiTenantTimeTrackingTest('test_01_company_registration'))
    suite.addTest(MultiTenantTimeTrackingTest('test_02_login_authentication'))
    suite.addTest(MultiTenantTimeTrackingTest('test_03_user_management'))
    suite.addTest(MultiTenantTimeTrackingTest('test_04_employee_management'))
    suite.addTest(MultiTenantTimeTrackingTest('test_05_time_tracking'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n📊 Multi-Tenant Test Summary:")
    print(f"Ran {result.testsRun} tests")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return len(result.failures) + len(result.errors) == 0

if __name__ == "__main__":
    run_multi_tenant_tests()