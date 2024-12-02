import numpy as np
import random
from deap import base, creator, tools, algorithms

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

creator.create("FitnessMulti", base.Fitness, weights=(-1.0, -1.0, -1.0)) 
creator.create("Individual", list, fitness=creator.FitnessMulti)

toolbox = base.Toolbox()

def generate_individual():
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

toolbox.register("individual", tools.initRepeat, creator.Individual, generate_individual, n=20) 
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def evaluate(individual):
    teacher_conflicts, room_conflicts, student_conflicts = 0, 0, 0
    schedule = {}

    for session in individual:
        day, selected_periods, facility, module, teacher = session
        teacher_data = next((t for t in teachers_data if t["name"] == teacher), None)
        
        if teacher_data is None:
            return 1000, 1000, 1000

        if day not in teacher_data["available_days"]:
            teacher_conflicts += 1

        for period in selected_periods:
            if (day, period, facility) in schedule:
                room_conflicts += 1
            else:
                schedule[(day, period, facility)] = session 

            students_in_module = [s["id"] for s in students_data if module in s["modules"]]
            for student in students_in_module:
                if (day, period, student) in schedule:
                    student_conflicts += 1
                else:
                    schedule[(day, period, student)] = session 

    return teacher_conflicts, room_conflicts, student_conflicts


toolbox.register("evaluate", evaluate)

toolbox.register("mate", tools.cxTwoPoint) 
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.1) 
toolbox.register("select", tools.selNSGA2)

def main():
    print("Running genetic algorithm...")
    print(generate_individual())
    random.seed(42)
    population = toolbox.population(n=100) 
    ngen = 50 
    cxpb = 0.7 
    mutpb = 0.2 

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean, axis=0)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)

    algorithms.eaMuPlusLambda(population, toolbox, mu=100, lambda_=200, cxpb=cxpb, mutpb=mutpb, ngen=ngen, stats=stats, verbose=True)
    
    best_individual = tools.selBest(population, 1)[0]
    print("Best individual:", best_individual)
    print("Fitness values:", best_individual.fitness.values)

    timetable_dict = [
        {
            "Day": entry[0],
            "Time": entry[1],
            "Room": entry[2],
            "Course": entry[3],
            "Lecturer": entry[4]
        }
        for entry in best_individual
    ]

    with open('timetable.json', 'w') as json_file:
        json.dump(timetable_dict, json_file, indent=4)

if __name__ == "__main__":
    main()
