import random
import numpy as np
from collections import defaultdict
from generator.data_collector import *

NUM_ANTS = 50
NUM_ITERATIONS = 60
EVAPORATION_RATE = 0.5
ALPHA = 1 
BETA = 2  
Q = 100   

days = []
facilities = []
modules = []
periods = []
students = []
teachers = []
years = []
activities = []

def get_data():
    globle
    global days, facilities, modules, periods, students, teachers, years, activities
    days = get_days()
    facilities = get_spaces()
    modules = get_modules()
    periods = get_periods()
    students = get_students()
    teachers = get_teachers()
    years = get_years()
    activities = get_activities()

def get_num_students_per_activity(activity_code):
    module_code = next((activity["subject"] for activity in activities if activity["code"] == activity_code), None)
    if not module_code:
        return 0
    return len([student for student in students if module_code in student["subjects"]])

pheromone = defaultdict(lambda: 1.0) 
heuristic = defaultdict(float)      

def initialize_heuristic():
    global heuristic
    for activity in activities:
        num_students = get_num_students_per_activity(activity["code"])
        heuristic[activity["code"]] = 1 / (1 + num_students) 

def construct_solution():
    solution = []
    used_periods = set()
    
    for activity in activities:
        num_students = get_num_students_per_activity(activity["code"])
        
        valid_rooms = [room for room in facilities if room["capacity"] >= num_students]
        if not valid_rooms:
            continue
        room = random.choice(valid_rooms)
        
        day = random.choice(days)
        
        teacher = random.choice(activity["teacher_ids"])
        
        period_indices = {period["name"]: idx for idx, period in enumerate(periods)}

        valid_periods = [
            period for period in periods[:len(periods) - activity["duration"] - 1]
            if all(p not in used_periods for p in range(period_indices[period["name"]], period_indices[period["name"]] + activity["duration"]))
        ]

        if not valid_periods:
            continue
        start_period = random.choice(valid_periods)
        
        assigned_periods = [start_period]
        for i in range(1, activity["duration"]):
            assigned_periods.append(periods[periods.index(start_period) + i])
        
        solution.append({
            "subgroup": activity["subgroup_ids"][0],
            "activity_id": activity["code"],
            "day": day,
            "period": assigned_periods,
            "room": room,
            "teacher": teacher,
            "duration": activity["duration"],
            "subject": activity["subject"]
        })
        
        used_periods.update([p["_id"] for p in assigned_periods])
    
    return solution

def evaluate_solution(solution):
    room_conflicts = 0
    teacher_conflicts = 0
    interval_conflicts = 0
    period_conflicts = 0

    scheduled_activities = defaultdict(list)
    interval_usage = defaultdict(int)

    for schedule in solution:
        key = (schedule["day"]["_id"], schedule["period"][0]["_id"])
        scheduled_activities[key].append(schedule)
        for period in schedule["period"]:
            if period["is_interval"]:
                interval_usage[period["_id"]] += 1

    for scheduled in scheduled_activities.values():
        rooms_used = defaultdict(int)
        teachers_involved = set()
        periods_used = defaultdict(int)

        for activity in scheduled:
            rooms_used[activity["room"]["code"]] += 1
            teachers_involved.add(activity["teacher"])
            for period in activity["period"]:
                periods_used[period["_id"]] += 1

        room_conflicts += sum(count - 1 for count in rooms_used.values() if count > 1)
        teacher_conflicts += len(teachers_involved) - len(set(teachers_involved))

    interval_conflicts = sum(interval_usage.values())
    period_conflicts = sum(periods_used.values())

    return teacher_conflicts, room_conflicts, interval_conflicts, period_conflicts

def update_pheromone(all_solutions, best_solution):
    global pheromone
    for activity_code in pheromone:
        pheromone[activity_code] *= (1 - EVAPORATION_RATE) 

    for schedule in best_solution:
        pheromone[schedule["activity_id"]] += Q / (1 + sum(evaluate_solution(best_solution)))

def generate_co():
    get_data()
    initialize_heuristic()
    
    best_solution = None
    best_score = float('inf')

    for iteration in range(NUM_ITERATIONS):
        all_solutions = []
        
        for ant in range(NUM_ANTS):
            solution = construct_solution()
            fitness = evaluate_solution(solution)
            all_solutions.append((solution, fitness))

            if sum(fitness) < best_score:
                best_solution = solution
                best_score = sum(fitness)

        update_pheromone([sol[0] for sol in all_solutions], best_solution)
        print(f"Iteration {iteration + 1}: Best Score = {best_score}")

    return best_solution

