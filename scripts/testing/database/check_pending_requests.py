#!/usr/bin/env python3
"""
Quick script to check pending faculty unavailability requests
"""

import requests
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def login_admin():
    """Login as admin and get token"""
    response = requests.post(f"{BASE_URL}/users/login", json={
        "username": "admin",
        "password": "Test123"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Admin login failed: {response.status_code} - {response.text}")
        return None

def check_pending_requests():
    """Check current pending requests"""
    print("🔍 Checking Faculty Unavailability Requests")
    print("=" * 50)
    
    # Login as admin
    token = login_admin()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check new endpoint for pending requests
    print("\n📋 Checking NEW endpoint (/api/v1/faculty-availability/unavailability-requests/pending):")
    response = requests.get(f"{BASE_URL}/faculty-availability/unavailability-requests/pending", headers=headers)
    if response.status_code == 200:
        pending_requests = response.json()
        print(f"✅ Found {len(pending_requests)} pending request(s) in NEW system")
        for i, req in enumerate(pending_requests, 1):
            print(f"\n   Request #{i}:")
            print(f"   📝 ID: {req.get('record_id', 'N/A')}")
            print(f"   👤 Faculty: {req.get('faculty_name', 'N/A')}")
            print(f"   🏢 Department: {req.get('department', 'N/A')}")
            print(f"   📅 Date: {req.get('date', 'N/A')}")
            print(f"   💬 Reason: {req.get('reason', 'N/A')}")
            print(f"   📊 Status: {req.get('status', 'N/A')}")
            print(f"   🕐 Created: {req.get('created_at', 'N/A')}")
    else:
        print(f"❌ Failed to get pending requests from NEW endpoint: {response.status_code} - {response.text}")
    
    # Check old endpoint for comparison
    print("\n📋 Checking OLD endpoint (/api/v1/faculty/pending-unavailability):")
    response = requests.get(f"{BASE_URL}/faculty/pending-unavailability", headers=headers)
    if response.status_code == 200:
        old_pending = response.json()
        print(f"✅ Found {len(old_pending)} pending request(s) in OLD system")
        for i, req in enumerate(old_pending, 1):
            print(f"\n   Request #{i}:")
            print(f"   👤 Faculty: {req.get('faculty_name', 'N/A')}")
            print(f"   📅 Date: {req.get('date', 'N/A')}")
            print(f"   💬 Reason: {req.get('reason', 'N/A')}")
            print(f"   📊 Status: {req.get('status', 'N/A')}")
    else:
        print(f"❌ Failed to get pending requests from OLD endpoint: {response.status_code} - {response.text}")
    
    # Check all requests
    print("\n📋 Checking ALL requests (/api/v1/faculty-availability/unavailability-requests):")
    response = requests.get(f"{BASE_URL}/faculty-availability/unavailability-requests", headers=headers)
    if response.status_code == 200:
        all_requests = response.json()
        print(f"✅ Found {len(all_requests)} total request(s)")
        
        # Group by status
        by_status = {}
        for req in all_requests:
            status = req.get('status', 'unknown')
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(req)
        
        for status, requests_list in by_status.items():
            print(f"\n   📊 {status.upper()}: {len(requests_list)} request(s)")
            for req in requests_list[:3]:  # Show first 3
                print(f"      • {req.get('faculty_name', 'N/A')} - {req.get('date', 'N/A')} - {req.get('reason', 'N/A')}")
    else:
        print(f"❌ Failed to get all requests: {response.status_code} - {response.text}")
    
    # Check statistics
    print("\n📊 Checking Statistics:")
    response = requests.get(f"{BASE_URL}/faculty-availability/statistics", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print(f"   📈 Total requests: {stats.get('total_requests', 0)}")
        print(f"   ⏳ Pending: {stats.get('pending_requests', 0)}")
        print(f"   ✅ Approved: {stats.get('approved_requests', 0)}")
        print(f"   ❌ Denied: {stats.get('denied_requests', 0)}")
        print(f"   👥 With substitutes: {stats.get('assigned_substitutes', 0)}")
    else:
        print(f"❌ Failed to get statistics: {response.status_code} - {response.text}")
    
    # Check notifications
    print("\n🔔 Checking Admin Notifications:")
    response = requests.get(f"{BASE_URL}/notifications", headers=headers)
    if response.status_code == 200:
        notifications = response.json()
        faculty_notifs = [n for n in notifications if n.get("category") == "faculty_unavailability"]
        print(f"   📬 Faculty unavailability notifications: {len(faculty_notifs)}")
        for notif in faculty_notifs[:3]:  # Show first 3
            print(f"      • {notif.get('title', 'N/A')}: {notif.get('message', 'N/A')[:60]}...")
    else:
        print(f"❌ Failed to get notifications: {response.status_code} - {response.text}")

if __name__ == "__main__":
    check_pending_requests() 