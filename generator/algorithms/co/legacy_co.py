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

num_ants = 100
num_iterations = 50
alpha = 1.0 
beta = 2.0 
evaporation_rate = 0.5
pheromone_init = 1.0

pheromone = {}

def generate_schedule():
    day = random.choice(days_data)['name']
    module = random.choice(modules_data)
    duration = module.get('duration', 1)

    available_periods = [period['name'] for period in periods_data]
    if len(available_periods) < duration:
        return [random.choice(periods_data)]

    start_index = random.randint(0, len(available_periods) - duration)
    selected_periods = available_periods[start_index:start_index + duration]
    facility = random.choice(facilities_data['lecture_halls'] + facilities_data['computer_labs'])['code']

    available_teachers = [t for t in teachers_data if module["id"] in t["sessions"]]
    if available_teachers:
        teacher = random.choice(available_teachers)["name"]
    else:
        teacher = "NoTeacher"

    return [day, selected_periods, facility, module["id"], teacher]

def evaluate_schedule(schedule):
    teacher_conflicts, room_conflicts, student_conflicts = 0, 0, 0
    time_table = {}

    for entry in schedule:
        day, selected_periods, facility, module, teacher = entry
        teacher_data = next((t for t in teachers_data if t["name"] == teacher), None)

        if teacher_data is None:
            return 1000, 1000, 1000

        if day not in teacher_data["available_days"]:
            teacher_conflicts += 1

        for period in selected_periods:
            if (day, period, facility) in time_table:
                room_conflicts += 1
            else:
                time_table[(day, period, facility)] = entry

            students_in_module = [s["id"] for s in students_data if module in s["modules"]]
            for student in students_in_module:
                if (day, period, student) in time_table:
                    student_conflicts += 1
                else:
                    time_table[(day, period, student)] = entry

    return teacher_conflicts, room_conflicts, student_conflicts

def make_hashable(obj):
    if isinstance(obj, list):
        return tuple(make_hashable(item) for item in obj)
    return obj

def calculate_probabilities(choices, pheromone, alpha, beta):
    total = sum((pheromone.get(make_hashable(choice), pheromone_init) ** alpha) * (1.0 ** beta) for choice in choices)
    
    probabilities = [
        ((pheromone.get(make_hashable(choice), pheromone_init) ** alpha) * (1.0 ** beta)) / total
        for choice in choices
    ]
    
    return probabilities

def construct_solution():
    schedule = []
    for _ in range(20): 
        entry = generate_schedule()
        choices = [entry]  
        probabilities = calculate_probabilities(choices, pheromone, alpha, beta)
        schedule.append(random.choices(choices, probabilities)[0])
    return schedule

def aco_optimization():
    global pheromone
    best_schedule = None
    best_fitness = (float('inf'), float('inf'), float('inf'))

    for iteration in range(num_iterations):
        print(f"Iteration {iteration+1}/{num_iterations}")

        ants = [construct_solution() for _ in range(num_ants)]
        fitnesses = [evaluate_schedule(ant) for ant in ants]

        for ant, fitness in zip(ants, fitnesses):
            if fitness < best_fitness:
                best_schedule = ant
                best_fitness = fitness

        pheromone = {key: (1 - evaporation_rate) * value for key, value in pheromone.items()}

        for ant, fitness in zip(ants, fitnesses):
            for entry in ant:
                day, selected_periods, facility, module, teacher = entry
                for period in selected_periods:
                    key = (day, period, facility)
                    pheromone[key] = pheromone.get(key, pheromone_init) + 1.0 / sum(fitness)

    print("Best schedule found:", best_schedule)
    print("Best fitness values:", best_fitness)

    timetable_dict = [
        {
            "Day": entry[0],
            "Time": entry[1],
            "Room": entry[2],
            "Course": entry[3],
            "Lecturer": entry[4]
        }
        for entry in best_schedule
    ]

    with open('timetable.json', 'w') as json_file:
        json.dump(timetable_dict, json_file, indent=4)

if __name__ == "__main__":
    aco_optimization()
