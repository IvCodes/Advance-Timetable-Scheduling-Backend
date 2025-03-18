import json
import os

# Get the directory where this file is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load data from JSON file using absolute path
dataset_path = os.path.join(current_dir, 'sliit_computing_dataset.json')
with open(dataset_path, 'r') as file:
    data = json.load(file)

# Calculate basic statistics
total_activities = len(data["activities"])
total_rooms = len(data["spaces"])
slots_per_week = 5 * 8  # 5 days, 8 slots per day
total_duration = sum(act['duration'] for act in data["activities"])

# Calculate minimum rooms needed theoretically
min_rooms_theoretical = total_duration // slots_per_week
if total_duration % slots_per_week > 0:
    min_rooms_theoretical += 1

# Count room occupancy requirements by capacity
required_capacities = {}
for activity in data["activities"]:
    # Calculate total students for this activity
    total_students = 0
    for group_id in activity["subgroup_ids"]:
        for year in data["years"]:
            if year["id"] == group_id:
                total_students += year["size"]
                break
    
    # Track required room sizes
    size_category = (total_students // 50) * 50  # Group by 50s
    required_capacities[size_category] = required_capacities.get(size_category, 0) + activity["duration"]

# Analyze room distribution by capacity
room_capacities = {}
for room in data["spaces"]:
    capacity = room["capacity"]
    size_category = (capacity // 50) * 50  # Group by 50s
    room_capacities[size_category] = room_capacities.get(size_category, 0) + 1

# Print analysis results
print("===== DATASET ANALYSIS =====")
print(f"Total activities: {total_activities}")
print(f"Total activity duration units: {total_duration}")
print(f"Total time slots: {slots_per_week}")
print(f"Current total rooms: {total_rooms}")
print(f"Minimum theoretical rooms needed: {min_rooms_theoretical}")
print("\n=== ROOM CAPACITY DISTRIBUTION ===")
for capacity, count in sorted(room_capacities.items()):
    print(f"Rooms with ~{capacity} capacity: {count}")

print("\n=== REQUIRED CAPACITY DISTRIBUTION ===")
total_required_slots = 0
for capacity, slots_needed in sorted(required_capacities.items()):
    print(f"Activities needing ~{capacity} capacity: {slots_needed} slot-hours")
    total_required_slots += slots_needed

# Calculate the optimal room distribution
print("\n=== RECOMMENDED ROOM OPTIMIZATION ===")
# For practical scheduling with constraints, add a buffer to the theoretical minimum
practical_buffer = 1.2  # 20% buffer for constraints
optimal_total_rooms = int(min_rooms_theoretical * practical_buffer)

print(f"Recommended total rooms: {optimal_total_rooms} (down from {total_rooms})")

# Calculate a recommended distribution based on activity requirements
print("\n=== RECOMMENDED ROOM DISTRIBUTION ===")
total_slots = slots_per_week * optimal_total_rooms
remaining_slots = total_slots

recommended_rooms = {}
for capacity, slots_needed in sorted(required_capacities.items(), reverse=True):
    # Allocate proportionally, but ensure at least 1 room of each needed capacity
    proportion = slots_needed / total_required_slots
    allocated_rooms = max(1, int(optimal_total_rooms * proportion))
    
    if capacity in recommended_rooms:
        recommended_rooms[capacity] += allocated_rooms
    else:
        recommended_rooms[capacity] = allocated_rooms
        
    remaining_slots -= allocated_rooms * slots_per_week

# Adjust for any remaining capacity
if sum(recommended_rooms.values()) < optimal_total_rooms:
    # Add the remaining to the most common capacity
    most_common_capacity = max(required_capacities.items(), key=lambda x: x[1])[0]
    recommended_rooms[most_common_capacity] += (optimal_total_rooms - sum(recommended_rooms.values()))

# Print recommendations
for capacity, count in sorted(recommended_rooms.items()):
    print(f"Rooms with ~{capacity} capacity: {count}")

print(f"\nTotal recommended rooms: {sum(recommended_rooms.values())}")
