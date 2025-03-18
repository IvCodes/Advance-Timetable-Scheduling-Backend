import random
import copy

# Create the schedule dictionary
schedule = {slot: {space: None for space in spaces} for slot in slots}

# Reward function to evaluate schedule quality
def reward(schedule):
    score = 0
    teacher_assignments = {}
    group_assignments = {}

    for slot, space_dict in schedule.items():
        for space, activity in space_dict.items():
            if activity:
                # Reward for valid placement
                score += 10

                # Check for teacher conflicts
                teacher = activity.teacher_id
                if teacher in teacher_assignments and teacher_assignments[teacher] == slot:
                    score -= 20  # Penalize teacher conflict
                else:
                    teacher_assignments[teacher] = slot

                # Check for group conflicts
                for group in activity.group_ids:
                    if group in group_assignments and group_assignments[group] == slot:
                        score -= 15  # Penalize group conflict
                    else:
                        group_assignments[group] = slot

                # Check for student group clashes within the same time slot
                assigned_groups = set()
                for other_space, other_activity in space_dict.items():
                    if other_activity and other_activity != activity:
                        for group in other_activity.group_ids:
                            if group in assigned_groups:
                                score -= 25  # Higher penalty for student group clashes
                            assigned_groups.add(group)

                # Check for room capacity constraints
                total_students = sum(groups_dict[group].size for group in activity.group_ids)
                if total_students > spaces_dict[space].size:
                    score -= 30  # Penalize exceeding room capacity

    return score

# Function to find the best slot for an activity
def find_best_slot(activity, schedule):
    best_slot = None
    best_score = float('-inf')

    for i, slot in enumerate(slots):
        for space in spaces:
            if all(schedule.get(slots[j], {}).get(space) is None for j in range(i, min(i + activity.duration, len(slots)))):
                temp_schedule = copy.deepcopy(schedule)
                for j in range(i, min(i + activity.duration, len(slots))):
                    temp_schedule[slots[j]][space] = activity
                temp_score = reward(temp_schedule)
                if temp_score > best_score:
                    best_slot = (i, space)
                    best_score = temp_score

    return best_slot

# Make a copy of the activities dictionary
activities_copy = copy.deepcopy(activities_dict)

# Assign activities strategically
activity_list = sorted(activities_copy.values(), key=lambda x: x.duration, reverse=True)

for activity in activity_list:
    best_slot = find_best_slot(activity, schedule)
    if best_slot:
        slot_index, space = best_slot
        for j in range(slot_index, min(slot_index + activity.duration, len(slots))):
            schedule[slots[j]][space] = activity
        del activities_copy[activity.id]  # Remove assigned activity from the copy

# Print the final schedule and its reward score
from pprint import pprint
#pprint(schedule)
#print("Schedule Reward Score:", reward(schedule))