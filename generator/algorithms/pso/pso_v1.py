import random
import numpy as np
import uuid
from collections import defaultdict
from generator.data_collector import *

# PSO Parameters
NUM_PARTICLES = 60  # Similar to NUM_ANTS in ACO
NUM_ITERATIONS = 30
W = 0.5     # Inertia weight
C1 = 1.5    # Cognitive coefficient (particle's own best)
C2 = 2.0    # Social coefficient (swarm's best)
STUDENTS_PER_SUBGROUP = 40

# Global data holders (populated by get_data)
days = []
facilities = []
modules = []
periods = []
students = []
teachers = []
years = []
activities = []
constraints = []

def get_data():
    """
    Loads data from the database (or any source) into the global lists.
    """
    global days, facilities, modules, periods, students, teachers, years, activities, constraints
    days = get_days()
    facilities = get_spaces()
    modules = get_modules()
    periods = get_periods()
    students = get_students()
    teachers = get_teachers()
    years = get_years()
    activities = get_activities()
    constraints = get_constraints()

    # Add index to periods if it doesn't exist
    for idx, period in enumerate(periods):
        if "index" not in period:
            period["index"] = idx

def get_constraints():
    """
    Example function to fetch constraints from DB.
    Adjust as needed for your actual data structure.
    """
    # For illustration purposes only:
    constraints = list(db["constraints"].find())
    return constraints

# Particle state structures
particle_velocities = {}
particle_best_positions = {}
particle_best_scores = {}
global_best_position = None
global_best_score = float('inf')

#######################################################
#                  INITIALIZATION
#######################################################

def initialize_particles():
    """
    Initialize particles with random positions and zero velocities.
    In PSO for timetable scheduling, a "position" is a complete timetable solution.
    """
    global particle_velocities, particle_best_positions, particle_best_scores
    global global_best_position, global_best_score

    particles = []
    for i in range(NUM_PARTICLES):
        # Generate a random timetable solution as the initial position
        position = construct_solution()
        particles.append(position)
        
        # Initialize zero velocity components (for structural completeness)
        particle_velocities[i] = []
        
        # Evaluate initial position
        score = sum(evaluate_solution(position)[:2])  # Hard + soft constraints
        
        # Initialize particle's best position and score
        particle_best_positions[i] = position.copy()
        particle_best_scores[i] = score
        
        # Update global best if needed
        if score < global_best_score:
            global_best_score = score
            global_best_position = position.copy()
    
    return particles

#######################################################
#                   HELPER FUNCTIONS
#######################################################

def find_consecutive_periods(duration, valid_periods):
    """
    Given a duration and a list of valid (non-interval) periods sorted by 'index',
    return all possible blocks (each block is a list of consecutive period objects)
    of length 'duration' that do not skip any intermediate period indices.
    """
    consecutive_blocks = []
    valid_periods_sorted = sorted(valid_periods, key=lambda p: p["index"])
    
    for i in range(len(valid_periods_sorted) - duration + 1):
        block = valid_periods_sorted[i:i+duration]
        indices = [p["index"] for p in block]
        if all(indices[j+1] == indices[j] + 1 for j in range(len(indices) - 1)):
            consecutive_blocks.append(block)
    return consecutive_blocks

def get_teacher_availability(teacher_id, day_id, period_index):
    """
    Checks if a teacher is available (based on TC-001).
    Return True if available, False if not.
    """
    availability_constraint = next((c for c in constraints if c["code"] == "TC-001"), None)
    if not availability_constraint:
        return True
    teacher_unavailability = availability_constraint.get("details", {}).get(teacher_id, {})
    day_unavailability = teacher_unavailability.get(day_id, [])
    return (period_index not in day_unavailability)

def is_space_suitable(room, activity_type, space_requirements):
    """
    Determines if a space is suitable for an activity based on type and requirements.
    """
    attributes = room.get("attributes", {})
    room_name = room.get("name", "").lower()
    room_code = room.get("code", "").lower()
    
    if activity_type in ("Lecture+Tutorial"):
        if ("lecture" in room_name or "lh" in room_code or room.get("capacity", 0) >= 100):
            return True
    elif activity_type == "Lab":
        if ("lab" in room_name or "lab" in room_code or attributes.get("computers") == "Yes"):
            return True
    if space_requirements:
        for req in space_requirements:
            req_lower = req.lower()
            if "lecture hall" in req_lower and ("lecture" in room_name or "lh" in room_code):
                return True
            elif "lab" in req_lower and ("lab" in room_name or attributes.get("computers") == "Yes"):
                return True
    return False

def construct_solution():
    """
    Constructs a single timetable solution using a greedy + random approach.
    In PSO, this is used to initialize particles with valid starting positions.
    """
    solution = []
    scheduled_activities = set()
    
    # For each teacher & room, track usage
    teacher_schedule = defaultdict(lambda: defaultdict(set))
    room_schedule = defaultdict(lambda: defaultdict(set))
    
    # Skip interval periods in scheduling
    valid_non_interval_periods = [p for p in periods if not p.get("is_interval", False)]
    
    # Sort activities by descending subgroup count
    sorted_activities = sorted(activities, key=lambda act: -len(act.get("subgroup_ids", [])))
    
    for activity in sorted_activities:
        if activity["code"] in scheduled_activities:
            continue
        
        subgroup_ids = activity.get("subgroup_ids", [])
        subgroup_count = len(subgroup_ids)
        total_students = subgroup_count * STUDENTS_PER_SUBGROUP
        
        activity_type = activity.get("type", "Lecture+Tutorial")
        space_requirements = activity.get("space_requirements", [])
        
        valid_rooms = [room for room in facilities if is_space_suitable(room, activity_type, space_requirements)]
        valid_rooms.sort(key=lambda r: r["capacity"], reverse=True)
        if not valid_rooms:
            continue
        
        teacher_ids = activity.get("teacher_ids", [])
        random.shuffle(teacher_ids)
        
        # Determine if the activity must be split (common for labs)
        need_to_split = (activity_type == "Lab") and any(room["capacity"] < total_students for room in valid_rooms)
        
        if not need_to_split:
            suitable_rooms = [r for r in valid_rooms if r["capacity"] >= total_students]
            if not suitable_rooms:
                continue
            activity_scheduled = False
            for teacher_id in teacher_ids:
                if activity_scheduled:
                    break
                shuffled_days = random.sample(days, len(days))
                for day in shuffled_days:
                    if activity_scheduled:
                        break
                    day_id = day["_id"]
                    for room in suitable_rooms:
                        free_periods = []
                        for p in valid_non_interval_periods:
                            idx = p["index"]
                            if (idx not in teacher_schedule[teacher_id][day_id] and
                                idx not in room_schedule[room["code"]][day_id] and
                                get_teacher_availability(teacher_id, day_id, idx)):
                                free_periods.append(p)
                        possible_blocks = find_consecutive_periods(activity["duration"], free_periods)
                        if possible_blocks:
                            chosen_block = random.choice(possible_blocks)
                            solution.append({
                                "session_id" : str(uuid.uuid4()),
                                "subgroup": subgroup_ids,
                                "activity_id": activity["code"],
                                "day": day,
                                "period": chosen_block,
                                "room": room,
                                "teacher": teacher_id,
                                "duration": activity["duration"],
                                "subject": activity["subject"],
                                "student_count": total_students,
                                "activity_type": activity_type
                            })
                            scheduled_activities.add(activity["code"])
                            activity_scheduled = True
                            for p_obj in chosen_block:
                                p_idx = p_obj["index"]
                                teacher_schedule[teacher_id][day_id].add(p_idx)
                                room_schedule[room["code"]][day_id].add(p_idx)
                            break
        else:
            lab_rooms = [room for room in valid_rooms if room["capacity"] <= 120 and is_space_suitable(room, "Lab", ["Lab Room"])]
            if not lab_rooms:
                continue
            subgroup_scheduled = [False] * len(subgroup_ids)
            for i, sg in enumerate(subgroup_ids):
                if subgroup_scheduled[i]:
                    continue
                random.shuffle(teacher_ids)
                for teacher_id in teacher_ids:
                    if subgroup_scheduled[i]:
                        break
                    shuffled_days = random.sample(days, len(days))
                    for day in shuffled_days:
                        if subgroup_scheduled[i]:
                            break
                        day_id = day["_id"]
                        shuffled_labs = random.sample(lab_rooms, len(lab_rooms))
                        for room in shuffled_labs:
                            free_periods = []
                            for p in valid_non_interval_periods:
                                idx = p["index"]
                                if (idx not in teacher_schedule[teacher_id][day_id] and
                                    idx not in room_schedule[room["code"]][day_id] and
                                    get_teacher_availability(teacher_id, day_id, idx)):
                                    free_periods.append(p)
                            possible_blocks = find_consecutive_periods(activity["duration"], free_periods)
                            if possible_blocks:
                                chosen_block = random.choice(possible_blocks)
                                solution.append({
                                    "session_id" : str(uuid.uuid4()),
                                    "subgroup": [sg],
                                    "activity_id": activity["code"],
                                    "day": day,
                                    "period": chosen_block,
                                    "room": room,
                                    "teacher": teacher_id,
                                    "duration": activity["duration"],
                                    "subject": activity["subject"],
                                    "student_count": STUDENTS_PER_SUBGROUP,
                                    "activity_type": activity_type,
                                    "is_split": True
                                })
                                subgroup_scheduled[i] = True
                                for p_obj in chosen_block:
                                    p_idx = p_obj["index"]
                                    teacher_schedule[teacher_id][day_id].add(p_idx)
                                    room_schedule[room["code"]][day_id].add(p_idx)
                                break
            if all(subgroup_scheduled):
                scheduled_activities.add(activity["code"])
    
    return solution

#######################################################
#            UPDATED EVALUATION FUNCTION
#######################################################

def evaluate_solution(solution):
    """
    Evaluate the solution's quality in terms of constraints.
    Hard constraints (multiplied by 1000) include:
      - Base conflicts: room, teacher, interval, teacher availability, capacity, unscheduled, duplicates, room type.
      - Additional hard penalties:
          TC-004: Teacher maximum consecutive periods
          TC-009: Maximum teaching hours per day
          TC-011: Room availability
          TC-014: Activity duration check
          
    Soft constraints include:
      - Base soft violations: teacher working days (max/min days) and split activities penalty.
      - Additional soft penalties:
          TC-003: Teacher preferred time
          TC-005: Student preferred time
          TC-008: Minimum gap between classes for teacher
          TC-010: Student maximum classes per day
          TC-012: Teacher subject preference
    Returns a 15-tuple:
      (hard_conflicts, soft_violations, room_conflicts, teacher_conflicts, interval_conflicts,
       teacher_availability_conflicts, capacity_conflicts, unscheduled_activities,
       duplicate_activities, room_type_mismatches, min_days_violations, max_days_violations,
       split_activities_penalty, new_hard_penalties, new_soft_penalties)
    """
    # Base conflict checks
    room_conflicts = 0
    teacher_conflicts = 0
    interval_conflicts = 0
    teacher_availability_conflicts = 0
    capacity_conflicts = 0
    duplicate_activities = 0
    room_type_mismatches = 0
    split_activities_penalty = 0
    
    max_days_violations = 0
    min_days_violations = 0
    
    scheduled_map = defaultdict(list)  # (day_id, period_id) -> list of scheduled items
    teacher_working_days = defaultdict(set)
    scheduled_activities_count = defaultdict(int)
    activity_scheduled_subgroups = defaultdict(set)
    
    for item in solution:
        day_id = item["day"]["_id"]
        teacher_id = item["teacher"]
        activity_id = item["activity_id"]
        subgroups = item["subgroup"]
        act_type = item.get("activity_type", "Lecture+Tutorial")
        
        for sg in subgroups:
            activity_scheduled_subgroups[activity_id].add(sg)
        scheduled_activities_count[activity_id] += 1
        
        student_count = item.get("student_count", 0)
        capacity = item["room"]["capacity"]
        if student_count > capacity:
            capacity_conflicts += 1
        
        if not is_space_suitable(item["room"], act_type, []):
            room_type_mismatches += 1
        
        teacher_working_days[teacher_id].add(day_id)
        
        for p in item["period"]:
            period_id = p["_id"]
            period_index = p["index"]
            if not get_teacher_availability(teacher_id, day_id, period_index):
                teacher_availability_conflicts += 1
            if p.get("is_interval", False):
                interval_conflicts += 1
            scheduled_map[(day_id, period_id)].append(item)
    
    for act_id, count in scheduled_activities_count.items():
        activity = next((a for a in activities if a["code"] == act_id), None)
        if not activity:
            continue
        expected_count = 1
        base_type = activity.get("type", "Lecture+Tutorial")
        if base_type == "Lab":
            subgroup_count = len(activity.get("subgroup_ids", []))
            expected_count = subgroup_count
            scheduled_subgroups = len(activity_scheduled_subgroups[act_id])
            if scheduled_subgroups < subgroup_count:
                split_activities_penalty += (subgroup_count - scheduled_subgroups) * 10
        elif base_type != "Lab" and count > expected_count:
            duplicate_activities += (count - expected_count)
    
    all_codes = set(a["code"] for a in activities)
    scheduled_codes = set(x["activity_id"] for x in solution)
    unscheduled_activities = len(all_codes - scheduled_codes)
    
    for _, items_in_slot in scheduled_map.items():
        room_usage = defaultdict(int)
        teacher_usage = defaultdict(int)
        for it in items_in_slot:
            room_usage[it["room"]["code"]] += 1
            teacher_usage[it["teacher"]] += 1
        for c in room_usage.values():
            if c > 1:
                room_conflicts += (c - 1)
        for c in teacher_usage.values():
            if c > 1:
                teacher_conflicts += (c - 1)
    
    # Soft constraints: teacher working days
    max_days_constraint = next((c for c in constraints if c["code"] == "TC-002"), None)
    min_days_constraint = next((c for c in constraints if c["code"] == "TC-003"), None)
    max_days_weight = max_days_constraint["weight"] if max_days_constraint else 5
    min_days_weight = min_days_constraint["weight"] if min_days_constraint else 5
    default_max_days = 5
    default_min_days = 1
    
    for t_id, days_set in teacher_working_days.items():
        days_worked = len(days_set)
        teacher_max_days = max_days_constraint.get("details", {}).get(t_id, default_max_days) if max_days_constraint else default_max_days
        teacher_min_days = min_days_constraint.get("details", {}).get(t_id, default_min_days) if min_days_constraint else default_min_days
        if days_worked > teacher_max_days:
            max_days_violations += (days_worked - teacher_max_days) * max_days_weight
        if days_worked < teacher_min_days:
            min_days_violations += (teacher_min_days - days_worked) * min_days_weight
    
    base_hard = room_conflicts + teacher_conflicts + interval_conflicts + teacher_availability_conflicts + capacity_conflicts + unscheduled_activities + duplicate_activities + room_type_mismatches
    
    # Additional constraint checks
    new_hard_penalties = 0
    new_soft_penalties = 0
    
    # Helper dictionaries from constraints
    teacher_pref = {}
    tc003 = next((c for c in constraints if c["code"] == "TC-003"), None)
    if tc003:
        for tp in tc003["details"].get("teacher_preferred_times", []):
            teacher_pref[tp["teacher_id"]] = tp["preferred_times"]
    
    teacher_max_consec = {}
    tc004 = next((c for c in constraints if c["code"] == "TC-004"), None)
    if tc004:
        for m in tc004["details"].get("max_consecutive_periods", []):
            teacher_max_consec[m["teacher_id"]] = m["max_periods"]
    
    student_pref = {}
    tc005 = next((c for c in constraints if c["code"] == "TC-005"), None)
    if tc005:
        for sp in tc005["details"].get("student_preferred_times", []):
            student_pref[sp["subgroup_id"]] = sp["preferred_times"]
    
    teacher_min_gap = {}
    tc008 = next((c for c in constraints if c["code"] == "TC-008"), None)
    if tc008:
        for mg in tc008["details"].get("min_gap_between_classes", []):
            teacher_min_gap[mg["teacher_id"]] = mg["min_gap"]
    
    teacher_max_hours = {}
    tc009 = next((c for c in constraints if c["code"] == "TC-009"), None)
    if tc009:
        for mh in tc009["details"].get("max_teaching_hours_per_day", []):
            teacher_max_hours[mh["teacher_id"]] = mh["max_hours"]
    
    student_max_classes = {}
    tc010 = next((c for c in constraints if c["code"] == "TC-010"), None)
    if tc010:
        for sc in tc010["details"].get("max_classes_per_day", []):
            student_max_classes[sc["subgroup_id"]] = sc["max_classes"]
    
    room_unavail = {}
    tc011 = next((c for c in constraints if c["code"] == "TC-011"), None)
    if tc011:
        for ru in tc011["details"].get("room_unavailability", []):
            room_unavail[ru["room_id"]] = ru["unavailable_times"]
    
    teacher_subject_pref = {}
    tc012 = next((c for c in constraints if c["code"] == "TC-012"), None)
    if tc012:
        for tsp in tc012["details"].get("teacher_subject_preference", []):
            teacher_subject_pref[tsp["teacher_id"]] = tsp["preferred_subjects"]
    
    # Build teacher blocks and day durations; count classes per subgroup per day
    teacher_blocks = defaultdict(lambda: defaultdict(list))
    teacher_day_durations = defaultdict(lambda: defaultdict(int))
    subgroup_day_counts = defaultdict(lambda: defaultdict(int))
    
    for item in solution:
        day_id = item["day"]["_id"]
        teacher_id = item["teacher"]
        period_indices = [p["index"] for p in item["period"]]
        start = min(period_indices)
        end = max(period_indices)
        teacher_blocks[teacher_id][day_id].append((start, end))
        teacher_day_durations[teacher_id][day_id] += item["duration"]
        for sg in item["subgroup"]:
            subgroup_day_counts[sg][day_id] += 1
        
        # TC-003: Teacher preferred time (soft)
        if teacher_id in teacher_pref:
            pref_found = False
            for pref in teacher_pref[teacher_id]:
                if pref["day_id"] == day_id:
                    preferred_periods = pref.get("periods", [])
                    if any(p["_id"] in preferred_periods for p in item["period"]):
                        pref_found = True
                        break
            if not pref_found:
                new_soft_penalties += tc003["weight"]
        
        # TC-012: Teacher subject preference (soft)
        if teacher_id in teacher_subject_pref:
            if item["subject"] not in teacher_subject_pref[teacher_id]:
                new_soft_penalties += tc012["weight"]
        
        # TC-014: Activity duration check (hard)
        expected_duration = item["duration"]
        actual_duration = len(item["period"])
        if actual_duration != expected_duration:
            new_hard_penalties += abs(actual_duration - expected_duration) * 10
        
        # TC-011: Room availability (hard)
        room_code = item["room"]["code"]
        if room_code in room_unavail:
            for unavail in room_unavail[room_code]:
                if unavail["day_id"] == day_id:
                    unavailable_periods = unavail.get("periods", [])
                    if any(p["_id"] in unavailable_periods for p in item["period"]):
                        new_hard_penalties += tc011["weight"]
        
        # TC-005: Student preferred time (soft)
        for sg in item["subgroup"]:
            if sg in student_pref:
                pref_found = False
                for pref in student_pref[sg]:
                    if pref["day_id"] == day_id:
                        preferred_periods = pref.get("periods", [])
                        if any(p["_id"] in preferred_periods for p in item["period"]):
                            pref_found = True
                            break
                if not pref_found:
                    new_soft_penalties += tc005["weight"]
    
    # TC-004: Teacher maximum consecutive periods (hard)
    for teacher_id, days_blocks in teacher_blocks.items():
        if teacher_id in teacher_max_consec:
            allowed = teacher_max_consec[teacher_id]
            for day_id, blocks in days_blocks.items():
                for (start, end) in blocks:
                    block_length = end - start + 1
                    if block_length > allowed:
                        new_hard_penalties += (block_length - allowed) * tc004["weight"]
    
    # TC-008: Minimum gap between classes for teacher (soft)
    for teacher_id, day_blocks in teacher_blocks.items():
        if teacher_id in teacher_min_gap:
            min_gap = teacher_min_gap[teacher_id]
            for day_id, blocks in day_blocks.items():
                blocks_sorted = sorted(blocks, key=lambda b: b[0])
                for i in range(len(blocks_sorted) - 1):
                    gap = blocks_sorted[i+1][0] - blocks_sorted[i][1] - 1
                    if gap < min_gap:
                        new_soft_penalties += (min_gap - gap) * tc008["weight"]
    
    # TC-009: Maximum teaching hours per day for teacher (hard)
    for teacher_id, day_durations in teacher_day_durations.items():
        if teacher_id in teacher_max_hours:
            max_hours = teacher_max_hours[teacher_id]
            for day_id, total in day_durations.items():
                if total > max_hours:
                    new_hard_penalties += (total - max_hours) * tc009["weight"]
    
    # TC-010: Student maximum classes per day (soft)
    for sg, day_counts in subgroup_day_counts.items():
        if sg in student_max_classes:
            max_classes = student_max_classes[sg]
            for day_id, count in day_counts.items():
                if count > max_classes:
                    new_soft_penalties += (count - max_classes) * tc010["weight"]
    
    hard_conflicts = 1000 * base_hard + new_hard_penalties
    soft_violations = max_days_violations + min_days_violations + split_activities_penalty + new_soft_penalties
    
    return (
        hard_conflicts,
        soft_violations,
        room_conflicts,
        teacher_conflicts,
        interval_conflicts,
        teacher_availability_conflicts,
        capacity_conflicts,
        unscheduled_activities,
        duplicate_activities,
        room_type_mismatches,
        min_days_violations,
        max_days_violations,
        split_activities_penalty,
        new_hard_penalties,
        new_soft_penalties
    )

def print_solution_stats(solution):
    """
    Print a summary of the solution's statistics and constraint violations.
    """
    (
        hard_conflicts,
        soft_violations,
        room_conflicts,
        teacher_conflicts,
        interval_conflicts,
        teacher_availability_conflicts,
        capacity_conflicts,
        unscheduled_activities,
        duplicate_activities,
        room_type_mismatches,
        min_days_violations,
        max_days_violations,
        split_activities_penalty,
        new_hard,
        new_soft
    ) = evaluate_solution(solution)
    
    print("\nSolution Statistics:")
    print(f"  Total scheduled entries: {len(solution)}")
    unique_activities = {s['activity_id'] for s in solution}
    print(f"  Unique activities scheduled: {len(unique_activities)}")
    print(f"  Activities not scheduled: {unscheduled_activities}")
    print(f"  Activities scheduled multiple times: {duplicate_activities}")
    print(f"  Hard constraint violations: {hard_conflicts}")
    print(f"    - Room conflicts: {room_conflicts}")
    print(f"    - Teacher conflicts: {teacher_conflicts}")
    print(f"    - Interval conflicts: {interval_conflicts}")
    print(f"    - Teacher availability conflicts: {teacher_availability_conflicts}")
    print(f"    - Room capacity conflicts: {capacity_conflicts}")
    print(f"    - Room type mismatches: {room_type_mismatches}")
    print(f"    - New hard penalties (TC-004, TC-009, TC-011, TC-014): {new_hard}")
    print(f"  Soft constraint violations: {soft_violations}")
    print(f"    - Max/min days violations: {max_days_violations + min_days_violations}")
    print(f"    - Split activities penalty: {split_activities_penalty}")
    print(f"    - New soft penalties (TC-003, TC-005, TC-008, TC-010, TC-012): {new_soft}")
    
    split_labs = [s for s in solution if s.get("is_split", False)]
    print(f"  Lab activities split into multiple sessions: {len(split_labs)}")
    
    activities_per_day = defaultdict(int)
    for s in solution:
        activities_per_day[s["day"]["_id"]] += 1
    print("\nActivities per day:")
    for d_id, count in activities_per_day.items():
        day_name = next((d["name"] for d in days if d["_id"] == d_id), str(d_id))
        print(f"  {day_name}: {count}")
    
    teacher_counts = defaultdict(int)
    for s in solution:
        teacher_counts[s["teacher"]] += 1
    top_teachers = sorted(teacher_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\nActivities per teacher (top 5):")
    for t_id, count in top_teachers:
        t_name = next((t["name"] for t in teachers if t["_id"] == t_id), str(t_id))
        print(f"  {t_name}: {count}")
    
    room_usage = defaultdict(int)
    for s in solution:
        room_usage[s["room"]["code"]] += 1
    top_rooms = sorted(room_usage.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\nRoom utilization (top 5):")
    for r_code, count in top_rooms:
        r = next((r for r in facilities if r["code"] == r_code), {})
        r_name = r.get("name", r_code)
        r_capacity = r.get("capacity", "Unknown")
        print(f"  {r_name} (Capacity: {r_capacity}): {count} activities")
    
    room_type_counts = defaultdict(int)
    for s in solution:
        act_type = s.get("activity_type", "Lecture+Tutorial")
        room_type_counts[act_type] += 1
    print("\nActivity types distribution:")
    for act_type, count in room_type_counts.items():
        print(f"  {act_type}: {count}")

#######################################################
#             UPDATE PARTICLES (PSO STEP)
#######################################################

def update_particles(particles):
    """
    Update particle positions based on PSO principles.
    In timetable scheduling, this means modifying the current schedule
    by blending assignments from the particle's personal best and the global best.
    """
    global particle_velocities
    global particle_best_positions, particle_best_scores
    global global_best_position, global_best_score
    
    for i, particle in enumerate(particles):
        new_position = []
        scheduled_activities = set()
        teacher_schedule = defaultdict(lambda: defaultdict(set))
        room_schedule = defaultdict(lambda: defaultdict(set))
        
        # Step 1: Inertia - keep some items from current position
        inertia_items = []
        for item in particle:
            if random.random() < W:
                inertia_items.append(item.copy())
                scheduled_activities.add(item["activity_id"])
                d_id = item["day"]["_id"]
                for p in item["period"]:
                    idx = p["index"]
                    teacher_schedule[item["teacher"]][d_id].add(idx)
                    room_schedule[item["room"]["code"]][d_id].add(idx)
        
        # Step 2: Cognitive (personal best)
        personal_best = particle_best_positions[i]
        for item in personal_best:
            if random.random() < C1 and item["activity_id"] not in scheduled_activities:
                d_id = item["day"]["_id"]
                conflict = False
                for p in item["period"]:
                    idx = p["index"]
                    if (idx in teacher_schedule[item["teacher"]][d_id] or
                        idx in room_schedule[item["room"]["code"]][d_id]):
                        conflict = True
                        break
                if not conflict:
                    inertia_items.append(item.copy())
                    scheduled_activities.add(item["activity_id"])
                    for p in item["period"]:
                        idx = p["index"]
                        teacher_schedule[item["teacher"]][d_id].add(idx)
                        room_schedule[item["room"]["code"]][d_id].add(idx)
        
        # Step 3: Social (global best)
        if global_best_position:
            for item in global_best_position:
                if random.random() < C2 and item["activity_id"] not in scheduled_activities:
                    d_id = item["day"]["_id"]
                    conflict = False
                    for p in item["period"]:
                        idx = p["index"]
                        if (idx in teacher_schedule[item["teacher"]][d_id] or
                            idx in room_schedule[item["room"]["code"]][d_id]):
                            conflict = True
                            break
                    if not conflict:
                        inertia_items.append(item.copy())
                        scheduled_activities.add(item["activity_id"])
                        for p in item["period"]:
                            idx = p["index"]
                            teacher_schedule[item["teacher"]][d_id].add(idx)
                            room_schedule[item["room"]["code"]][d_id].add(idx)
        
        # (Optionally, one could try to schedule any remaining activities here.)
        new_position = inertia_items
        
        new_score = sum(evaluate_solution(new_position)[:2])
        particles[i] = new_position
        
        if new_score < particle_best_scores[i]:
            particle_best_positions[i] = new_position.copy()
            particle_best_scores[i] = new_score
            if new_score < global_best_score:
                global_best_score = new_score
                global_best_position = new_position.copy()
                print(f"New global best! Score = {global_best_score}")
    
    return particles

#######################################################
#                   MAIN PSO FUNCTION
#######################################################

def generate_pso():
    """
    Main PSO function to coordinate:
      1) Data loading
      2) Particle initialization
      3) Iterative updates
      4) Final best solution
    """
    global global_best_position, global_best_score
    
    # 1) Load data
    get_data()
    
    # 2) Initialize particles
    particles = initialize_particles()
    
    print(f"Initial Global Best Score = {global_best_score}")
    
    # 3) Main PSO Iterations
    for iteration in range(NUM_ITERATIONS):
        print(f"\n=== PSO Iteration {iteration + 1} ===")
        particles = update_particles(particles)
        print(f"Iteration {iteration + 1} done. Current Global Best = {global_best_score}")
    
    # 4) Print final best solution stats
    print("\n=== Final Best Solution (PSO) ===")
    print_solution_stats(global_best_position)
    
    return global_best_position
