from app.utils.database import db
import numpy as np
from skfuzzy import control as ctrl
import skfuzzy as fuzz
from collections import defaultdict
import logging

# Configure logging
logger = logging.getLogger(__name__)

def calculate_conflicts(timetable):
    teacher_schedule = {}
    room_schedule = {}
    conflicts = 0

    for entry in timetable["timetable"]:
        # Use defensive programming to get values
        day = entry.get("day", {}).get("name", "Unknown")
        teacher = entry.get("teacher", "Unknown")
        
        # Handle different room ID formats
        room = None
        if "room" in entry:
            if isinstance(entry["room"], dict):
                # Try different possible keys for room ID
                room = entry["room"].get("_id") or entry["room"].get("id") or entry["room"].get("code")
            elif isinstance(entry["room"], str):
                room = entry["room"]
                
        # If no room ID found, use a placeholder
        if not room:
            room = f"unknown_room_{id(entry)}"
        
        # Get periods safely
        periods = []
        if "period" in entry:
            if isinstance(entry["period"], list):
                periods = [p.get("name", f"period_{i}") if isinstance(p, dict) else str(p) 
                          for i, p in enumerate(entry["period"])]
            elif isinstance(entry["period"], dict):
                periods = [entry["period"].get("name", "Unknown")]
        
        # Skip entries with missing critical data
        if day == "Unknown" or not periods:
            continue

        # Check teacher conflicts
        if teacher not in teacher_schedule:
            teacher_schedule[teacher] = {}
        if day not in teacher_schedule[teacher]:
            teacher_schedule[teacher][day] = []
        if any(period in teacher_schedule[teacher][day] for period in periods):
            conflicts += 1
        teacher_schedule[teacher][day].extend(periods)

        # Check room conflicts
        if room not in room_schedule:
            room_schedule[room] = {}
        if day not in room_schedule[room]:
            room_schedule[room][day] = []
        if any(period in room_schedule[room][day] for period in periods):
            conflicts += 1
        room_schedule[room][day].extend(periods)

    return conflicts

def calculate_room_utilization(timetable):
    total_utilization = 0
    total_entries = len(timetable["timetable"])
    
    if total_entries == 0:
        return 0

    for entry in timetable["timetable"]:
        # Get room capacity with fallback
        room_capacity = 30  # Default capacity if not found
        if "room" in entry and isinstance(entry["room"], dict):
            room_capacity = entry["room"].get("capacity", 30)
        
        # Estimate students count - could be improved with actual data
        students = 25  # Default student count
        if "students" in entry:
            if isinstance(entry["students"], list):
                students = len(entry["students"])
            elif isinstance(entry["students"], int):
                students = entry["students"]
        
        # Calculate utilization percentage (cap at 100%)
        utilization = min((students / max(room_capacity, 1)) * 100, 100)
        total_utilization += utilization

    return total_utilization / total_entries

def calculate_period_overlap(timetable):
    subgroup_schedule = {}
    overlaps = 0

    for entry in timetable["timetable"]:
        # Use defensive programming to get values
        day = entry.get("day", {}).get("name", "Unknown")
        
        # Get periods safely
        periods = []
        if "period" in entry:
            if isinstance(entry["period"], list):
                periods = [p.get("name", f"period_{i}") if isinstance(p, dict) else str(p) 
                          for i, p in enumerate(entry["period"])]
            elif isinstance(entry["period"], dict):
                periods = [entry["period"].get("name", "Unknown")]
        
        # Get module code safely
        module_code = "Unknown"
        if "module" in entry:
            if isinstance(entry["module"], dict):
                module_code = entry["module"].get("code", "Unknown")
            elif isinstance(entry["module"], str):
                module_code = entry["module"]
                
        # Skip entries with missing critical data
        if day == "Unknown" or not periods or module_code == "Unknown":
            continue

        for period in periods:
            key = f"{day}_{period}"
            if key not in subgroup_schedule:
                subgroup_schedule[key] = []
            
            if module_code in subgroup_schedule[key]:
                overlaps += 1
            subgroup_schedule[key].append(module_code)

    return overlaps

# Define fuzzy logic system
conflicts = ctrl.Antecedent(np.arange(0, 11, 1), 'conflicts')
room_utilization = ctrl.Antecedent(np.arange(0, 101, 1), 'room_utilization')
overlap = ctrl.Antecedent(np.arange(0, 11, 1), 'overlap')
quality = ctrl.Consequent(np.arange(0, 101, 1), 'quality')

# Define membership functions
conflicts['low'] = fuzz.trimf(conflicts.universe, [0, 0, 5])
conflicts['medium'] = fuzz.trimf(conflicts.universe, [0, 5, 10])
conflicts['high'] = fuzz.trimf(conflicts.universe, [5, 10, 10])

room_utilization['poor'] = fuzz.trimf(room_utilization.universe, [0, 0, 50])
room_utilization['adequate'] = fuzz.trimf(room_utilization.universe, [25, 50, 75])
room_utilization['good'] = fuzz.trimf(room_utilization.universe, [50, 100, 100])

overlap['low'] = fuzz.trimf(overlap.universe, [0, 0, 5])
overlap['medium'] = fuzz.trimf(overlap.universe, [0, 5, 10])
overlap['high'] = fuzz.trimf(overlap.universe, [5, 10, 10])

quality['poor'] = fuzz.trimf(quality.universe, [0, 0, 50])
quality['average'] = fuzz.trimf(quality.universe, [25, 50, 75])
quality['good'] = fuzz.trimf(quality.universe, [50, 100, 100])

# Define fuzzy rules
rule1 = ctrl.Rule(conflicts['low'] & room_utilization['good'] & overlap['low'], quality['good'])
rule2 = ctrl.Rule(conflicts['medium'] | room_utilization['adequate'] | overlap['medium'], quality['average'])
rule3 = ctrl.Rule(conflicts['high'] | room_utilization['poor'] | overlap['high'], quality['poor'])

# Create control system
quality_ctrl = ctrl.ControlSystem([rule1, rule2, rule3])
quality_evaluation = ctrl.ControlSystemSimulation(quality_ctrl)

def evaluate_timetable(conflict_count, utilization, overlap_count):
    quality_evaluation.input['conflicts'] = min(conflict_count, 10)  # Limit to max of our scale
    quality_evaluation.input['room_utilization'] = min(utilization, 100)  # Limit to max of our scale
    quality_evaluation.input['overlap'] = min(overlap_count, 10)  # Limit to max of our scale
    
    # Compute result
    quality_evaluation.compute()
    return quality_evaluation.output['quality']

def evaluate():
    """
    Evaluate all timetables in the database and return scores by algorithm
    """
    # Get all timetables from the database
    try:
        timetables = list(db["Timetable"].find()) if "Timetable" in db.list_collection_names() else []
        
        if not timetables:
            logger.warning("No timetables found in database for evaluation")
            return {}
    except Exception as e:
        logger.error(f"Error retrieving timetables from database: {str(e)}")
        return {}
        
    results_by_algorithm = defaultdict(list)
    algorithm_scores = defaultdict(list) 
    wins = defaultdict(int)

    # Group timetables by semester
    timetables_by_semester = defaultdict(list)
    for timetable in timetables:
        semester = timetable.get("semester", "Unknown")
        timetables_by_semester[semester].append(timetable)

    # Log evaluation process
    logger.info(f"Evaluating timetables across {len(timetables_by_semester)} semesters")
    
    for semester, schedules in timetables_by_semester.items():
        best_score = -1
        best_algorithm = None

        logger.info(f"Evaluating semester: {semester} ({len(schedules)} timetables)")
        
        for timetable in schedules:
            try:
                algorithm = timetable.get("algorithm", "Unknown")
                
                # Skip timetables without valid algorithm info
                if not algorithm or algorithm == "Unknown":
                    continue
                    
                # Calculate metrics
                conflict_count = calculate_conflicts(timetable)
                utilization = calculate_room_utilization(timetable)
                overlap_count = calculate_period_overlap(timetable)
                
                # Calculate overall score
                score = evaluate_timetable(conflict_count, utilization, overlap_count)
                
                # Store score for this algorithm
                algorithm_scores[algorithm].append(score)
                
                logger.info(f"  Algorithm: {algorithm}, Code: {timetable.get('code', 'N/A')}, Score: {score:.2f}")

                if score > best_score:
                    best_score = score
                    best_algorithm = algorithm
            except Exception as e:
                logger.error(f"Error evaluating timetable {timetable.get('code', 'N/A')}: {str(e)}")
                continue

        if best_algorithm:
            wins[best_algorithm] += 1
            logger.info(f"Best algorithm for {semester}: {best_algorithm} (Score: {best_score:.2f})")
    
    logger.info("Evaluation complete")
    
    # Return only the scores, not the logging output
    return algorithm_scores