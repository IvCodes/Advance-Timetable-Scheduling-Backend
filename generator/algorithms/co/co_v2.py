import random
import threading
import time
from collections import defaultdict
from generator.data_collector import *

# Configurable parameters
NUM_ANTS = 30
NUM_ITERATIONS = 40
EVAPORATION_RATE = 0.5
ALPHA = 1
BETA = 2
Q = 100
MAX_ATTEMPTS = 5  

# Global data stores
days = []
spaces = []
modules = []
periods = []
students = []
teachers = []  
years = []
activities = []
constraints = []
teacher_dict = {} 
module_dict = {}  

# Data for tracking scheduling
pheromone = defaultdict(lambda: 1.0)
heuristic = defaultdict(float)

def get_data():
    """Load all required data for timetable generation"""
    global days, spaces, modules, periods, students, teachers, years, activities, constraints
    global teacher_dict, module_dict

    days = get_days()
    spaces = get_spaces()
    modules = get_modules()
    periods = get_periods()
    students = get_students()
    teachers = get_teachers()
    years = get_years()
    activities = get_activities()
    constraints = get_constraints()
    
    # Create lookup dictionaries for quick access
    teacher_dict = {t["id"]: t for t in teachers}
    module_dict = {m["code"]: m for m in modules}
    
    # Add index to periods for easier consecutive period identification
    for idx, p in enumerate(periods):
        p["index"] = idx

def get_num_students_per_activity(activity_code):
    """Calculate the number of students registered for an activity"""
    activity = next((act for act in activities if act["code"] == activity_code), None)
    if not activity:
        return 0
        
    module_code = activity["subject"]
    
   
    if activity.get("subgroup_ids"):
        return sum(1 for s in students 
                  if module_code in s["subjects"] and 
                  any(sg in s.get("subgroups", []) for sg in activity["subgroup_ids"]))
    
 
    return len([s for s in students if module_code in s["subjects"]])

def initialize_heuristic():
    """Initialize heuristic values for activities based on number of students"""
    global heuristic
    for activity in activities:
        num_students = get_num_students_per_activity(activity["code"])
        
        heuristic[activity["code"]] = 1 / (1 + num_students)

def find_consecutive_periods(duration, valid_periods):
    """Find all possible blocks of consecutive periods of required duration"""
    consecutive_blocks = []
    sorted_periods = sorted(valid_periods, key=lambda p: p["index"])
    
    for i in range(len(sorted_periods) - duration + 1):
        block = sorted_periods[i:i+duration]
        # Check if periods are truly consecutive by index
        if all(block[j+1]["index"] == block[j]["index"] + 1 for j in range(len(block)-1)):
            consecutive_blocks.append(block)
    
    return consecutive_blocks

def get_activity_priority(activity):
    """Calculate priority for scheduling an activity"""
    # Combine pheromone and heuristic information using ALPHA and BETA parameters
    return (pheromone[activity["code"]] ** ALPHA) * (heuristic[activity["code"]] ** BETA)

def check_teacher_constraint(teacher_id, day_id, period_ids):
    """Check if teacher is available for the given periods based on constraints"""
    relevant_constraints = [
        c for c in constraints 
        if c["is_type"] == "time" and c["scope"] == "teacher" and 
        c.get("teacher_id") == teacher_id
    ]
    
    for constraint in relevant_constraints:
        
        if (constraint.get("day_id") == day_id or constraint.get("day_id") is None):
            if constraint.get("period_ids"):
               
                if any(p_id in constraint["period_ids"] for p_id in period_ids):
                    return False
    return True

def check_space_constraint(space_code, day_id, period_ids):
    """Check if space is available for the given periods based on constraints"""
    relevant_constraints = [
        c for c in constraints 
        if c["is_type"] == "time" and c["scope"] == "space" and 
        c.get("space_code") == space_code
    ]
    
    for constraint in relevant_constraints:
       
        if (constraint.get("day_id") == day_id or constraint.get("day_id") is None):
            if constraint.get("period_ids"):
             
                if any(p_id in constraint["period_ids"] for p_id in period_ids):
                    return False
    return True

def construct_solution():
    """Build a complete timetable solution using ACO approach"""
    solution = []
    
    # Track schedules to avoid conflicts
    teacher_schedule = defaultdict(lambda: defaultdict(set))
    space_schedule = defaultdict(lambda: defaultdict(set))
    group_schedule = defaultdict(lambda: defaultdict(set))
    
    
    valid_non_interval_periods = [p for p in periods if not p.get("is_interval", False)]
    
    # Sort activities by priority combining pheromone and heuristic information
    sorted_activities = sorted(
        activities, 
        key=get_activity_priority,
        reverse=True 
    )
    
    for activity in sorted_activities:
        num_students = get_num_students_per_activity(activity["code"])
        
        # Find suitable spaces
        valid_spaces = [s for s in spaces if s["capacity"] >= num_students]
        if not valid_spaces:
            continue 

        # Get teachers assigned to this activity
        teacher_ids = activity.get("teacher_ids", [])
        if not teacher_ids:
            continue 
            
        random.shuffle(teacher_ids)
        
        # Get student subgroups if applicable
        subgroups = activity.get("subgroup_ids", [])
        
        scheduled = False
        attempts = 0
        
        while not scheduled and attempts < MAX_ATTEMPTS:
            attempts += 1
            shuffled_days = random.sample(days, len(days))
            
            for day in shuffled_days:
                day_id = day["_id"]
                random.shuffle(valid_spaces)
                
                for space in valid_spaces:
                    space_code = space["code"]
                    
                    # Check space availability based on constraints
                    if not check_space_constraint(space_code, day_id, [p["_id"] for p in valid_non_interval_periods]):
                        continue
                    
                    for teacher_id in teacher_ids:
                        # Check teacher availability based on constraints
                        if not check_teacher_constraint(teacher_id, day_id, [p["_id"] for p in valid_non_interval_periods]):
                            continue
                            
                        # Find periods that are free for teacher, space, and student groups
                        free_periods = [
                            p for p in valid_non_interval_periods
                            if p["index"] not in teacher_schedule[teacher_id][day_id]
                            and p["index"] not in space_schedule[space_code][day_id]
                            and all(p["index"] not in group_schedule[sg][day_id] for sg in subgroups)
                        ]
                        
                        # Find consecutive blocks of required duration
                        blocks = find_consecutive_periods(activity["duration"], free_periods)
                        
                        if blocks:
                            # Choose a block based on probability proportional to pheromone * heuristic
                            chosen_block = random.choice(blocks)
                            
                            # Create timetable entry
                            solution.append({
                                "activity_id": activity["code"],
                                "day": day,
                                "period": chosen_block,
                                "space": space,
                                "teacher": teacher_id,
                                "duration": activity["duration"],
                                "subject": activity["subject"],
                                "subgroup": activity["subgroup_ids"]
                            })
                            
                            # Update schedules
                            for p in chosen_block:
                                teacher_schedule[teacher_id][day_id].add(p["index"])
                                space_schedule[space_code][day_id].add(p["index"])
                                for sg in subgroups:
                                    group_schedule[sg][day_id].add(p["index"])
                                    
                            scheduled = True
                            break
                        
                    if scheduled:
                        break
                if scheduled:
                    break
        
    return solution

def evaluate_solution(solution):
    """Evaluate a timetable solution using multiple criteria"""
    if not solution:
        return (0, 0, 0, 0, 0, 0, float('inf'))
    
    # Initialize counters for different types of conflicts
    teacher_conflicts = 0
    room_conflicts = 0
    interval_conflicts = 0
    period_conflicts = 0
    group_conflicts = 0
    
    # Track scheduled activities by time slot
    scheduled_map = defaultdict(list)
    
    # Populate the schedule map
    for entry in solution:
        day_id = entry["day"]["_id"]
        for p in entry["period"]:
            period_id = p["_id"]
            scheduled_map[(day_id, period_id)].append(entry)
            
            # Count activities scheduled during intervals
            if p.get("is_interval", False):
                interval_conflicts += 1

    # Count overlaps for teachers, rooms, and student groups
    for time_slot, entries in scheduled_map.items():
        teachers_used = defaultdict(int)
        rooms_used = defaultdict(int)
        groups_used = defaultdict(int)
        
        for entry in entries:
            teachers_used[entry["teacher"]] += 1
            rooms_used[entry["space"]["code"]] += 1
            
            # Count conflicts for student subgroups
            if entry["subgroup"]:
                groups_used[tuple(entry["subgroup"])] += 1

            else:
                # If no subgroup specified, consider the whole module
                module_students = [s for s in students if entry["subject"] in s["subjects"]]
                for student in module_students:
                    student_id = student.get("id")
                    if student_id:
                        groups_used[f"student_{student_id}"] += 1
        
        # Sum up conflicts (occurrences - 1)
        teacher_conflicts += sum(v-1 for v in teachers_used.values() if v > 1)
        room_conflicts += sum(v-1 for v in rooms_used.values() if v > 1)
        group_conflicts += sum(v-1 for v in groups_used.values() if v > 1)
        
        # Overall period conflicts
        period_conflicts += max(0, len(entries)-1)

    # Calculate teacher workload compliance
    teacher_hours = defaultdict(int)
    for entry in solution:
        teacher_hours[entry["teacher"]] += entry["duration"]
    
    overload = 0
    for teacher_id, hours in teacher_hours.items():
        teacher = teacher_dict.get(teacher_id, {})
        target = teacher.get("target_hours", 10)
        min_hours = teacher.get("min_hours", 0)
        max_hours = teacher.get("max_hours", float('inf'))
        
        # Penalize both under and over allocation
        if hours < min_hours:
            overload += (min_hours - hours) 
        elif hours > max_hours:
            overload += (hours - max_hours)
        
    # Validate additional constraints
    constraint_penalty = validate_constraints(solution)

    # Calculate total penalty
    total = (
        teacher_conflicts * 10 +  # Teacher conflicts are critical
        room_conflicts * 10 +     # Room conflicts are critical
        interval_conflicts * 5 +  # Interval conflicts important but can sometimes be necessary
        group_conflicts * 8 +     # Student group conflicts are important
        period_conflicts * 3 +    # Overall period conflicts (redundant but useful as indicator)
        overload * 2 +            # Teacher workload issues
        constraint_penalty        # Additional constraints with their own weights
    )
    
    return (teacher_conflicts, room_conflicts, interval_conflicts, 
            period_conflicts, overload, constraint_penalty, total)

def validate_constraints(solution):
    """Validate all constraints and return total penalty"""
    penalty = 0
    
    # Process each constraint type
    for constraint in constraints:
        constraint_type = constraint.get("type", "soft")  # Default to soft constraint
        weight = constraint.get("weight", 1)
        
        # Hard constraints have higher weight multiplier
        weight_multiplier = 10 if constraint_type == "hard" else 1
        
        # Check constraint by type
        if constraint["is_type"] == "time":
            # Time-based constraints
            penalty += validate_time_constraint(constraint, solution) * weight * weight_multiplier
        elif constraint["is_type"] == "assignment":
            # Teacher-subject assignment constraints
            penalty += validate_assignment_constraint(constraint, solution) * weight * weight_multiplier
        elif constraint["is_type"] == "workload":
            # Workload constraints
            penalty += validate_workload_constraint(constraint, solution) * weight * weight_multiplier
        elif constraint["is_type"] == "spread":
            # Activities that should be spread throughout the week
            penalty += validate_spread_constraint(constraint, solution) * weight * weight_multiplier
    
    return penalty

def validate_time_constraint(constraint, solution):
    """Validate time-based constraints"""
    penalty = 0
    scope = constraint.get("scope")
    
    if scope == "teacher":
        # Teacher availability constraint
        teacher_id = constraint.get("teacher_id")
        if not teacher_id:
            return 0
            
        day_id = constraint.get("day_id")
        period_ids = constraint.get("period_ids", [])
        
        for entry in solution:
            if entry["teacher"] == teacher_id:
                # If day is specified in constraint, check only that day
                if day_id and entry["day"]["_id"] != day_id:
                    continue
                    
                # Check if any scheduled period conflicts with restricted periods
                for p in entry["period"]:
                    if p["_id"] in period_ids:
                        penalty += 1
                        
    elif scope == "space":
        # Space availability constraint
        space_code = constraint.get("space_code")
        if not space_code:
            return 0
            
        day_id = constraint.get("day_id")
        period_ids = constraint.get("period_ids", [])
        
        for entry in solution:
            if entry["space"]["code"] == space_code:
                # If day is specified in constraint, check only that day
                if day_id and entry["day"]["_id"] != day_id:
                    continue
                    
                # Check if any scheduled period conflicts with restricted periods
                for p in entry["period"]:
                    if p["_id"] in period_ids:
                        penalty += 1
                        
    elif scope == "activity":
        # Activity timing constraint (must be at specific time)
        activity_id = constraint.get("activity_id")
        if not activity_id:
            return 0
            
        day_id = constraint.get("day_id")
        period_ids = constraint.get("period_ids", [])
        require_in = constraint.get("require_in", True)  # True = must be in these periods, False = must not be
        
        for entry in solution:
            if entry["activity_id"] == activity_id:
                scheduled_period_ids = [p["_id"] for p in entry["period"]]
                
                if require_in:
                    # Activity must be in specified periods
                    if day_id and entry["day"]["_id"] != day_id:
                        penalty += 1
                    elif not any(p_id in period_ids for p_id in scheduled_period_ids):
                        penalty += 1
                else:
                    # Activity must NOT be in specified periods
                    if day_id and entry["day"]["_id"] == day_id:
                        if any(p_id in period_ids for p_id in scheduled_period_ids):
                            penalty += 1
    
    return penalty

def validate_assignment_constraint(constraint, solution):
    """Validate teacher-subject assignment constraints"""
    penalty = 0
    teacher_id = constraint.get("teacher_id")
    subject_code = constraint.get("subject_code")
    
    if not teacher_id or not subject_code:
        return 0
        
    # Check if assignment preference is respected
    require_teach = constraint.get("require_teach", True)  # True = teacher must teach subject, False = must not
    
    for entry in solution:
        if entry["subject"] == subject_code:
            if require_teach and entry["teacher"] != teacher_id:
                penalty += 1
            elif not require_teach and entry["teacher"] == teacher_id:
                penalty += 1
    
    return penalty

def validate_workload_constraint(constraint, solution):
    """Validate workload constraints"""
    penalty = 0
    teacher_id = constraint.get("teacher_id")
    
    if not teacher_id:
        return 0
        
    min_hours = constraint.get("min_hours", 0)
    max_hours = constraint.get("max_hours", float('inf'))
    
    # Calculate actual hours
    teacher_hours = sum(
        entry["duration"] for entry in solution 
        if entry["teacher"] == teacher_id
    )
    
    # Check if hours are within constraints
    if teacher_hours < min_hours:
        penalty += (min_hours - teacher_hours)
    elif teacher_hours > max_hours:
        penalty += (teacher_hours - max_hours)
    
    return penalty

def validate_spread_constraint(constraint, solution):
    """Validate spread constraints for activities throughout the week"""
    penalty = 0
    activity_ids = constraint.get("activity_ids", [])
    
    if not activity_ids:
        return 0
        
    min_days_between = constraint.get("min_days_between", 1)
    
    # Find all instances of the activities
    activity_instances = []
    for activity_id in activity_ids:
        instances = [entry for entry in solution if entry["activity_id"] == activity_id]
        activity_instances.extend(instances)
    
    # Group by days
    days_with_activities = defaultdict(list)
    for instance in activity_instances:
        day_id = instance["day"]["_id"]
        days_with_activities[day_id].append(instance)
    
    # Check if too many activities on same day
    if len(days_with_activities) < len(activity_instances) / (min_days_between + 1):
        penalty += len(activity_instances) - len(days_with_activities)
    
    # Check day intervals
    day_ids = [day["_id"] for day in days]
    days_with_activities_ids = sorted(
        days_with_activities.keys(),
        key=lambda d: day_ids.index(d)
    )
    
    for i in range(len(days_with_activities_ids) - 1):
        current_day_idx = day_ids.index(days_with_activities_ids[i])
        next_day_idx = day_ids.index(days_with_activities_ids[i+1])
        
        days_apart = next_day_idx - current_day_idx
        if days_apart < min_days_between:
            penalty += min_days_between - days_apart
    
    return penalty

def update_pheromone(all_solutions, best_solution):
    """Update pheromone trails based on solution quality"""
    global pheromone
    
    # Evaporate pheromone on all paths
    for code in list(pheromone.keys()):
        pheromone[code] *= (1 - EVAPORATION_RATE)
    
    # Deposit pheromone based on best solution
    if best_solution:
        *_, best_score = evaluate_solution(best_solution)
        
        # The better the solution (lower score), the more pheromone gets deposited
        deposit = Q / (1 + best_score) if best_score else Q
        
        for entry in best_solution:
            pheromone[entry["activity_id"]] += deposit

def ant_task(results, best_solution, best_score, lock):
    """Task function for each ant thread"""
    solution = construct_solution()
    *_, score = evaluate_solution(solution)
    
    with lock:
        results.append((solution, score))
        if score < best_score[0]:
            best_solution[0] = solution
            best_score[0] = score

def generate_co():
    """Main function to generate a timetable using ACO"""
    start_time = time.time()
    
    # Load all data
    get_data()
    
    # Initialize heuristic information
    initialize_heuristic()
    
    # Track best solution found
    best_solution = [None]
    best_score = [float('inf')]
    lock = threading.Lock()
    
    # Track progress metrics
    iteration_scores = []

    print("Starting ACO timetable generation...")
    for iteration in range(NUM_ITERATIONS):
        iteration_start = time.time()
        results = []
        threads = []
        
        # Create and start threads for parallel ant processing
        for _ in range(NUM_ANTS):
            t = threading.Thread(
                target=ant_task,
                args=(results, best_solution, best_score, lock)
            )
            threads.append(t)
            t.start()
            
        # Wait for all threads to complete
        for t in threads:
            t.join()
            
        # Update pheromones based on results
        update_pheromone(results, best_solution[0])
        
        # Calculate statistics for this iteration
        if results:
            scores = [score for _, score in results]
            avg_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)
            iteration_scores.append(min_score)
        else:
            avg_score = min_score = max_score = "N/A"
            
        iteration_time = time.time() - iteration_start
        
        # Print progress information
        print(f"Iteration {iteration+1}/{NUM_ITERATIONS}: Best Score = {best_score[0]}")
        print(f"  Min: {min_score}, Avg: {avg_score}, Max: {max_score}")
        print(f"  Time: {iteration_time:.2f}s, Total: {time.time() - start_time:.2f}s")
        
        # Optionally: Early termination if solution is good enough
        if best_score[0] < 10:  # Almost no conflicts
            print("Found excellent solution, terminating early.")
            break

    # Print final statistics
    total_time = time.time() - start_time
    print(f"\nTimetable generation completed in {total_time:.2f} seconds")
    print(f"Final solution score: {best_score[0]}")
    
    if best_solution[0]:
        teacher_conflicts, room_conflicts, interval_conflicts, period_conflicts, overload, constraint_penalty, _ = evaluate_solution(best_solution[0])
        print(f"Teacher conflicts: {teacher_conflicts}")
        print(f"Room conflicts: {room_conflicts}")
        print(f"Interval conflicts: {interval_conflicts}")
        print(f"Period conflicts: {period_conflicts}")
        print(f"Teacher workload issues: {overload}")
        print(f"Constraint penalties: {constraint_penalty}")
        print(f"Activities scheduled: {len(best_solution[0])}/{len(activities)}")
    
    return best_solution[0]