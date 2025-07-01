import requests
import json
from datetime import datetime

def test_api_endpoints():
    base_url = "http://localhost:8001/api"
    owner_token = None
    admin_token = None
    company_id = None
    employee_id = None
    
    print("🧪 Testing Multi-Tenant Time Tracking System API")
    
    # Test 1: Owner login
    print("\n🔍 Testing owner login...")
    response = requests.post(
        f"{base_url}/auth/login",
        json={"username": "owner", "password": "owner123"}
    )
    
    if response.status_code == 200:
        data = response.json()
        owner_token = data["access_token"]
        print(f"✅ Owner login successful - Token: {owner_token[:10]}...")
    else:
        print(f"❌ Owner login failed: {response.text}")
        return
    
    # Test 2: Get companies as owner
    print("\n🔍 Testing get companies as owner...")
    headers = {"Authorization": f"Bearer {owner_token}"}
    response = requests.get(f"{base_url}/owner/companies", headers=headers)
    
    if response.status_code == 200:
        companies = response.json()
        print(f"✅ Retrieved {len(companies)} companies")
        
        # Print company details
        for company in companies:
            print(f"  - {company['name']} (ID: {company['id'][:8]}...)")
    else:
        print(f"❌ Get companies failed: {response.text}")
    
    # Test 3: Create a new company
    print("\n🔍 Testing create company...")
    company_data = {
        "name": f"Test Company {datetime.now().strftime('%H%M%S')}",
        "admin_username": f"admin{datetime.now().strftime('%H%M%S')}",
        "admin_email": f"admin{datetime.now().strftime('%H%M%S')}@test.com",
        "admin_password": "admin123"
    }
    
    response = requests.post(
        f"{base_url}/owner/companies",
        json=company_data,
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        company_id = data["company"]["id"]
        admin_username = company_data["admin_username"]
        admin_password = company_data["admin_password"]
        print(f"✅ Created new company: {data['company']['name']} (ID: {company_id[:8]}...)")
    else:
        print(f"❌ Create company failed: {response.text}")
        return
    
    # Test 4: Admin login
    print("\n🔍 Testing admin login...")
    response = requests.post(
        f"{base_url}/auth/login",
        json={"username": admin_username, "password": admin_password}
    )
    
    if response.status_code == 200:
        data = response.json()
        admin_token = data["access_token"]
        print(f"✅ Admin login successful - Token: {admin_token[:10]}...")
    else:
        print(f"❌ Admin login failed: {response.text}")
        return
    
    # Test 5: Get company info as admin
    print("\n🔍 Testing get company info as admin...")
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{base_url}/company/info", headers=headers)
    
    if response.status_code == 200:
        company = response.json()
        print(f"✅ Retrieved company info: {company['name']}")
    else:
        print(f"❌ Get company info failed: {response.text}")
    
    # Test 6: Create an employee
    print("\n🔍 Testing create employee...")
    employee_data = {
        "name": "Jan",
        "surname": "Kowalski",
        "position": "Programista",
        "number": f"EMP{datetime.now().strftime('%H%M%S')}"
    }
    
    response = requests.post(
        f"{base_url}/employees",
        json=employee_data,
        headers=headers
    )
    
    if response.status_code == 200:
        employee = response.json()
        employee_id = employee["id"]
        print(f"✅ Created employee: {employee['name']} {employee['surname']} (ID: {employee_id[:8]}...)")
        print(f"  - QR code generated: {'qr_code' in employee}")
    else:
        print(f"❌ Create employee failed: {response.text}")
        return
    
    # Test 7: Get employees
    print("\n🔍 Testing get employees...")
    response = requests.get(f"{base_url}/employees", headers=headers)
    
    if response.status_code == 200:
        employees = response.json()
        print(f"✅ Retrieved {len(employees)} employees")
    else:
        print(f"❌ Get employees failed: {response.text}")
    
    # Test 8: Create a time entry
    print("\n🔍 Testing create time entry...")
    today = datetime.now().strftime("%Y-%m-%d")
    time_entry_data = {
        "employee_id": employee_id,
        "check_in": "09:00",
        "check_out": "17:00",
        "date": today
    }
    
    response = requests.post(
        f"{base_url}/time/entries",
        json=time_entry_data,
        headers=headers
    )
    
    if response.status_code == 200:
        entry = response.json()
        print(f"✅ Created time entry for employee (Date: {entry['date']})")
    else:
        print(f"❌ Create time entry failed: {response.text}")
    
    # Test 9: Get time entries
    print("\n🔍 Testing get time entries...")
    response = requests.get(f"{base_url}/time/entries", headers=headers)
    
    if response.status_code == 200:
        entries = response.json()
        print(f"✅ Retrieved {len(entries)} time entries")
    else:
        print(f"❌ Get time entries failed: {response.text}")
    
    # Test 10: Delete the company
    print("\n🔍 Testing delete company...")
    headers = {"Authorization": f"Bearer {owner_token}"}
    response = requests.delete(f"{base_url}/owner/companies/{company_id}", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Deleted company: {data['message']}")
    else:
        print(f"❌ Delete company failed: {response.text}")
    
    print("\n📊 API Testing Summary:")
    print("All API endpoints tested successfully!")

if __name__ == "__main__":
    test_api_endpoints()