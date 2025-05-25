#!/usr/bin/env python3

from app.utils.database import db

print("Checking teacher faculty assignments...")
print("=" * 50)

# Check Users collection for faculty members
print("Checking Users collection for faculty members...")
faculty_users = list(db["Users"].find({"role": "faculty"}).limit(5))
print(f"Found {len(faculty_users)} faculty users")

for i, user in enumerate(faculty_users, 1):
    print(f"Faculty {i}:")
    print(f"  Name: {user.get('first_name', '')} {user.get('last_name', '')}")
    print(f"  Username: {user.get('username', '')}")
    print(f"  Faculty: {user.get('faculty', 'NOT_SET')}")
    print(f"  Department: {user.get('department', 'NOT_SET')}")
    print(f"  All fields: {list(user.keys())}")
    print("---")

print(f"\nTotal faculty users: {db['Users'].count_documents({'role': 'faculty'})}")
print(f"Faculty with faculty field: {db['Users'].count_documents({'role': 'faculty', 'faculty': {'$exists': True, '$ne': None}})}")
print(f"Faculty without faculty field: {db['Users'].count_documents({'role': 'faculty', 'faculty': {'$exists': False}})}")

# Also check if there's a separate teachers collection
print(f"\nChecking teachers collection...")
print(f"Total teachers: {db['teachers'].count_documents({})}")
if db['teachers'].count_documents({}) > 0:
    teachers = list(db['teachers'].find().limit(3))
    for i, teacher in enumerate(teachers, 1):
        print(f"Teacher {i}:")
        print(f"  Name: {teacher.get('first_name', '')} {teacher.get('last_name', '')}")
        print(f"  Faculty: {teacher.get('faculty', 'NOT_SET')}")
        print(f"  All fields: {list(teacher.keys())}")
        print("---") 