from app.generator.data_collector import *
from deap import base, creator, tools, algorithms
import random
import logging
import os
from datetime import datetime
import logging # Configure logging
def setup_logging():
    # Remove file logging completely - only use console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    logging.info("Genetic Algorithm Execution Started")
    logging.info("-" * 50)
    # Return None instead of a log file path
    return None

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
    logging.info("Loading dataset components...")
    
    days =  get_days()
    logging.info(f"Loaded {len(days)} days")
    
    facilities =  get_spaces()
    logging.info(f"Loaded {len(facilities)} facilities")
    
    modules =  get_modules()
    logging.info(f"Loaded {len(modules)} modules")
    
    periods =  get_periods()
    logging.info(f"Loaded {len(periods)} periods")
    
    students =  get_students()
    logging.info(f"Loaded {len(students)} students")
    
    teachers =  get_teachers()
    logging.info(f"Loaded {len(teachers)} teachers")
    
    years =  get_years()
    logging.info(f"Loaded {len(years)} years")
    
    activities =  get_activities()
    logging.info(f"Loaded {len(activities)} activities")
    
    logging.info("Dataset loading complete")
    logging.info("-" * 50)

def print_first():
    logging.info("Printing first items of each dataset (if available):")
    if days and len(days) > 0:
        logging.info(f"First day: {days[0]}")
    else:
        logging.warning("No days data available")
        
    if facilities and len(facilities) > 0:
        logging.info(f"First facility: {facilities[0]}")
    else:
        logging.warning("No facilities data available")
        
    if modules and len(modules) > 0:
        logging.info(f"First module: {modules[0]}")
    else:
        logging.warning("No modules data available")
        
    if periods and len(periods) > 0:
        logging.info(f"First period: {periods[0]}")
    else:
        logging.warning("No periods data available")
        
    if students and len(students) > 0:
        logging.info(f"First student: {students[0]}")
    else:
        logging.warning("No students data available")
        
    if teachers and len(teachers) > 0:
        logging.info(f"First teacher: {teachers[0]}")
    else:
        logging.warning("No teachers data available")
        
    if years and len(years) > 0:
        logging.info(f"First year: {years[0]}")
    else:
        logging.warning("No years data available")
        
    if activities and len(activities) > 0:
        logging.info(f"First activity: {activities[0]}")
    else:
        logging.warning("No activities data available")

#-1 is equaling a hard
creator.create("FitnessMulti", base.Fitness, weights=(-1.0, -1.0, -1.0, -1.0))
creator.create("Individual", list, fitness=creator.FitnessMulti)
toolbox = base.Toolbox()

def get_num_students_per_activity(activity_code):
    logging.debug(f"Getting student count for activity: {activity_code}")
    module_code = next((activity["subject"] for activity in activities if activity["code"] == activity_code), None)
    if not module_code:
        logging.warning(f"No module found for activity: {activity_code}")
        return 0

    student_count = len([student for student in students if module_code in student["subjects"]])
    logging.debug(f"Activity {activity_code} has {student_count} students")
    return student_count

def generate_individual():
    logging.debug("Generating new individual...")
    individual = []
    
    for idx, activity in enumerate(activities):
        num_of_students = get_num_students_per_activity(activity["code"])
        logging.debug(f"Processing activity {activity['code']} with {num_of_students} students")
        
        suitable_rooms = [x for x in facilities if x["capacity"] >= num_of_students]
        room = random.choice(suitable_rooms)
        logging.debug(f"Selected room {room['code']} with capacity {room['capacity']}")
        
        day = random.choice(days)
        teacher = random.choice(activity["teacher_ids"])
        
        period_start = random.choice(periods[:len(periods) - activity["duration"] - 1])
        period = [period_start]
        for i in range(1, activity["duration"]):
            next_period = periods[periods.index(period_start) + i]
            period.append(next_period)
        
        logging.debug(f"Scheduled: Room={room['code']}, Day={day['name']}, Teacher={teacher}, Periods={[p['name'] for p in period]}")
        
        individual.append({
            "subgroup": activity["subgroup_ids"][0],
            "activity_id": activity["code"],
            "day": day,
            "period": period,
            "room": room,
            "teacher": teacher,
            "duration": activity["duration"],
            "subject": activity["subject"]
        })
        
        activity["periods_assigned"] = activity.get("periods_assigned", []) + period
    
    logging.debug(f"Individual generation complete with {len(individual)} scheduled activities")
    return individual

#register the logic for creating a single individual
toolbox.register("individual", tools.initIterate, creator.Individual, generate_individual)

#registers the logic for creating a population:
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def evaluate(individual):
    logging.debug("Evaluating individual...")
    room_conflicts = 0
    teacher_conflicts = 0
    interval_conflicts = 0
    period_conflicts = 0

    scheduled_activities = {}
    interval_usage = {}

    # Count conflicts
    for schedule in individual:
        key = (schedule["day"]["_id"], schedule["period"][0]["_id"])
        if key not in scheduled_activities:
            scheduled_activities[key] = []
        scheduled_activities[key].append(schedule)
        
        for per in schedule["period"]:
            if per["is_interval"]:
                interval_usage[per["_id"]] = interval_usage.get(per["_id"], 0) + 1

    # Evaluate conflicts
    for key, scheduled in scheduled_activities.items():
        day_id, period_id = key
        logging.debug(f"Checking conflicts for day={day_id}, period={period_id}")
        
        rooms_used = {}
        teachers_involved = []
        periods_used = {}

        for activity in scheduled:
            room = activity["room"]
            if room["code"] in rooms_used:
                rooms_used[room["code"]] += 1
                logging.debug(f"Room conflict detected: {room['code']}")
            else:
                rooms_used[room["code"]] = 1

            teachers_involved.append(activity["teacher"])

            for per in activity["period"]:
                periods_used[per["_id"]] = periods_used.get(per["_id"], 0) + 1

        # Log conflicts
        for room, count in rooms_used.items():
            if count > 1:
                room_conflicts += count - 1
                logging.debug(f"Room {room} has {count} conflicts")

        teacher_conflicts += len(teachers_involved) - len(set(teachers_involved))
        if teacher_conflicts > 0:
            logging.debug(f"Teacher conflicts: {teacher_conflicts}")

    interval_conflicts = sum(interval_usage.values())
    period_conflicts = sum(periods_used.values())

    logging.debug(f"Evaluation complete - Conflicts: Teacher={teacher_conflicts}, Room={room_conflicts}, "
                f"Interval={interval_conflicts}, Period={period_conflicts}")
    
    return teacher_conflicts, room_conflicts, interval_conflicts, period_conflicts

toolbox.register("evaluate", evaluate)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.2)
toolbox.register("select", tools.selNSGA2)

def generate_ga():
    log_filepath = setup_logging()
    logging.info("Starting Genetic Algorithm execution")
    
    get_data()
    print_first()
    
    # Check if we have enough data to proceed
    if (len(days) == 0 or len(facilities) == 0 or len(modules) == 0 or 
        len(periods) == 0 or len(teachers) == 0 or len(activities) == 0):
        logging.error("Insufficient data to generate timetable. Missing required collections.")
        empty_population = []
        empty_logbook = tools.Logbook()
        empty_hof = tools.HallOfFame(1)
        empty_lastpopulation = []
        return empty_population, empty_logbook, empty_hof, empty_lastpopulation
    
    pop_size = 100
    generations = 50
    logging.info(f"GA Parameters: Population={pop_size}, Generations={generations}")

    logging.info("Generating initial population...")
    pop = toolbox.population(n=pop_size)
    hof = tools.HallOfFame(1)

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("teacher_conflicts", lambda fits: min(fit[0] for fit in fits))
    stats.register("room_conflicts", lambda fits: min(fit[1] for fit in fits))
    stats.register("interval_conflicts", lambda fits: min(fit[2] for fit in fits))
    stats.register("period_conflicts", lambda fits: min(fit[3] for fit in fits))

    logging.info("Starting evolution...")
    pop, log = algorithms.eaMuPlusLambda(
        pop,
        toolbox,
        mu=pop_size,
        lambda_=pop_size,
        cxpb=0.7,
        mutpb=0.2,
        ngen=generations,
        stats=stats,
        halloffame=hof,
        verbose=True,
    )

    best_solution = hof[0]
    logging.info("Evolution complete!")
    logging.info(f"Best solution fitness: {best_solution.fitness.values}")
    logging.info(f"Detailed logs available at: {log_filepath}")
    
    # Format the solution in a way that matches the frontend expectations
    formatted_solution = []
    for activity in best_solution:
        if not activity:
            continue
            
        day_obj = activity.get("day", {})
        period_objs = activity.get("period", [])
        room_obj = activity.get("room", {})
        
        formatted_solution.append({
            "activity": activity.get("activity_id", "") or activity.get("activity", ""),
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
            "algorithm": "GA"  # Add algorithm to be consistent
        })
    
    return pop, log, hof, formatted_solution
