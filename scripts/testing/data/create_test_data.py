#!/usr/bin/env python3
"""
Create test data for faculty availability testing
"""

import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def login_admin():
    """Login as admin"""
    response = requests.post(f"{BASE_URL}/users/login", json={
        "username": "admin",
        "password": "Test123"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Admin login failed: {response.text}")
        return None

def create_faculty_user(token, username, first_name, last_name, password="Test123"):
    """Create a faculty user"""
    headers = {"Authorization": f"Bearer {token}"}
    
    user_data = {
        "username": username,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "email": f"{username}@university.edu",
        "role": "faculty",
        "faculty": "Engineering"
    }
    
    response = requests.post(f"{BASE_URL}/users", json=user_data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to create user {username}: {response.text}")
        return None

def create_unavailability_request(token, faculty_id, date_str, reason):
    """Create an unavailability request"""
    headers = {"Authorization": f"Bearer {token}"}
    
    request_data = {
        "faculty_id": faculty_id,
        "date": date_str,
        "reason": reason,
        "unavailability_type": "personal_leave"
    }
    
    response = requests.post(f"{BASE_URL}/faculty-availability/unavailability-requests", 
                           json=request_data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to create unavailability request: {response.text}")
        return None

def approve_request(token, request_id):
    """Approve an unavailability request"""
    headers = {"Authorization": f"Bearer {token}"}
    
    approval_data = {
        "status": "approved",
        "admin_notes": "Approved for testing"
    }
    
    response = requests.put(f"{BASE_URL}/faculty-availability/unavailability-requests/{request_id}/status",
                          json=approval_data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to approve request: {response.text}")
        return None

def main():
    print("🔧 Creating test data for faculty availability")
    print("=" * 50)
    
    # Login as admin
    print("\n1️⃣ Logging in as admin...")
    admin_token = login_admin()
    if not admin_token:
        print("❌ Cannot proceed without admin access")
        return
    print("✅ Admin login successful")
    
    # Create ruwan123 user if it doesn't exist
    print("\n2️⃣ Creating ruwan123 user...")
    ruwan_user = create_faculty_user(admin_token, "ruwan123", "Ruwan", "Jayawardena", "pwTest123")
    if ruwan_user:
        print(f"✅ Created user: {ruwan_user['first_name']} {ruwan_user['last_name']} (ID: {ruwan_user['id']})")
        ruwan_id = ruwan_user['id']
    else:
        # User might already exist, try to get it
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            ruwan_user = next((u for u in users if u.get('username') == 'ruwan123'), None)
            if ruwan_user:
                print(f"✅ Found existing user: {ruwan_user['first_name']} {ruwan_user['last_name']} (ID: {ruwan_user['id']})")
                ruwan_id = ruwan_user['id']
            else:
                print("❌ Could not find or create ruwan123 user")
                return
        else:
            print("❌ Could not fetch users")
            return
    
    # Create some unavailability requests
    print("\n3️⃣ Creating unavailability requests...")
    
    # Request 1: Tomorrow (pending)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    request1 = create_unavailability_request(admin_token, ruwan_id, tomorrow, "Medical appointment")
    if request1:
        print(f"✅ Created request for {tomorrow}: {request1['reason']}")
    
    # Request 2: Day after tomorrow (will be approved)
    day_after = (date.today() + timedelta(days=2)).isoformat()
    request2 = create_unavailability_request(admin_token, ruwan_id, day_after, "Personal leave")
    if request2:
        print(f"✅ Created request for {day_after}: {request2['reason']}")
        
        # Approve this request
        print(f"   Approving request {request2['record_id']}...")
        approved = approve_request(admin_token, request2['record_id'])
        if approved:
            print(f"   ✅ Request approved")
        else:
            print(f"   ❌ Failed to approve request")
    
    # Request 3: Next week (will be approved)
    next_week = (date.today() + timedelta(days=7)).isoformat()
    request3 = create_unavailability_request(admin_token, ruwan_id, next_week, "Conference attendance")
    if request3:
        print(f"✅ Created request for {next_week}: {request3['reason']}")
        
        # Approve this request
        print(f"   Approving request {request3['record_id']}...")
        approved = approve_request(admin_token, request3['record_id'])
        if approved:
            print(f"   ✅ Request approved")
        else:
            print(f"   ❌ Failed to approve request")
    
    print("\n🎉 Test data creation complete!")
    print("\nYou can now test:")
    print("- Faculty Dashboard: Login as ruwan123 / pwTest123")
    print("- Admin Dashboard: Login as admin / Test123")

if __name__ == "__main__":
    main() 