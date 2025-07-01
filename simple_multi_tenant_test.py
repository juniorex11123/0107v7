import requests
import uuid
import time

def test_multi_tenant_system():
    """Test the multi-tenant time tracking system"""
    base_url = "http://localhost:8001/api"
    
    print("🧪 Starting Multi-Tenant Time Tracking System Test")
    
    # Generate unique company names and admin usernames
    company1_name = f"Firma ABC {uuid.uuid4().hex[:8]}"
    company1_admin = f"admin_abc_{uuid.uuid4().hex[:8]}"
    company2_name = f"Firma XYZ {uuid.uuid4().hex[:8]}"
    company2_admin = f"admin_xyz_{uuid.uuid4().hex[:8]}"
    
    # Step 1: Register Company 1
    print(f"\n1. Registering Company 1: {company1_name}")
    response = requests.post(
        f"{base_url}/auth/register-company",
        json={
            "company_name": company1_name,
            "admin_username": company1_admin,
            "admin_email": f"{company1_admin}@example.com",
            "admin_password": "admin123"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to register Company 1: {response.text}")
        return False
    
    company1_data = response.json()
    company1_token = company1_data["access_token"]
    company1_id = company1_data["user"]["company_id"]
    print(f"✅ Company 1 registered with ID: {company1_id}")
    
    # Step 2: Register Company 2
    print(f"\n2. Registering Company 2: {company2_name}")
    response = requests.post(
        f"{base_url}/auth/register-company",
        json={
            "company_name": company2_name,
            "admin_username": company2_admin,
            "admin_email": f"{company2_admin}@example.com",
            "admin_password": "admin123"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to register Company 2: {response.text}")
        return False
    
    company2_data = response.json()
    company2_token = company2_data["access_token"]
    company2_id = company2_data["user"]["company_id"]
    print(f"✅ Company 2 registered with ID: {company2_id}")
    
    if company1_id == company2_id:
        print("❌ Companies have the same ID!")
        return False
    
    print("✅ Companies have different IDs")
    
    # Step 3: Create a user in Company 1
    print("\n3. Creating a user in Company 1")
    user1_username = f"user1_{uuid.uuid4().hex[:8]}"
    response = requests.post(
        f"{base_url}/company/users",
        headers={"Authorization": f"Bearer {company1_token}"},
        json={
            "username": user1_username,
            "email": f"{user1_username}@example.com",
            "password": "user123",
            "role": "user"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create user in Company 1: {response.text}")
        return False
    
    company1_user_id = response.json()["id"]
    print(f"✅ User created in Company 1 with ID: {company1_user_id}")
    
    # Step 4: Create an employee in Company 1
    print("\n4. Creating an employee in Company 1")
    employee1_number = f"EMP{uuid.uuid4().hex[:8]}"
    response = requests.post(
        f"{base_url}/employees",
        headers={"Authorization": f"Bearer {company1_token}"},
        json={
            "name": "Jan",
            "surname": "Kowalski",
            "position": "Developer",
            "number": employee1_number
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create employee in Company 1: {response.text}")
        return False
    
    company1_employee = response.json()
    company1_employee_id = company1_employee["id"]
    print(f"✅ Employee created in Company 1 with ID: {company1_employee_id}")
    
    # Step 5: Create an employee in Company 2
    print("\n5. Creating an employee in Company 2")
    employee2_number = f"EMP{uuid.uuid4().hex[:8]}"
    response = requests.post(
        f"{base_url}/employees",
        headers={"Authorization": f"Bearer {company2_token}"},
        json={
            "name": "Anna",
            "surname": "Nowak",
            "position": "Manager",
            "number": employee2_number
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create employee in Company 2: {response.text}")
        return False
    
    company2_employee = response.json()
    company2_employee_id = company2_employee["id"]
    print(f"✅ Employee created in Company 2 with ID: {company2_employee_id}")
    
    # Step 6: Verify Company 1 can only see its employees
    print("\n6. Verifying Company 1 can only see its employees")
    response = requests.get(
        f"{base_url}/employees",
        headers={"Authorization": f"Bearer {company1_token}"}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get employees for Company 1: {response.text}")
        return False
    
    company1_employees = response.json()
    company1_employee_ids = [emp["id"] for emp in company1_employees]
    
    if company1_employee_id not in company1_employee_ids:
        print("❌ Company 1 employee not found in Company 1's employee list")
        return False
    
    if company2_employee_id in company1_employee_ids:
        print("❌ Company 2 employee found in Company 1's employee list")
        return False
    
    print(f"✅ Company 1 can only see its own employees ({len(company1_employees)} employees)")
    
    # Step 7: Verify Company 2 can only see its employees
    print("\n7. Verifying Company 2 can only see its employees")
    response = requests.get(
        f"{base_url}/employees",
        headers={"Authorization": f"Bearer {company2_token}"}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get employees for Company 2: {response.text}")
        return False
    
    company2_employees = response.json()
    company2_employee_ids = [emp["id"] for emp in company2_employees]
    
    if company2_employee_id not in company2_employee_ids:
        print("❌ Company 2 employee not found in Company 2's employee list")
        return False
    
    if company1_employee_id in company2_employee_ids:
        print("❌ Company 1 employee found in Company 2's employee list")
        return False
    
    print(f"✅ Company 2 can only see its own employees ({len(company2_employees)} employees)")
    
    # Step 8: Test cross-company QR code scanning (should fail)
    print("\n8. Testing cross-company QR code scanning (should fail)")
    
    # Extract QR data from employee QR codes
    # Looking at the server code, we need to use the actual employee number from the database
    # Let's get the employee number from the employee objects
    company1_employee_number = company1_employee["number"]
    company2_employee_number = company2_employee["number"]
    
    # Create valid QR data format based on employee number and company ID
    qr_data1 = f"EMP_{company1_id}_{company1_employee_number}_12345678"
    qr_data2 = f"EMP_{company2_id}_{company2_employee_number}_12345678"
    
    # Print the QR code from the employee
    print(f"Company 1 employee QR code: {company1_employee.get('qr_code', 'No QR code found')[:100]}...")
    print(f"Company 2 employee QR code: {company2_employee.get('qr_code', 'No QR code found')[:100]}...")
    
    # Try to scan Company 2's QR code with Company 1's token (should fail)
    print(f"Company 1 ID: {company1_id}")
    print(f"Company 2 ID: {company2_id}")
    print(f"QR data 2: {qr_data2}")
    
    response = requests.post(
        f"{base_url}/time/scan",
        headers={"Authorization": f"Bearer {company1_token}"},
        json={"qr_data": qr_data2}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response text: {response.text}")
    
    if response.status_code != 403:
        print(f"❌ Cross-company QR scan should be rejected, but got status {response.status_code}")
        return False
    
    print("✅ Cross-company QR code scanning correctly rejected")
    
    # Step 9: Test valid QR code scanning
    print("\n9. Testing valid QR code scanning")
    response = requests.post(
        f"{base_url}/time/scan",
        headers={"Authorization": f"Bearer {company1_token}"},
        json={"qr_data": qr_data1}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to scan valid QR code: {response.text}")
        return False
    
    scan_result = response.json()
    if scan_result["action"] != "check_in":
        print(f"❌ Expected check-in action, got {scan_result['action']}")
        return False
    
    print(f"✅ Valid QR code scanning successful: {scan_result['message']}")
    
    # Wait for cooldown
    cooldown = scan_result.get("cooldown_seconds", 5)
    print(f"Waiting for cooldown ({cooldown}s)...")
    time.sleep(cooldown + 1)
    
    # Step 10: Test check-out
    print("\n10. Testing check-out")
    response = requests.post(
        f"{base_url}/time/scan",
        headers={"Authorization": f"Bearer {company1_token}"},
        json={"qr_data": qr_data1}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to scan QR code for check-out: {response.text}")
        return False
    
    scan_result = response.json()
    if scan_result["action"] != "check_out":
        print(f"❌ Expected check-out action, got {scan_result['action']}")
        return False
    
    print(f"✅ Check-out successful: {scan_result['message']}")
    
    # Step 11: Verify time entries are company-scoped
    print("\n11. Verifying time entries are company-scoped")
    response = requests.get(
        f"{base_url}/time/entries",
        headers={"Authorization": f"Bearer {company1_token}"}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get time entries for Company 1: {response.text}")
        return False
    
    company1_entries = response.json()
    if len(company1_entries) == 0:
        print("❌ No time entries found for Company 1")
        return False
    
    print(f"✅ Company 1 has {len(company1_entries)} time entries")
    
    # Check if Company 2 can see Company 1's time entries
    response = requests.get(
        f"{base_url}/time/entries",
        headers={"Authorization": f"Bearer {company2_token}"}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get time entries for Company 2: {response.text}")
        return False
    
    company2_entries = response.json()
    
    # Verify no overlap between companies' time entries
    company1_employee_ids_in_entries = [entry["employee_id"] for entry in company1_entries if "employee_id" in entry]
    company2_employee_ids_in_entries = [entry["employee_id"] for entry in company2_entries if "employee_id" in entry]
    
    for emp_id in company1_employee_ids_in_entries:
        if emp_id in company2_employee_ids_in_entries:
            print(f"❌ Company 1 employee time entry found in Company 2's entries: {emp_id}")
            return False
    
    print("✅ Time entries are properly company-scoped")
    
    print("\n🎉 All multi-tenant tests passed successfully!")
    return True

if __name__ == "__main__":
    test_multi_tenant_system()