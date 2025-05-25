#!/usr/bin/env python3

from app.utils.database import db

print("Assigning faculty and department fields to faculty users...")
print("=" * 60)

# Define faculty assignments based on common academic departments
faculty_assignments = {
    # Computer Science faculty
    "ruwan123": {"faculty": "Faculty of Computing", "department": "Computer Science"},
    "janith123": {"faculty": "Faculty of Computing", "department": "Computer Science"},
    "saman123": {"faculty": "Faculty of Computing", "department": "Software Engineering"},
    "nirosha123": {"faculty": "Faculty of Computing", "department": "Information Systems"},
    "amali123": {"faculty": "Faculty of Computing", "department": "Computer Science"},
    "chathura123": {"faculty": "Faculty of Computing", "department": "Software Engineering"},
    "dilshan123": {"faculty": "Faculty of Computing", "department": "Computer Science"},
    "isuru123": {"faculty": "Faculty of Computing", "department": "Information Technology"},
    "jayantha123": {"faculty": "Faculty of Computing", "department": "Computer Science"},
    "kumari123": {"faculty": "Faculty of Computing", "department": "Information Systems"},
    "lakshitha123": {"faculty": "Faculty of Computing", "department": "Software Engineering"},
    "manoj123": {"faculty": "Faculty of Computing", "department": "Computer Science"},
    "nadeeka123": {"faculty": "Faculty of Computing", "department": "Information Technology"},
}

# Get all faculty users
faculty_users = list(db["Users"].find({"role": "faculty"}))
print(f"Found {len(faculty_users)} faculty users")

updated_count = 0
for user in faculty_users:
    username = user.get("username", "")
    name = f"{user.get('first_name', '')} {user.get('last_name', '')}"
    
    # Check if user already has faculty assignment
    if user.get("faculty"):
        print(f"✓ {name} ({username}) already has faculty: {user.get('faculty')}")
        continue
    
    # Assign faculty based on username or use default
    if username in faculty_assignments:
        assignment = faculty_assignments[username]
    else:
        # Default assignment for users not in the predefined list
        assignment = {"faculty": "Faculty of Computing", "department": "Computer Science"}
    
    # Update the user
    result = db["Users"].update_one(
        {"_id": user["_id"]},
        {"$set": assignment}
    )
    
    if result.modified_count > 0:
        print(f"✓ Updated {name} ({username}): {assignment['faculty']} - {assignment['department']}")
        updated_count += 1
    else:
        print(f"✗ Failed to update {name} ({username})")

print(f"\n" + "=" * 60)
print(f"Summary:")
print(f"  Total faculty users: {len(faculty_users)}")
print(f"  Updated users: {updated_count}")
print(f"  Users with faculty field now: {db['Users'].count_documents({'role': 'faculty', 'faculty': {'$exists': True, '$ne': None}})}")

# Show sample of updated users
print(f"\nSample of updated users:")
updated_users = list(db["Users"].find({"role": "faculty", "faculty": {"$exists": True}}).limit(5))
for user in updated_users:
    print(f"  {user.get('first_name', '')} {user.get('last_name', '')} - {user.get('faculty', '')} - {user.get('department', '')}")

print("\nFaculty assignment complete!") 