import random
import numpy as np
from collections import defaultdict
from app.generator.data_collector import *

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
        num_students = get_num_students_per_activity(activity.get("code", ""))
        
        valid_rooms = [room for room in facilities if room.get("capacity", 0) >= num_students]
        if not valid_rooms:
            continue
        room = random.choice(valid_rooms)
        
        day = random.choice(days) if days else {}
        
        teacher_ids = activity.get("teacher_ids", [])
        teacher = random.choice(teacher_ids) if teacher_ids else ""
        
        period_indices = {period.get("name", ""): idx for idx, period in enumerate(periods)}

        valid_periods = []
        duration = activity.get("duration", 1)
        
        if len(periods) > duration:
            valid_periods = [
                period for period in periods[:len(periods) - duration - 1]
                if all(p not in used_periods for p in 
                       range(period_indices.get(period.get("name", ""), 0), 
                            period_indices.get(period.get("name", ""), 0) + duration))
            ]
        
        if not valid_periods:
            continue
        start_period = random.choice(valid_periods)
        
        assigned_periods = [start_period]
        start_idx = periods.index(start_period) if start_period in periods else 0
        
        for i in range(1, duration):
            if start_idx + i < len(periods):
                assigned_periods.append(periods[start_idx + i])
        
        subgroup_ids = activity.get("subgroup_ids", [])
        solution.append({
            "subgroup": subgroup_ids[0] if subgroup_ids else "",
            "activity_id": activity.get("code", ""),
            "day": day,
            "period": assigned_periods,
            "room": room,
            "teacher": teacher,
            "duration": duration,
            "subject": activity.get("subject", "")
        })
        
        used_periods.update([p.get("_id", "") for p in assigned_periods])
    
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

    formatted_solution = []
    for activity in best_solution:
        if not activity:
            continue
            
        day_obj = activity.get("day", {})
        period_objs = activity.get("period", [])
        room_obj = activity.get("room", {})
        
        formatted_solution.append({
            "activity": activity.get("activity_id", ""),
            "day": {
                "name": day_obj.get("name", ""),
                "code": day_obj.get("code", ""),
                "order": day_obj.get("order", 0),
                "long_name": day_obj.get("long_name", "")
            },
            "period": [{
                "name": p.get("name", ""),
                "start_time": p.get("start_time", ""),
                "end_time": p.get("end_time", ""),
                "order": p.get("order", 0),
                "long_name": p.get("long_name", ""),
                "is_interval": p.get("is_interval", False)
            } for p in period_objs] if period_objs else [],
            "room": {
                "name": room_obj.get("name", ""),
                "code": room_obj.get("code", ""),
                "capacity": room_obj.get("capacity", 0),
                "type": room_obj.get("type", "classroom")
            },
            "teacher": activity.get("teacher", ""),
            "subgroup": activity.get("subgroup", ""),
            "subject": activity.get("subject", ""),
            "duration": activity.get("duration", 1),
            "algorithm": "CO"  
        })

    return formatted_solution
