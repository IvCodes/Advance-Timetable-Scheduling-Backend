from app.utils.database import db

print("=== Checking Faculty Unavailability Data ===")

# Check Users collection for unavailable_dates
print("\n1. Users with unavailable_dates:")
users = list(db["Users"].find({"role": "faculty", "unavailable_dates": {"$exists": True}}))
print(f"Found {len(users)} faculty with unavailable_dates")
for user in users[:3]:
    unavailable_count = len(user.get("unavailable_dates", []))
    print(f"  {user.get('first_name')} {user.get('last_name')} (ID: {user.get('id')}): {unavailable_count} dates")
    if unavailable_count > 0:
        for date_entry in user.get("unavailable_dates", [])[:2]:
            print(f"    - {date_entry.get('date')}: {date_entry.get('reason', 'No reason')}")

# Check faculty_unavailability collection
print("\n2. Faculty Unavailability Collection:")
try:
    unavailability_records = list(db["faculty_unavailability"].find())
    print(f"Found {len(unavailability_records)} records in faculty_unavailability collection")
    for record in unavailability_records[:3]:
        print(f"  Faculty ID: {record.get('faculty_id')}, Date: {record.get('date')}, Status: {record.get('status')}")
except Exception as e:
    print(f"Error accessing faculty_unavailability collection: {e}")

# Check specific user ruwan123
print("\n3. Checking user 'ruwan123':")
ruwan_user = db["Users"].find_one({"username": "ruwan123"})
if ruwan_user:
    print(f"Found user: {ruwan_user.get('first_name')} {ruwan_user.get('last_name')}")
    print(f"User ID: {ruwan_user.get('id')}")
    print(f"Role: {ruwan_user.get('role')}")
    unavailable_dates = ruwan_user.get("unavailable_dates", [])
    print(f"Unavailable dates: {len(unavailable_dates)}")
    for date_entry in unavailable_dates:
        print(f"  - {date_entry}")
else:
    print("User 'ruwan123' not found")

print("\n=== End Check ===") 