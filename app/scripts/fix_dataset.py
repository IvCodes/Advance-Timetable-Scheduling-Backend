#!/usr/bin/env python3
"""
Dataset Fix Script
==================

This script fixes the critical duplicate room issue in sliit_computing_dataset.json
and optionally adds more rooms and time structure.
"""

import json
import os
from datetime import datetime

def backup_original_file():
    """Create a backup of the original file"""
    original_file = "app/algorithms_2/sliit_computing_dataset.json"
    backup_file = f"app/algorithms_2/sliit_computing_dataset_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    if os.path.exists(original_file):
        with open(original_file, 'r') as f:
            data = json.load(f)
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Backup created: {backup_file}")
        return True
    else:
        print(f"❌ Original file not found: {original_file}")
        return False

def fix_duplicate_rooms():
    """Fix the duplicate room issue"""
    print("🔧 FIXING DUPLICATE ROOMS")
    print("=" * 40)
    
    file_path = "app/algorithms_2/sliit_computing_dataset.json"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        # Load the current data
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        print(f"📊 Original spaces count: {len(data.get('spaces', []))}")
        
        # Define unique spaces (removing duplicates, keeping higher capacities)
        unique_spaces = [
            {
                "name": "A401",
                "long_name": "Main Lecture Hall A401",
                "code": "LH401",
                "capacity": 250,
                "type": "lecture_hall",
                "attributes": {
                    "projector": "Yes",
                    "computers": "No",
                    "air_conditioned": "Yes"
                }
            },
            {
                "name": "A501",
                "long_name": "Main Lecture Hall A501", 
                "code": "LH501",
                "capacity": 300,
                "type": "lecture_hall",
                "attributes": {
                    "projector": "Yes",
                    "computers": "No",
                    "air_conditioned": "Yes"
                }
            },
            {
                "name": "B501",
                "long_name": "Computer Lab B501",
                "code": "LAB501", 
                "capacity": 100,
                "type": "computer_lab",
                "attributes": {
                    "projector": "Yes",
                    "computers": "Yes",
                    "air_conditioned": "Yes"
                }
            },
            {
                "name": "B502",
                "long_name": "Computer Lab B502",
                "code": "LAB502",
                "capacity": 80,
                "type": "computer_lab", 
                "attributes": {
                    "projector": "Yes",
                    "computers": "Yes",
                    "air_conditioned": "Yes"
                }
            }
        ]
        
        # Replace the spaces array
        data['spaces'] = unique_spaces
        
        print(f"📊 Fixed spaces count: {len(data['spaces'])}")
        print("✅ Removed duplicates:")
        for space in unique_spaces:
            print(f"   - {space['code']}: {space['name']} (capacity: {space['capacity']})")
        
        # Save the fixed data
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Fixed dataset saved to: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing dataset: {e}")
        return False

def add_more_rooms():
    """Add more rooms to improve scheduling options"""
    print("\n🏢 ADDING MORE ROOMS")
    print("=" * 40)
    
    file_path = "app/algorithms_2/sliit_computing_dataset.json"
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Additional rooms to add
        additional_rooms = [
            {
                "name": "A301",
                "long_name": "Lecture Hall A301",
                "code": "LH301",
                "capacity": 150,
                "type": "lecture_hall",
                "attributes": {
                    "projector": "Yes",
                    "computers": "No",
                    "air_conditioned": "Yes"
                }
            },
            {
                "name": "A302", 
                "long_name": "Lecture Hall A302",
                "code": "LH302",
                "capacity": 120,
                "type": "lecture_hall",
                "attributes": {
                    "projector": "Yes",
                    "computers": "No",
                    "air_conditioned": "Yes"
                }
            },
            {
                "name": "B301",
                "long_name": "Computer Lab B301",
                "code": "LAB301",
                "capacity": 50,
                "type": "computer_lab",
                "attributes": {
                    "projector": "Yes",
                    "computers": "Yes",
                    "air_conditioned": "Yes"
                }
            },
            {
                "name": "B302",
                "long_name": "Computer Lab B302", 
                "code": "LAB302",
                "capacity": 45,
                "type": "computer_lab",
                "attributes": {
                    "projector": "Yes",
                    "computers": "Yes",
                    "air_conditioned": "Yes"
                }
            },
            {
                "name": "C101",
                "long_name": "Seminar Room C101",
                "code": "SEM101",
                "capacity": 30,
                "type": "seminar_room",
                "attributes": {
                    "projector": "Yes",
                    "computers": "No",
                    "air_conditioned": "Yes"
                }
            },
            {
                "name": "C102",
                "long_name": "Seminar Room C102",
                "code": "SEM102", 
                "capacity": 25,
                "type": "seminar_room",
                "attributes": {
                    "projector": "Yes",
                    "computers": "No",
                    "air_conditioned": "Yes"
                }
            }
        ]
        
        # Add the new rooms
        data['spaces'].extend(additional_rooms)
        
        print(f"📊 Total spaces after addition: {len(data['spaces'])}")
        print("✅ Added rooms:")
        for room in additional_rooms:
            print(f"   - {room['code']}: {room['name']} (capacity: {room['capacity']}, type: {room['type']})")
        
        # Save the updated data
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Enhanced dataset saved to: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error adding rooms: {e}")
        return False

def verify_fix():
    """Verify that the fix worked correctly"""
    print("\n🔍 VERIFYING FIX")
    print("=" * 40)
    
    file_path = "app/algorithms_2/sliit_computing_dataset.json"
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        spaces = data.get('spaces', [])
        print(f"📊 Total spaces: {len(spaces)}")
        
        # Check for duplicates
        codes = [space.get('code', '') for space in spaces]
        names = [space.get('name', '') for space in spaces]
        
        duplicate_codes = [code for code in set(codes) if codes.count(code) > 1]
        duplicate_names = [name for name in set(names) if names.count(name) > 1]
        
        if duplicate_codes:
            print(f"❌ Duplicate codes found: {duplicate_codes}")
        else:
            print("✅ No duplicate codes found")
        
        if duplicate_names:
            print(f"❌ Duplicate names found: {duplicate_names}")
        else:
            print("✅ No duplicate names found")
        
        # Show room summary
        print("\n📋 Room Summary:")
        room_types = {}
        for space in spaces:
            room_type = space.get('type', 'unknown')
            if room_type not in room_types:
                room_types[room_type] = []
            room_types[room_type].append(f"{space.get('code', 'N/A')} ({space.get('capacity', 0)})")
        
        for room_type, rooms in room_types.items():
            print(f"   {room_type}: {len(rooms)} rooms")
            for room in rooms:
                print(f"     - {room}")
        
        return len(duplicate_codes) == 0 and len(duplicate_names) == 0
        
    except Exception as e:
        print(f"❌ Error verifying fix: {e}")
        return False

def main():
    """Main function"""
    print("🔧 DATASET FIX SCRIPT")
    print("=" * 60)
    
    # Step 1: Create backup
    if not backup_original_file():
        return
    
    # Step 2: Fix duplicates
    if not fix_duplicate_rooms():
        print("❌ Failed to fix duplicate rooms")
        return
    
    # Step 3: Verify fix
    if not verify_fix():
        print("❌ Fix verification failed")
        return
    
    # Step 4: Ask about adding more rooms
    print("\n" + "=" * 60)
    add_rooms = input("🏢 Add more rooms for better scheduling? (y/n): ").lower().strip()
    
    if add_rooms == 'y':
        if add_more_rooms():
            verify_fix()
    
    print("\n" + "=" * 60)
    print("✅ DATASET FIX COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Test the algorithms with fixed data")
    print("2. Run: cd app/algorithms_2 && python Data_Loading.py")
    print("3. Check for any remaining issues")

if __name__ == "__main__":
    main() 