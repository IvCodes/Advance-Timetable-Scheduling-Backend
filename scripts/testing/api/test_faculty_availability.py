#!/usr/bin/env python3
"""
Test script for Faculty Unavailability Management System

This script demonstrates the complete workflow:
1. Faculty submits unavailability request
2. Admin receives notification
3. Admin approves/denies request and assigns substitute
4. All parties receive appropriate notifications

Usage:
    python test_faculty_availability.py

Prerequisites:
    - Server running on localhost:8000
    - Admin user: username=admin, password=Test123
    - Faculty user: any faculty member with username/password=Test123
"""

import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def login(username, password):
    """Login and get access token"""
    response = requests.post(f"{BASE_URL}/users/login", data={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed for {username}: {response.text}")
        return None

def get_headers(token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {token}"}

def test_faculty_unavailability_workflow():
    """Test the complete faculty unavailability workflow"""
    
    print("🧪 Testing Faculty Unavailability Management System")
    print("=" * 60)
    
    # Step 1: Login as admin
    print("\n1️⃣ Logging in as admin...")
    admin_token = login("admin", "Test123")
    if not admin_token:
        print("❌ Admin login failed")
        return
    print("✅ Admin logged in successfully")
    
    # Step 2: Get list of faculty members
    print("\n2️⃣ Getting faculty members...")
    response = requests.get(f"{BASE_URL}/users", headers=get_headers(admin_token))
    if response.status_code == 200:
        users = response.json()
        faculty_members = [user for user in users if user.get("role") == "faculty"]
        if not faculty_members:
            print("❌ No faculty members found")
            return
        faculty_member = faculty_members[0]
        print(f"✅ Found faculty member: {faculty_member['first_name']} {faculty_member['last_name']} (ID: {faculty_member['id']})")
    else:
        print(f"❌ Failed to get users: {response.text}")
        return
    
    # Step 3: Login as faculty member
    print(f"\n3️⃣ Logging in as faculty member...")
    faculty_token = login(faculty_member["username"], "Test123")
    if not faculty_token:
        print("❌ Faculty login failed")
        return
    print("✅ Faculty logged in successfully")
    
    # Step 4: Submit unavailability request
    print("\n4️⃣ Submitting unavailability request...")
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    request_data = {
        "faculty_id": faculty_member["id"],
        "date": tomorrow,
        "reason": "Medical appointment",
        "unavailability_type": "personal_leave"
    }
    
    response = requests.post(
        f"{BASE_URL}/faculty-availability/unavailability-requests",
        json=request_data,
        headers=get_headers(faculty_token)
    )
    
    if response.status_code == 200:
        request_response = response.json()
        request_id = request_response["record_id"]
        print(f"✅ Unavailability request submitted successfully (ID: {request_id})")
        print(f"   Date: {request_response['date']}")
        print(f"   Reason: {request_response['reason']}")
        print(f"   Status: {request_response['status']}")
    else:
        print(f"❌ Failed to submit request: {response.text}")
        return
    
    # Step 5: Check admin notifications
    print("\n5️⃣ Checking admin notifications...")
    response = requests.get(f"{BASE_URL}/notifications", headers=get_headers(admin_token))
    if response.status_code == 200:
        notifications = response.json()
        faculty_notifications = [n for n in notifications if n.get("category") == "faculty_unavailability"]
        if faculty_notifications:
            print(f"✅ Admin received {len(faculty_notifications)} faculty unavailability notification(s)")
            for notif in faculty_notifications[:1]:  # Show first one
                print(f"   Title: {notif['title']}")
                print(f"   Message: {notif['message']}")
        else:
            print("⚠️ No faculty unavailability notifications found")
    else:
        print(f"❌ Failed to get notifications: {response.text}")
    
    # Step 6: Get pending requests (admin view)
    print("\n6️⃣ Getting pending requests...")
    response = requests.get(
        f"{BASE_URL}/faculty-availability/unavailability-requests/pending",
        headers=get_headers(admin_token)
    )
    if response.status_code == 200:
        pending_requests = response.json()
        print(f"✅ Found {len(pending_requests)} pending request(s)")
        for req in pending_requests:
            if req["record_id"] == request_id:
                print(f"   Request ID: {req['record_id']}")
                print(f"   Faculty: {req['faculty_name']}")
                print(f"   Date: {req['date']}")
                print(f"   Status: {req['status']}")
    else:
        print(f"❌ Failed to get pending requests: {response.text}")
    
    # Step 7: Get available substitutes
    print("\n7️⃣ Getting available substitutes...")
    response = requests.get(
        f"{BASE_URL}/faculty-availability/available-substitutes?date_str={tomorrow}",
        headers=get_headers(admin_token)
    )
    if response.status_code == 200:
        substitutes = response.json()
        print(f"✅ Found {len(substitutes)} available substitute(s)")
        if substitutes:
            substitute = substitutes[0]
            print(f"   Substitute: {substitute['name']} (ID: {substitute['id']})")
        else:
            substitute = None
            print("   No substitutes available")
    else:
        print(f"❌ Failed to get substitutes: {response.text}")
        substitute = None
    
    # Step 8: Approve request with substitute
    print("\n8️⃣ Approving request...")
    approval_data = {
        "status": "approved",
        "admin_notes": "Approved - substitute assigned"
    }
    if substitute:
        approval_data["substitute_id"] = substitute["id"]
    
    response = requests.put(
        f"{BASE_URL}/faculty-availability/unavailability-requests/{request_id}/status",
        json=approval_data,
        headers=get_headers(admin_token)
    )
    
    if response.status_code == 200:
        approved_request = response.json()
        print("✅ Request approved successfully")
        print(f"   Status: {approved_request['status']}")
        print(f"   Approved by: {approved_request['approved_by']}")
        if approved_request.get('substitute_name'):
            print(f"   Substitute: {approved_request['substitute_name']}")
    else:
        print(f"❌ Failed to approve request: {response.text}")
    
    # Step 9: Check faculty notifications
    print("\n9️⃣ Checking faculty notifications...")
    response = requests.get(f"{BASE_URL}/notifications", headers=get_headers(faculty_token))
    if response.status_code == 200:
        notifications = response.json()
        approval_notifications = [n for n in notifications if "approved" in n.get("message", "").lower()]
        if approval_notifications:
            print(f"✅ Faculty received approval notification")
            notif = approval_notifications[0]
            print(f"   Title: {notif['title']}")
            print(f"   Message: {notif['message']}")
        else:
            print("⚠️ No approval notifications found")
    else:
        print(f"❌ Failed to get faculty notifications: {response.text}")
    
    # Step 10: Get statistics
    print("\n🔟 Getting availability statistics...")
    response = requests.get(f"{BASE_URL}/faculty-availability/statistics", headers=get_headers(admin_token))
    if response.status_code == 200:
        stats = response.json()
        print("✅ Statistics retrieved:")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Pending requests: {stats['pending_requests']}")
        print(f"   Approved requests: {stats['approved_requests']}")
        print(f"   Denied requests: {stats['denied_requests']}")
        print(f"   Assigned substitutes: {stats['assigned_substitutes']}")
    else:
        print(f"❌ Failed to get statistics: {response.text}")
    
    print("\n🎉 Faculty Unavailability Management System test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_faculty_unavailability_workflow() 