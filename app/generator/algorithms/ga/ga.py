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
    
    # Get non-interval periods only
    non_interval_periods = [p for p in periods if not p.get("is_interval", False)]
    logging.debug(f"Available non-interval periods: {len(non_interval_periods)} out of {len(periods)} total periods")
    
    # Track occupied time slots per subgroup to avoid conflicts
    subgroup_schedules = {}
    
    for idx, activity in enumerate(activities):
        num_of_students = get_num_students_per_activity(activity["code"])
        logging.debug(f"Processing activity {activity['code']} with {num_of_students} students")
        
        subgroup = activity["subgroup_ids"][0]
        if subgroup not in subgroup_schedules:
            subgroup_schedules[subgroup] = set()
        
        suitable_rooms = [x for x in facilities if x["capacity"] >= num_of_students]
        if not suitable_rooms:
            # If no suitable rooms, use the largest available room
            suitable_rooms = [max(facilities, key=lambda x: x["capacity"])]
            logging.warning(f"No suitable room for {num_of_students} students, using largest room")
        
        room = random.choice(suitable_rooms)
        teacher = random.choice(activity["teacher_ids"])
        
        # Find a conflict-free time slot for this subgroup
        max_attempts = 50  # Prevent infinite loops
        attempt = 0
        scheduled = False
        
        while attempt < max_attempts and not scheduled:
            day = random.choice(days)
            
            # Only select from non-interval periods and ensure we have enough consecutive periods
            max_start_index = len(non_interval_periods) - activity["duration"]
            if max_start_index < 0:
                logging.error(f"Activity {activity['code']} duration {activity['duration']} exceeds available periods")
                max_start_index = 0
            
            period_start_index = random.randint(0, max_start_index)
            period_start = non_interval_periods[period_start_index]
            
            # Build consecutive periods for the activity duration
            period = [period_start]
            for i in range(1, activity["duration"]):
                next_index = period_start_index + i
                if next_index < len(non_interval_periods):
                    period.append(non_interval_periods[next_index])
                else:
                    logging.warning(f"Cannot schedule full duration for activity {activity['code']}")
                    break
            
            # Check for conflicts with existing activities in this subgroup
            conflict_found = False
            for p in period:
                time_slot = (day["_id"], p["_id"])
                if time_slot in subgroup_schedules[subgroup]:
                    conflict_found = True
                    break
            
            if not conflict_found:
                # No conflict, schedule the activity
                for p in period:
                    time_slot = (day["_id"], p["_id"])
                    subgroup_schedules[subgroup].add(time_slot)
                
                logging.debug(f"Scheduled: Room={room['code']}, Day={day['name']}, Teacher={teacher}, Periods={[p['name'] for p in period]}")
                
                individual.append({
                    "subgroup": subgroup,
                    "activity_id": activity["code"],
                    "day": day,
                    "period": period,
                    "room": room,
                    "teacher": teacher,
                    "duration": activity["duration"],
                    "subject": activity["subject"]
                })
                
                scheduled = True
            else:
                attempt += 1
                logging.debug(f"Conflict found for {activity['code']}, attempt {attempt}")
        
        if not scheduled:
            # Fallback: schedule anyway but log the issue
            logging.warning(f"Could not find conflict-free slot for {activity['code']}, scheduling with potential conflict")
            day = random.choice(days)
            max_start_index = len(non_interval_periods) - activity["duration"]
            if max_start_index < 0:
                max_start_index = 0
            period_start_index = random.randint(0, max_start_index)
            period_start = non_interval_periods[period_start_index]
            
            period = [period_start]
            for i in range(1, activity["duration"]):
                next_index = period_start_index + i
                if next_index < len(non_interval_periods):
                    period.append(non_interval_periods[next_index])
                else:
                    break
            
            individual.append({
                "subgroup": subgroup,
                "activity_id": activity["code"],
                "day": day,
                "period": period,
                "room": room,
                "teacher": teacher,
                "duration": activity["duration"],
                "subject": activity["subject"]
            })
    
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
    
    # Count conflicts
    for schedule in individual:
        key = (schedule["day"]["_id"], schedule["period"][0]["_id"])
        if key not in scheduled_activities:
            scheduled_activities[key] = []
        scheduled_activities[key].append(schedule)
        
        # Check for interval violations (activities scheduled during break times)
        for per in schedule["period"]:
            if per.get("is_interval", False):
                interval_conflicts += 1
                logging.debug(f"Interval violation: Activity {schedule['activity_id']} scheduled during interval {per['name']}")

    # Evaluate conflicts for each time slot
    for key, scheduled in scheduled_activities.items():
        day_id, period_id = key
        logging.debug(f"Checking conflicts for day={day_id}, period={period_id}")
        
        rooms_used = {}
        teachers_involved = []

        for activity in scheduled:
            room = activity["room"]
            if room["code"] in rooms_used:
                rooms_used[room["code"]] += 1
                logging.debug(f"Room conflict detected: {room['code']}")
            else:
                rooms_used[room["code"]] = 1

            teachers_involved.append(activity["teacher"])

        # Count room conflicts (multiple activities in same room at same time)
        for room, count in rooms_used.items():
            if count > 1:
                room_conflicts += count - 1
                logging.debug(f"Room {room} has {count} conflicts")

        # Count teacher conflicts (same teacher in multiple places at same time)
        unique_teachers = len(set(teachers_involved))
        if len(teachers_involved) > unique_teachers:
            teacher_conflicts += len(teachers_involved) - unique_teachers
            logging.debug(f"Teacher conflicts in this slot: {len(teachers_involved) - unique_teachers}")

    # Period conflicts: check for overlapping activities within the SAME subgroup
    subgroup_period_assignments = {}
    for schedule in individual:
        subgroup = schedule["subgroup"]
        for per in schedule["period"]:
            key = (subgroup, schedule["day"]["_id"], per["_id"])
            if key not in subgroup_period_assignments:
                subgroup_period_assignments[key] = []
            subgroup_period_assignments[key].append(schedule["activity_id"])
    
    for key, activities in subgroup_period_assignments.items():
        if len(activities) > 1:
            period_conflicts += len(activities) - 1
            subgroup = key[0]
            logging.debug(f"Period conflict: {len(activities)} activities for subgroup {subgroup} in same period")

    logging.debug(f"Evaluation complete - Conflicts: Teacher={teacher_conflicts}, Room={room_conflicts}, "
                f"Interval={interval_conflicts}, Period={period_conflicts}")
    
    return teacher_conflicts, room_conflicts, interval_conflicts, period_conflicts

def custom_mutate(individual, indpb=0.2):
    """Custom mutation that tries to resolve conflicts"""
    non_interval_periods = [p for p in periods if not p.get("is_interval", False)]
    
    for i in range(len(individual)):
        if random.random() < indpb:
            activity = individual[i]
            
            # Try to find a better time slot for this activity
            max_attempts = 10
            for attempt in range(max_attempts):
                new_day = random.choice(days)
                max_start_index = len(non_interval_periods) - activity["duration"]
                if max_start_index < 0:
                    continue
                    
                period_start_index = random.randint(0, max_start_index)
                period_start = non_interval_periods[period_start_index]
                
                new_period = [period_start]
                for j in range(1, activity["duration"]):
                    next_index = period_start_index + j
                    if next_index < len(non_interval_periods):
                        new_period.append(non_interval_periods[next_index])
                    else:
                        break
                
                # Update the activity
                individual[i]["day"] = new_day
                individual[i]["period"] = new_period
                break
    
    return individual,

toolbox.register("evaluate", evaluate)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", custom_mutate, indpb=0.2)
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
