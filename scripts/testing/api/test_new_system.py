#!/usr/bin/env python3
"""
Test the new faculty unavailability system
"""

import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def login_user(username, password):
    """Login and get token"""
    response = requests.post(f"{BASE_URL}/users/login", json={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Login failed for {username}: {response.status_code} - {response.text}")
        return None

def test_new_system():
    """Test the new faculty unavailability system"""
    print("🧪 Testing New Faculty Unavailability System")
    print("=" * 50)
    
    # Step 1: Login as admin
    print("\n1️⃣ Logging in as admin...")
    admin_token = login_user("admin", "Test123")
    if not admin_token:
        return
    print("✅ Admin logged in successfully")
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Step 2: Get a faculty member
    print("\n2️⃣ Getting faculty members...")
    response = requests.get(f"{BASE_URL}/users/faculty", headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ Failed to get faculty: {response.text}")
        return
    
    faculty_users = response.json()
    if not faculty_users:
        print("❌ No faculty members found")
        return
    
    faculty_member = faculty_users[0]
    print(f"✅ Using faculty: {faculty_member['first_name']} {faculty_member['last_name']} ({faculty_member['id']})")
    
    # Step 3: Login as faculty
    print(f"\n3️⃣ Logging in as faculty...")
    faculty_token = login_user(faculty_member["username"], "Test123")
    if not faculty_token:
        print("❌ Faculty login failed")
        return
    print("✅ Faculty logged in successfully")
    
    faculty_headers = {"Authorization": f"Bearer {faculty_token}"}
    
    # Step 4: Submit a new request
    print("\n4️⃣ Submitting unavailability request...")
    tomorrow = (date.today() + timedelta(days=2)).isoformat()
    request_data = {
        "faculty_id": faculty_member["id"],
        "date": tomorrow,
        "reason": "Test request from new system",
        "unavailability_type": "personal_leave"
    }
    
    response = requests.post(
        f"{BASE_URL}/faculty-availability/unavailability-requests",
        json=request_data,
        headers=faculty_headers
    )
    
    if response.status_code == 200:
        request_response = response.json()
        request_id = request_response["record_id"]
        print(f"✅ Request submitted successfully!")
        print(f"   ID: {request_id}")
        print(f"   Date: {request_response['date']}")
        print(f"   Status: {request_response['status']}")
    else:
        print(f"❌ Failed to submit request: {response.status_code} - {response.text}")
        return
    
    # Step 5: Check pending requests
    print("\n5️⃣ Checking pending requests...")
    response = requests.get(
        f"{BASE_URL}/faculty-availability/unavailability-requests/pending",
        headers=admin_headers
    )
    
    if response.status_code == 200:
        pending_requests = response.json()
        print(f"✅ Found {len(pending_requests)} pending request(s)")
        for req in pending_requests:
            print(f"   • {req['faculty_name']} - {req['date']} - {req['reason']}")
    else:
        print(f"❌ Failed to get pending requests: {response.status_code} - {response.text}")
        print(f"   Response: {response.text}")
    
    # Step 6: Approve the request
    print("\n6️⃣ Approving the request...")
    approval_data = {
        "status": "approved",
        "admin_notes": "Test approval"
    }
    
    response = requests.put(
        f"{BASE_URL}/faculty-availability/unavailability-requests/{request_id}/status",
        json=approval_data,
        headers=admin_headers
    )
    
    if response.status_code == 200:
        approved_request = response.json()
        print("✅ Request approved successfully!")
        print(f"   Status: {approved_request['status']}")
        print(f"   Approved by: {approved_request['approved_by']}")
    else:
        print(f"❌ Failed to approve request: {response.status_code} - {response.text}")
    
    # Step 7: Check statistics
    print("\n7️⃣ Checking statistics...")
    response = requests.get(f"{BASE_URL}/faculty-availability/statistics", headers=admin_headers)
    if response.status_code == 200:
        stats = response.json()
        print("✅ Statistics:")
        print(f"   Total: {stats['total_requests']}")
        print(f"   Pending: {stats['pending_requests']}")
        print(f"   Approved: {stats['approved_requests']}")
    else:
        print(f"❌ Failed to get statistics: {response.text}")

if __name__ == "__main__":
    test_new_system() 