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
    # Get non-interval periods count
    non_interval_periods = [x for x in periods if not x.get("is_interval", False)]
    max_teachers_per_activity = max(len(activity["teacher_ids"]) for activity in activities) if activities else 1
    
    pheromone = {
        "room": np.ones((len(activities), len(facilities))),
        "day": np.ones((len(activities), len(days))),
        "period": np.ones((len(activities), len(non_interval_periods))),
        "teacher": np.ones((len(activities), max_teachers_per_activity)),
    }
    return pheromone

def calculate_heuristic(activity, num_of_students):
    room_scores = [
        1.0 / (abs(room["capacity"] - num_of_students) + 1) if room["capacity"] >= num_of_students else 0
        for room in facilities
    ]
    # Teacher scores should only be for teachers assigned to this activity
    teacher_scores = [1.0 for _ in activity["teacher_ids"]]
    # Only consider non-interval periods
    non_interval_periods = [x for x in periods if not x.get("is_interval", False)]
    period_scores = [1.0 for _ in non_interval_periods]
    day_scores = [1.0 for _ in days]

    return {
        "room": np.array(room_scores),
        "day": np.array(day_scores),
        "period": np.array(period_scores),
        "teacher": np.array(teacher_scores),
    }

def construct_solution(pheromone, heuristics):
    individual = []
    non_interval_periods = [x for x in periods if not x.get("is_interval", False)]
    
    for i, activity in enumerate(activities):
        num_of_students = get_num_students_per_activity(activity["code"])
        heuristic = heuristics[i]
        
        # Calculate probabilities
        room_probs = (pheromone["room"][i] ** ALPHA) * (heuristic["room"] ** BETA)
        day_probs = (pheromone["day"][i] ** ALPHA) * (heuristic["day"] ** BETA)
        period_probs = (pheromone["period"][i] ** ALPHA) * (heuristic["period"] ** BETA)
        
        # Teacher probabilities - only for teachers assigned to this activity
        teacher_pheromone = pheromone["teacher"][i][:len(activity["teacher_ids"])]
        teacher_probs = (teacher_pheromone ** ALPHA) * (heuristic["teacher"] ** BETA)

        # Normalize probabilities
        room_probs /= room_probs.sum()
        day_probs /= day_probs.sum()
        period_probs /= period_probs.sum()
        teacher_probs /= teacher_probs.sum()

        # Make selections
        room = facilities[np.random.choice(len(facilities), p=room_probs)]
        day = days[np.random.choice(len(days), p=day_probs)]
        period_start = non_interval_periods[np.random.choice(len(non_interval_periods), p=period_probs)]
        
        # Select teacher from activity's assigned teachers
        teacher_idx = np.random.choice(len(activity["teacher_ids"]), p=teacher_probs)
        teacher = activity["teacher_ids"][teacher_idx]

        # Build consecutive periods for multi-period activities
        period = [period_start]
        period_start_index = non_interval_periods.index(period_start)
        for j in range(1, activity["duration"]):
            next_period_index = period_start_index + j
            if next_period_index < len(non_interval_periods):
                period.append(non_interval_periods[next_period_index])
            else:
                break  # Can't schedule full duration

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

    # Group activities by time slot for room and teacher conflict checking
    scheduled_activities = {}
    for schedule in individual:
        key = (schedule["day"]["_id"], schedule["period"][0]["_id"])
        if key not in scheduled_activities:
            scheduled_activities[key] = []
        scheduled_activities[key].append(schedule)

    # Check room and teacher conflicts (these apply across all subgroups)
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

    # Check period conflicts within same subgroup only
    subgroup_period_assignments = {}
    for schedule in individual:
        subgroup = schedule["subgroup"]
        for per in schedule["period"]:
            key = (subgroup, schedule["day"]["_id"], per["_id"])
            if key not in subgroup_period_assignments:
                subgroup_period_assignments[key] = []
            subgroup_period_assignments[key].append(schedule["activity_id"])
    
    period_conflicts = 0
    for key, activities in subgroup_period_assignments.items():
        if len(activities) > 1:
            period_conflicts += len(activities) - 1

    return teacher_conflicts, room_conflicts, period_conflicts

def update_pheromone(pheromone, solutions, scores):
    non_interval_periods = [x for x in periods if not x.get("is_interval", False)]
    
    for i, (solution, (teacher_conflicts, room_conflicts, period_conflicts)) in enumerate(zip(solutions, scores)):
        total_conflicts = teacher_conflicts + room_conflicts + period_conflicts
        for j, activity in enumerate(solution):
            # Update room pheromone
            room_idx = facilities.index(activity["room"])
            pheromone["room"][j][room_idx] += Q / (1 + total_conflicts)
            
            # Update day pheromone
            day_idx = days.index(activity["day"])
            pheromone["day"][j][day_idx] += Q / (1 + total_conflicts)
            
            # Update period pheromone (only for non-interval periods)
            period_idx = non_interval_periods.index(activity["period"][0])
            pheromone["period"][j][period_idx] += Q / (1 + total_conflicts)
            
            # Update teacher pheromone (find teacher index in activity's teacher list)
            activity_obj = activities[j]
            if activity["teacher"] in activity_obj["teacher_ids"]:
                teacher_idx = activity_obj["teacher_ids"].index(activity["teacher"])
                if teacher_idx < pheromone["teacher"].shape[1]:
                    pheromone["teacher"][j][teacher_idx] += Q / (1 + total_conflicts)

    # Evaporate pheromone
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
