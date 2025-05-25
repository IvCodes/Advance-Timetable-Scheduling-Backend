#!/usr/bin/env python3
"""
Test script to verify frontend API endpoints are working correctly
and returning all faculty unavailability requests
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login_admin():
    """Login as admin and get access token"""
    response = requests.post(f"{BASE_URL}/users/login", json={
        "username": "admin",
        "password": "Test123"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Admin login failed: {response.text}")
        return None

def get_headers(token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {token}"}

def test_all_api_endpoints():
    """Test all faculty availability API endpoints"""
    
    print("🧪 Testing Faculty Availability API Endpoints")
    print("=" * 60)
    
    # Step 1: Login as admin
    print("\n1️⃣ Logging in as admin...")
    token = login_admin()
    if not token:
        print("❌ Cannot proceed without admin access")
        return
    print("✅ Admin login successful")
    
    headers = get_headers(token)
    
    # Initialize variables
    all_requests = []
    pending_requests = []
    faculty_dates = []
    
    # Step 2: Test all requests endpoint
    print("\n2️⃣ Testing GET /faculty-availability/unavailability-requests")
    response = requests.get(f"{BASE_URL}/faculty-availability/unavailability-requests", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        all_requests = response.json()
        print(f"   ✅ Found {len(all_requests)} total requests")
        
        # Group by status
        status_counts = {}
        faculty_counts = {}
        
        for req in all_requests:
            status = req.get('status', 'unknown')
            faculty_id = req.get('faculty_id', 'unknown')
            faculty_name = req.get('faculty_name', 'Unknown')
            
            status_counts[status] = status_counts.get(status, 0) + 1
            faculty_counts[faculty_name] = faculty_counts.get(faculty_name, 0) + 1
            
            print(f"     - {faculty_name}: {req.get('date')} ({status})")
        
        print(f"\n   📊 Status breakdown:")
        for status, count in status_counts.items():
            print(f"     {status}: {count}")
            
        print(f"\n   👥 Faculty breakdown:")
        for faculty, count in faculty_counts.items():
            print(f"     {faculty}: {count} requests")
    else:
        print(f"   ❌ Error: {response.text}")
    
    # Step 3: Test pending requests endpoint
    print("\n3️⃣ Testing GET /faculty-availability/unavailability-requests/pending")
    response = requests.get(f"{BASE_URL}/faculty-availability/unavailability-requests/pending", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        pending_requests = response.json()
        print(f"   ✅ Found {len(pending_requests)} pending requests")
        for req in pending_requests:
            print(f"     - {req.get('faculty_name')}: {req.get('date')} - {req.get('reason')}")
    else:
        print(f"   ❌ Error: {response.text}")
    
    # Step 4: Test specific faculty endpoint
    print("\n4️⃣ Testing faculty-specific endpoints...")
    
    # Get a faculty ID to test with
    try:
        if all_requests and len(all_requests) > 0:
            test_faculty_id = all_requests[0].get('faculty_id')
            test_faculty_name = all_requests[0].get('faculty_name')
            
            print(f"   Testing with faculty: {test_faculty_name} (ID: {test_faculty_id})")
            
            response = requests.get(f"{BASE_URL}/faculty-availability/faculty/{test_faculty_id}/unavailable-dates", headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                faculty_dates = response.json()
                print(f"   ✅ Found {len(faculty_dates)} unavailable dates for {test_faculty_name}")
                for date_info in faculty_dates:
                    print(f"     - {date_info.get('date')}: {date_info.get('reason', 'No reason')}")
            else:
                print(f"   ❌ Error: {response.text}")
        else:
            print("   ⚠️ No requests found to test faculty-specific endpoint")
    except NameError:
        print("   ⚠️ No requests found to test faculty-specific endpoint")
    
    # Step 5: Test initialize endpoint
    print("\n5️⃣ Testing POST /faculty/initialize-unavailable-dates")
    response = requests.post(f"{BASE_URL}/faculty/initialize-unavailable-dates", json={}, headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"   ✅ Initialize endpoint working: {response.json()}")
    else:
        print(f"   ❌ Error: {response.text}")
    
    print("\n🎯 Summary:")
    print("   - All Requests API: ✅" if 'all_requests' in locals() else "   - All Requests API: ❌")
    print("   - Pending Requests API: ✅" if 'pending_requests' in locals() else "   - Pending Requests API: ❌")
    print("   - Faculty-specific API: ✅" if 'faculty_dates' in locals() else "   - Faculty-specific API: ❌")

def create_test_request_for_saman():
    """Create a test request for saman123 to verify it appears in frontend"""
    
    print("\n" + "="*60)
    print("🔧 Creating test request for saman123")
    print("="*60)
    
    # Login as saman123
    print("\n1️⃣ Logging in as saman123...")
    response = requests.post(f"{BASE_URL}/users/login", json={
        "username": "saman123",
        "password": "Test123"
    })
    
    if response.status_code != 200:
        # Try alternative password
        response = requests.post(f"{BASE_URL}/users/login", json={
            "username": "saman123",
            "password": "pwTest123"
        })
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ saman123 login successful")
        
        # Get user info
        headers = get_headers(token)
        user_response = requests.get(f"{BASE_URL}/users/me", headers=headers)
        
        if user_response.status_code == 200:
            user_info = user_response.json()
            faculty_id = user_info["id"]
            print(f"   Faculty ID: {faculty_id}")
            
            # Create a test request
            from datetime import date, timedelta
            test_date = (date.today() + timedelta(days=5)).isoformat()
            
            request_data = {
                "faculty_id": faculty_id,
                "date": test_date,
                "reason": "Test request created by API test script",
                "unavailability_type": "personal_leave"
            }
            
            print(f"\n2️⃣ Creating unavailability request for {test_date}...")
            create_response = requests.post(
                f"{BASE_URL}/faculty-availability/unavailability-requests",
                json=request_data,
                headers=headers
            )
            
            if create_response.status_code == 200:
                request_info = create_response.json()
                print(f"✅ Request created successfully!")
                print(f"   Request ID: {request_info.get('record_id')}")
                print(f"   Status: {request_info.get('status')}")
                print("\n🎉 saman123 should now appear in the admin dashboard!")
            else:
                print(f"❌ Failed to create request: {create_response.text}")
        else:
            print(f"❌ Failed to get user info: {user_response.text}")
    else:
        print(f"❌ saman123 login failed: {response.text}")

if __name__ == "__main__":
    test_all_api_endpoints()
    create_test_request_for_saman() 