from app.utils.database import db

print("Checking database connection...")

try:
    # List all collections
    collections = db.list_collection_names()
    print(f"Collections in database: {collections}")
    
    # Check Users collection specifically
    if 'Users' in collections:
        user_count = db['Users'].count_documents({})
        print(f"\nUsers collection has {user_count} documents")
        
        if user_count > 0:
            # Get a sample user
            sample_user = db['Users'].find_one()
            print(f"Sample user: {sample_user}")
    else:
        print("\nUsers collection does not exist")
    
    # Check faculty_unavailability collection
    if 'faculty_unavailability' in collections:
        unavail_count = db['faculty_unavailability'].count_documents({})
        print(f"\nfaculty_unavailability collection has {unavail_count} documents")
        
        if unavail_count > 0:
            # Get a sample record
            sample_record = db['faculty_unavailability'].find_one()
            print(f"Sample unavailability record: {sample_record}")
    else:
        print("\nfaculty_unavailability collection does not exist")

except Exception as e:
    print(f"Error accessing database: {e}")

print("All users in database:")
users = list(db['Users'].find({}, {'username': 1, 'first_name': 1, 'last_name': 1, 'id': 1, 'role': 1}))
for user in users[:10]:
    print(f"  {user.get('username')} - {user.get('first_name')} {user.get('last_name')} (Role: {user.get('role')}, ID: {user.get('id')})")

print(f"\nTotal users: {len(users)}")

# Check if ruwan123 exists
ruwan = db['Users'].find_one({'username': 'ruwan123'})
if ruwan:
    print(f"\nruwan123 found:")
    print(f"  Name: {ruwan.get('first_name')} {ruwan.get('last_name')}")
    print(f"  Role: {ruwan.get('role')}")
    print(f"  ID: {ruwan.get('id')}")
else:
    print("\nruwan123 not found")

# Check faculty users specifically
faculty_users = list(db['Users'].find({'role': 'faculty'}))
print(f"\nFaculty users: {len(faculty_users)}")
for user in faculty_users[:5]:
    print(f"  {user.get('username')} - {user.get('first_name')} {user.get('last_name')}") 