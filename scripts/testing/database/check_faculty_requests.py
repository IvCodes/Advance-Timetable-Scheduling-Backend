#!/usr/bin/env python3
"""
Check all faculty unavailability requests in the database
"""

from app.utils.database import db

print("=== Checking Faculty Unavailability Requests ===")

# Check faculty_unavailability collection
try:
    requests = list(db["faculty_unavailability"].find())
    print(f"\nFound {len(requests)} total requests in faculty_unavailability collection:")
    
    for i, request in enumerate(requests, 1):
        print(f"\n{i}. Request ID: {request.get('record_id')}")
        print(f"   Faculty ID: {request.get('faculty_id')}")
        print(f"   Faculty Name: {request.get('faculty_name')}")
        print(f"   Date: {request.get('date')}")
        print(f"   Reason: {request.get('reason')}")
        print(f"   Status: {request.get('status')}")
        print(f"   Substitute ID: {request.get('substitute_id')}")
        print(f"   Substitute Name: {request.get('substitute_name')}")
        print(f"   Created: {request.get('created_at')}")
        print(f"   Type: {request.get('unavailability_type')}")
        
except Exception as e:
    print(f"Error accessing faculty_unavailability collection: {e}")

# Check for saman123 specifically
print("\n" + "="*50)
print("Looking for saman123 specifically...")

# First check if saman123 user exists
saman_user = db["Users"].find_one({"username": "saman123"})
if saman_user:
    print(f"\n✅ Found saman123 user:")
    print(f"   Name: {saman_user.get('first_name')} {saman_user.get('last_name')}")
    print(f"   ID: {saman_user.get('id')}")
    print(f"   Role: {saman_user.get('role')}")
    
    # Look for requests by this faculty ID
    saman_requests = list(db["faculty_unavailability"].find({"faculty_id": saman_user.get('id')}))
    print(f"\n   Requests by saman123: {len(saman_requests)}")
    for req in saman_requests:
        print(f"     - Date: {req.get('date')}, Status: {req.get('status')}, Reason: {req.get('reason')}")
else:
    print("\n❌ saman123 user not found")

# Check all faculty users
print("\n" + "="*50)
print("All faculty users:")
faculty_users = list(db["Users"].find({"role": "faculty"}))
for user in faculty_users:
    user_id = user.get('id')
    username = user.get('username')
    name = f"{user.get('first_name')} {user.get('last_name')}"
    
    # Count requests for this faculty
    request_count = db["faculty_unavailability"].count_documents({"faculty_id": user_id})
    print(f"   {username} ({name}) - ID: {user_id} - Requests: {request_count}")

print("\n=== End Check ===") 