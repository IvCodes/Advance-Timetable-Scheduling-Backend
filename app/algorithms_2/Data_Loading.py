import os
import json


class Space:
    def __init__(self, *args):
        self.code = args[0]
        self.size = args[1]

    def __repr__(self):
        return f"Space(code={self.code}, size={self.size})"


class Group:
    def __init__(self, *args):
        self.id = args[0]
        self.size = args[1]

    def __repr__(self):
        return f"Group(id={self.id}, size={self.size})"


class Activity:
    def __init__(self, id, *args):
        self.id = id
        self.subject = args[0]
        self.teacher_id = args[1]
        self.group_ids = args[2]
        self.duration = args[3]

    def __repr__(self):
        return f"Activity(id={self.id}, subject={self.subject}, teacher_id={self.teacher_id}, group_ids={self.group_ids}, duration={self.duration})"


class Period:
    def __init__(self, *args):
        self.space = args[0]
        self.slot = args[1]
        self.activity = args[2]

    def __repr__(self):
        return f"Period(space={self.space}, group={self.group}, activity={self.activity})"


class Lecturer:
    def __init__(self, id, first_name, last_name, username, department):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.department = department

    def __repr__(self):
        return f"Lecturer(id={self.id}, name={self.first_name} {self.last_name}, department={self.department})"


# Get the directory where this file is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load data from JSON file using absolute path
dataset_path = os.path.join(current_dir, 'sliit_computing_dataset.json')
with open(dataset_path, 'r') as file:
    data = json.load(file)

# Create dictionaries to store instances
spaces_dict = {}
groups_dict = {}
activities_dict = {}
lecturers_dict = {}
slots = []
# Populate the dictionaries with data from the JSON file
for space in data['spaces']:
    spaces_dict[space['code']] = Space(space['code'], space['capacity'])

for group in data['years']:
    groups_dict[group['id']] = Group(group['id'], group['size'])

for activity in data['activities']:
    activities_dict[activity['code']] = Activity(
        activity['code'], activity['subject'], activity['teacher_ids'][0], activity['subgroup_ids'], activity['duration'])

for user in data["users"]:
    if user["role"] == "lecturer":
        lecturers_dict[user["id"]] = Lecturer(
            user["id"], user["first_name"], user["last_name"], user["username"], user["department"]
        )

for day in ["MON", "TUE", "WED", "THU", "FRI"]:
    for id in range(1, 9):
        slots.append(day+str(id))
# Print the dictionaries to verify
print("spaces_dict=", spaces_dict)
print("groups_dict=", groups_dict)
print("activities_dict=", activities_dict)
print("lecturers_dict=", lecturers_dict)
print("slots=", slots)


class Period:
    def __init__(self, space, slot, activity=None):
        self.space = space
        self.slot = slot
        self.activity = activity

    def __repr__(self):
        return f"Period(space={self.space}, slot={self.slot}, activity={self.activity})"


# Use either the hardcoded spaces or load from the dataset:
# Uncomment the next line to use all spaces from your dataset:
spaces = list(spaces_dict.keys())

# Otherwise, if you want to use only a subset (e.g., 4 spaces), you can leave it as is:
# spaces = ['LH401', 'LH501', 'LAB501', 'LAB502']

# Build a schedule dictionary: for each slot, create a sub-dictionary for each space (initially None)
schedule = {slot: {space: None for space in spaces} for slot in slots}

# (Optional) Print the schedule to verify its structure
for slot in sorted(schedule.keys()):
    print(f"{slot}: {schedule[slot]}")
