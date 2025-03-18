import json
import os

def analyze_dataset(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Check activities
    activities = data.get('activities', [])
    print(f"Total activities: {len(activities)}")
    
    # Check room sizes vs activities
    spaces = data.get('spaces', [])
    print(f"Total spaces: {len(spaces)}")
    
    # Validate if activities can fit in rooms
    room_capacities = {space['code']: space.get('capacity', 0) for space in spaces}
    
    years = data.get('years', [])
    groups = {}
    for year in years:
        for group in year.get('groups', []):
            groups[group['id']] = group.get('size', 0)
    
    activity_sizes = {}
    for activity in activities:
        activity_id = activity['code']
        total_size = 0
        for group_id in activity.get('group_ids', []):
            total_size += groups.get(group_id, 0)
        activity_sizes[activity_id] = total_size
    
    # Count activities that can fit in at least one room
    valid_activities = 0
    for activity_id, size in activity_sizes.items():
        if any(capacity >= size for capacity in room_capacities.values()):
            valid_activities += 1
    
    print(f"Activities that can fit in at least one room: {valid_activities} / {len(activities)}")
    
    # Check for any inconsistencies
    if valid_activities < len(activities):
        print("WARNING: Some activities cannot fit in any available room!")
        
        # List problematic activities
        for activity_id, size in activity_sizes.items():
            if not any(capacity >= size for capacity in room_capacities.values()):
                activity_name = next((a['name'] for a in activities if a['code'] == activity_id), 'Unknown')
                print(f"  - Activity {activity_id} ({activity_name}) requires size {size}, but largest room is {max(room_capacities.values())}")

# Get the directory where this file is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define path to dataset using relative path from current directory
dataset_path = os.path.join(current_dir, "sliit_computing_dataset.json")

# Run the analysis
analyze_dataset(dataset_path)