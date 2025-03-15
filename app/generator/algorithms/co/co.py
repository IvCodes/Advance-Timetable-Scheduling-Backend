from app.generator.data_collector import *
import random
import numpy as np

days = []
facilities = []
modules = []
periods = []
students = []
teachers = []
years = []
activities = []
amount_of_intervals = 0
def get_data():
    global days, facilities, modules, periods, students, teachers, years, activities, amount_of_intervals
    days =  get_days()
    facilities =  get_spaces()
    modules =  get_modules()
    periods =  get_periods()
    students =  get_students()
    teachers =  get_teachers()
    years =  get_years()
    activities =  get_activities()
    amount_of_intervals =     sum([1 for x in periods if x.get("is_interval", False)])


def print_first():
    print(days[0])
    print(facilities[0])
    print(modules[0])
    print(periods[0])
    print(students[0])
    print(teachers[0])
    print(years[0])
    print(activities[0])


NUM_ANTS = 50
NUM_ITERATIONS = 50
ALPHA = 1.0   
BETA = 2.0   
RHO = 0.1    
Q = 10       


def get_num_students_per_activity(activity_code):
    module_code = next((activity["subject"] for activity in activities if activity["code"] == activity_code), None)
    if not module_code:
        return 0

    return len([student for student in students if module_code in student["subjects"]])

def initialize_pheromone():
    amount_of_intervals = sum([1 for x in periods if x.get("is_interval", False)])
    pheromone = {
        "room": np.ones((len(activities), len(facilities))),
        "day": np.ones((len(activities), len(days))),
        "period": np.ones((len(activities), len(periods) - amount_of_intervals)),
        "teacher": np.ones((len(activities), len(teachers))),
    }
    return pheromone

def calculate_heuristic(activity, num_of_students):
    room_scores = [
        1.0 / (abs(room["capacity"] - num_of_students) + 1) if room["capacity"] >= num_of_students else 0
        for room in facilities
    ]
    teacher_scores = [1.0 for teacher in activity["teacher_ids"]]
    period_scores = [1.0 for x in periods if not x.get("is_interval", False)]
    day_scores = [1.0 for _ in days]

    return {
        "room": np.array(room_scores),
        "day": np.array(day_scores),
        "period": np.array(period_scores),
        "teacher": np.array(teacher_scores),
    }

def construct_solution(pheromone, heuristics):
    individual = []
    for i, activity in enumerate(activities):
        num_of_students = get_num_students_per_activity(activity["code"])
        heuristic = heuristics[i]
        print(heuristic["teacher"])
        print(pheromone["teacher"][i])
        room_probs = (pheromone["room"][i] ** ALPHA) * (heuristic["room"] ** BETA)
        day_probs = (pheromone["day"][i] ** ALPHA) * (heuristic["day"] ** BETA)
        period_probs = (pheromone["period"][i] ** ALPHA) * (heuristic["period"] ** BETA)
        teacher_probs = (pheromone["teacher"][i] ** ALPHA) * (heuristic["teacher"] ** BETA)

        room_probs /= room_probs.sum()
        day_probs /= day_probs.sum()
        period_probs /= period_probs.sum()
        teacher_probs /= teacher_probs.sum()

        room = facilities[np.random.choice(len(facilities), p=room_probs)]
        day = days[np.random.choice(len(days), p=day_probs)]
        period_start = periods[np.random.choice(len(periods)-amount_of_intervals, p=period_probs)]
        print(len(activity["teacher_ids"]))
        print(len(teacher_probs))
        teacher = activity["teacher_ids"][np.random.choice(len(teachers), p=teacher_probs)]

        period = [period_start]
        for j in range(1, activity["duration"]):
            next_period_index = periods.index(period_start) + j
            if next_period_index < len(periods):
                period.append(periods[next_period_index])

        individual.append({
            "subgroup": activity["subgroup_ids"][0],
            "activity_id": activity["code"],
            "day": day,
            "period": period,
            "room": room,
            "teacher": teacher,
            "duration": activity["duration"],
            "subject": activity["subject"],
        })

    return individual

def evaluate_solution(individual):
    room_conflicts = 0
    teacher_conflicts = 0

    scheduled_activities = {}
    for schedule in individual:
        key = (schedule["day"]["_id"], schedule["period"][0]["_id"])
        if key not in scheduled_activities:
            scheduled_activities[key] = []
        scheduled_activities[key].append(schedule)

    for key, scheduled in scheduled_activities.items():
        rooms_used = {}
        teachers_involved = []

        for activity in scheduled:
            room = activity["room"]
            if room["code"] in rooms_used:
                rooms_used[room["code"]] += 1
            else:
                rooms_used[room["code"]] = 1

            teachers_involved.append(activity["teacher"])

        for room, count in rooms_used.items():
            if count > 1: 
                room_conflicts += count - 1

        teacher_conflicts += len(teachers_involved) - len(set(teachers_involved))

    return teacher_conflicts, room_conflicts

def update_pheromone(pheromone, solutions, scores):
    for i, (solution, (teacher_conflicts, room_conflicts)) in enumerate(zip(solutions, scores)):
        for j, activity in enumerate(solution):
            pheromone["room"][j][facilities.index(activity["room"])] += Q / (1 + teacher_conflicts + room_conflicts)
            pheromone["day"][j][days.index(activity["day"])] += Q / (1 + teacher_conflicts + room_conflicts)
            pheromone["period"][j][periods.index(activity["period"][0])] += Q / (1 + teacher_conflicts + room_conflicts)
            pheromone["teacher"][j][activity["teacher"]] += Q / (1 + teacher_conflicts + room_conflicts)

    for key in pheromone:
        pheromone[key] *= (1 - RHO)

def generate_co():
    get_data()
    print_first()
    pheromone = initialize_pheromone()
    best_solution = None
    best_score = float("inf")

    for iteration in range(NUM_ITERATIONS):
        heuristics = [calculate_heuristic(activity, get_num_students_per_activity(activity["code"])) for activity in activities]
        solutions = [construct_solution(pheromone, heuristics) for _ in range(NUM_ANTS)]
        scores = [evaluate_solution(solution) for solution in solutions]

        update_pheromone(pheromone, solutions, scores)

        for solution, score in zip(solutions, scores):
            total_score = sum(score)
            if total_score < best_score:
                best_solution = solution
                best_score = total_score

        print(f"Iteration {iteration + 1}/{NUM_ITERATIONS}, Best Score: {best_score}")

    return best_solution
