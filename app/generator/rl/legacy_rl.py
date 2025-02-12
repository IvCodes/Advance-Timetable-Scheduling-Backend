import numpy as np
import random
import json

days_file = "days_per_week.json"
facilities_file = "facilities.json"
modules_file = "modules.json"
periods_file = "periods_per_day.json"
students_file = "students.json"
teachers_file = "teachers.json"

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

days_data = load_json(days_file)
facilities_data = load_json(facilities_file)
modules_data = load_json(modules_file)
periods_data = load_json(periods_file)
students_data = load_json(students_file)
teachers_data = load_json(teachers_file)

states = []
actions = ["assign_time", "assign_room", "assign_teacher"]
q_table = {}

alpha = 0.1 
gamma = 0.9 
epsilon = 0.1

for module in modules_data:
    for day in days_data:
        for period in periods_data:
            for facility in facilities_data['lecture_halls'] + facilities_data['computer_labs']:
                state = (module["id"], day["name"], period["name"], facility["code"])
                q_table[state] = {action: 0 for action in actions}


def calculate_reward(state, teacher_conflict, room_conflict, student_conflict):
    penalty = teacher_conflict * 10 + room_conflict * 5 + student_conflict * 2
    return 100 - penalty


def choose_action(state):
    if random.uniform(0, 1) < epsilon:
        return random.choice(actions)
    else:
        return max(q_table[state], key=q_table[state].get)


def evaluate_schedule(day, period, facility, module, teacher):
    teacher_conflict, room_conflict, student_conflict = 0, 0, 0
    schedule = {}


    teacher_data = next((t for t in teachers_data if t["name"] == teacher), None)
    if teacher_data and day not in teacher_data["available_days"]:
        teacher_conflict += 1


    students_in_module = [s["id"] for s in students_data if module in s["modules"]]


    day_name = day if isinstance(day, str) else day.get("name")
    period_name = str(period) if isinstance(period, int) else period.get("name")
    facility_code = facility if isinstance(facility, str) else facility.get("code")

    if (day_name, period_name, facility_code) in schedule:
        room_conflict += 1
    else:
        schedule[(day_name, period_name, facility_code)] = (module, teacher)
    

    for student in students_in_module:
        if (day_name, period_name, student) in schedule:
            student_conflict += 1
        else:
            schedule[(day_name, period_name, student)] = (module, teacher)

    return teacher_conflict, room_conflict, student_conflict

for episode in range(500):
    total_reward = 0
    for module in modules_data:
        for day in days_data:
            for period in periods_data:
                for facility in facilities_data['lecture_halls'] + facilities_data['computer_labs']:
                    state = (module["id"], day["name"], period if isinstance(period, int) else period["name"], facility["code"])
                    action = choose_action(state)
                    teacher = "NoTeacher"
                    if action == "assign_teacher":
                        available_teachers = [t["name"] for t in teachers_data if module["id"] in t["sessions"]]
                        teacher = random.choice(available_teachers) if available_teachers else "NoTeacher"
                    elif action == "assign_time":
                        period = random.choice([p["name"] for p in periods_data])
                    elif action == "assign_room":
                        facility = random.choice(facilities_data['lecture_halls'] + facilities_data['computer_labs'])['code']

                    teacher_conflict, room_conflict, student_conflict = evaluate_schedule(day["name"], period, facility, module["id"], teacher)
                    reward = calculate_reward(state, teacher_conflict, room_conflict, student_conflict)
                    total_reward += reward

                    best_future_action = max(q_table[state], key=q_table[state].get)
                    q_table[state][action] += alpha * (reward + gamma * q_table[state][best_future_action] - q_table[state][action])

    if episode % 50 == 0:
        print(f"Episode {episode} - Total Reward: {total_reward}")

def generate_timetable():
    timetable = []
    for module in modules_data:
        for day in days_data:
            for period in periods_data:
                for facility in facilities_data['lecture_halls'] + facilities_data['computer_labs']:
                    state = (module["id"], day["name"], period["name"], facility["code"])
                    action = max(q_table[state], key=q_table[state].get)
                    teacher = next((t["name"] for t in teachers_data if module["id"] in t["sessions"]), "NoTeacher")
                    timetable.append({
                        "Day": day["name"],
                        "Time": period["name"],
                        "Room": facility,
                        "Course": module["id"],
                        "Lecturer": teacher
                    })
    return timetable

timetable = generate_timetable()
with open('timetable.json', 'w') as json_file:
    json.dump(timetable, json_file, indent=4)
    
print("Timetable generated and saved to timetable.json")
