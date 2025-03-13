import random
import numpy as np
import uuid
from collections import defaultdict
from generator.data_collector import *

# BCO Parameters
NUM_EMPLOYED_BEES = 30
NUM_ONLOOKER_BEES = 30
NUM_ITERATIONS = 30
LIMIT = 5           # Max number of trials before abandoning a food source
SCOUT_PERCENTAGE = 0.1
MAX_TRIALS = 5
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

########################################
# EVALUATION AND UTILITY FUNCTIONS
########################################

def evaluate_solution(solution):
    """
    Evaluate the solution's quality in terms of constraints.
    
    Hard constraints (multiplied by 1000) include:
      - Room conflicts, teacher conflicts, interval conflicts,
        teacher availability conflicts, room capacity conflicts,
        unscheduled activities, duplicate activities, room type mismatches.
      - Additional hard penalties:
          TC-004: Teacher maximum consecutive periods
          TC-009: Maximum teaching hours per day
          TC-011: Room availability
          TC-014: Activity duration check
          
    Soft constraints include:
      - Violations on teacher working days (max/min days) and split activities penalty.
      - Additional soft penalties:
          TC-003: Teacher preferred time
          TC-005: Student set preferred time
          TC-008: Minimum gap between classes for teacher
          TC-010: Student set maximum classes per day
          TC-012: Teacher subject preference
    """
    # ------------------------------
    # Base conflict checks (as before)
    # ------------------------------
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
        # Use default type "Lecture" if not provided
        activity_type = item.get("activity_type", "Lecture+Tutorial")
        
        for sg in subgroups:
            activity_scheduled_subgroups[activity_id].add(sg)
        scheduled_activities_count[activity_id] += 1
        
        # Check room capacity
        student_count = item.get("student_count", 0)
        capacity = item["room"]["capacity"]
        if student_count > capacity:
            capacity_conflicts += 1
        
        # Check if room is suitable for the activity type
        if not is_space_suitable(item["room"], activity_type, []):
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
        act_type = activity.get("type", "Lecture+Tutorial")
        if act_type == "Lab":
            subgroup_count = len(activity.get("subgroup_ids", []))
            expected_count = subgroup_count
            scheduled_subgroups = len(activity_scheduled_subgroups[act_id])
            if scheduled_subgroups < subgroup_count:
                split_activities_penalty += (subgroup_count - scheduled_subgroups) * 10
        elif act_type != "Lab" and count > expected_count:
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
    
    # Soft constraints: teacher working days vs. max/min days
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
    # ------------------------------
    # Additional Constraint Checks
    # ------------------------------
    new_hard_penalties = 0
    new_soft_penalties = 0
    
    # Build helper dictionaries from constraints
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
        
        # TC-005: Student set preferred time (soft)
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
    
    # TC-004: Teacher max consecutive periods (hard)
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
    
    # TC-010: Student set maximum classes per day (soft)
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

########################################
# HELPER FUNCTIONS FOR SCHEDULING
########################################

def find_consecutive_periods(duration, valid_periods):
    """
    Given a duration and a list of valid (non-interval) periods sorted by 'index',
    return all possible consecutive blocks of length 'duration' 
    where no intermediate period indices are skipped.
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
    Checks if a teacher is available (based on a 'TC-001' constraint).
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

########################################
# CONSTRUCTING A NEW SOLUTION
########################################

def construct_solution():
    """
    Constructs a single timetable solution using a greedy + random approach.
    Used for both initial solutions and for scout bees' random exploration.
    """
    solution = []
    scheduled_activities = set()
    
    # For each teacher & room, track occupied periods on each day
    teacher_schedule = defaultdict(lambda: defaultdict(set))
    room_schedule = defaultdict(lambda: defaultdict(set))
    
    valid_non_interval_periods = [p for p in periods if not p.get("is_interval", False)]
    
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
        
        need_to_split = (activity_type == "Lab") and any(room["capacity"] < total_students for room in valid_rooms)
        
        if not need_to_split:
            suitable_rooms = [room for room in valid_rooms if room["capacity"] >= total_students]
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
                        blocks = find_consecutive_periods(activity["duration"], free_periods)
                        if blocks:
                            chosen_block = random.choice(blocks)
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
            lab_rooms = [r for r in valid_rooms if r["capacity"] <= 60 and is_space_suitable(r, "Lab", ["Lab Room"])]
            if not lab_rooms:
                continue
            subgroup_scheduled = [False] * len(subgroup_ids)
            for i, subgroup_id in enumerate(subgroup_ids):
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
                            blocks = find_consecutive_periods(activity["duration"], free_periods)
                            if blocks:
                                chosen_block = random.choice(blocks)
                                solution.append({
                                    "session_id" : str(uuid.uuid4()),
                                    "subgroup": [subgroup_id],
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

########################################
# NEIGHBORHOOD SEARCH
########################################

def neighborhood_search(solution):
    """
    Performs a neighborhood search on the given solution to produce a 'nearby' solution.
    Strategies include rescheduling, swapping, moving, and changing room/teacher.
    """
    if not solution:
        return construct_solution()
    new_solution = solution.copy()
    strategy = random.choices(
        ["reschedule", "swap", "move", "change_room", "change_teacher"],
        weights=[0.1, 0.2, 0.3, 0.2, 0.2],
        k=1
    )[0]
    
    if strategy == "reschedule" and len(new_solution) > 0:
        idx_to_remove = random.randrange(len(new_solution))
        activity_to_reschedule = new_solution.pop(idx_to_remove)
        activity_id = activity_to_reschedule["activity_id"]
        activity = next((a for a in activities if a["code"] == activity_id), None)
        if activity:
            new_activity_schedule = schedule_single_activity(activity, new_solution)
            if new_activity_schedule:
                new_solution.extend(new_activity_schedule)
    
    elif strategy == "swap" and len(new_solution) >= 2:
        idx1, idx2 = random.sample(range(len(new_solution)), 2)
        act1, act2 = new_solution[idx1], new_solution[idx2]
        if act1["duration"] == act2["duration"]:
            new_solution[idx1]["day"], new_solution[idx2]["day"] = act2["day"], act1["day"]
            new_solution[idx1]["period"], new_solution[idx2]["period"] = act2["period"], act1["period"]
            new_solution[idx1]["room"], new_solution[idx2]["room"] = act2["room"], act1["room"]
    
    elif strategy == "move" and len(new_solution) > 0:
        idx_to_move = random.randrange(len(new_solution))
        activity_to_move = new_solution[idx_to_move]
        valid_days = random.sample(days, len(days))
        valid_periods = [p for p in periods if not p.get("is_interval", False)]
        for day in valid_days:
            day_id = day["_id"]
            teacher_schedule = defaultdict(lambda: defaultdict(set))
            room_schedule = defaultdict(lambda: defaultdict(set))
            for j, item in enumerate(new_solution):
                if j == idx_to_move:
                    continue
                t = item["teacher"]
                r = item["room"]["code"]
                d = item["day"]["_id"]
                for block_p in item["period"]:
                    teacher_schedule[t][d].add(block_p["index"])
                    room_schedule[r][d].add(block_p["index"])
            t_id = activity_to_move["teacher"]
            r_code = activity_to_move["room"]["code"]
            free_periods = []
            for p in valid_periods:
                idx = p["index"]
                if (idx not in teacher_schedule[t_id][day_id] and 
                    idx not in room_schedule[r_code][day_id] and 
                    get_teacher_availability(t_id, day_id, idx)):
                    free_periods.append(p)
            possible_blocks = find_consecutive_periods(activity_to_move["duration"], free_periods)
            if possible_blocks:
                chosen_block = random.choice(possible_blocks)
                new_solution[idx_to_move]["day"] = day
                new_solution[idx_to_move]["period"] = chosen_block
                break
    
    elif strategy == "change_room" and len(new_solution) > 0:
        idx_to_change = random.randrange(len(new_solution))
        activity_to_change = new_solution[idx_to_change]
        act_type = activity_to_change.get("activity_type", "Lecture+Tutorial")
        space_req = activity_to_change.get("space_requirements", [])
        student_count = activity_to_change.get("student_count", 0)
        suitable_rooms = [
            r for r in facilities
            if is_space_suitable(r, act_type, space_req)
            and r["capacity"] >= student_count
            and r["code"] != activity_to_change["room"]["code"]
        ]
        if suitable_rooms:
            room_schedule = defaultdict(lambda: defaultdict(set))
            for j, item in enumerate(new_solution):
                if j == idx_to_change:
                    continue
                r_code = item["room"]["code"]
                d_id = item["day"]["_id"]
                for block_p in item["period"]:
                    room_schedule[r_code][d_id].add(block_p["index"])
            day_id = activity_to_change["day"]["_id"]
            period_indices = [bp["index"] for bp in activity_to_change["period"]]
            available_rooms = []
            for r in suitable_rooms:
                if all(p_idx not in room_schedule[r["code"]][day_id] for p_idx in period_indices):
                    available_rooms.append(r)
            if available_rooms:
                new_solution[idx_to_change]["room"] = random.choice(available_rooms)
    
    elif strategy == "change_teacher" and len(new_solution) > 0:
        idx_to_change = random.randrange(len(new_solution))
        activity_to_change = new_solution[idx_to_change]
        act_id = activity_to_change["activity_id"]
        activity = next((a for a in activities if a["code"] == act_id), None)
        if activity and activity.get("teacher_ids"):
            teacher_ids = activity["teacher_ids"]
            current_t = activity_to_change["teacher"]
            alt_teachers = [t for t in teacher_ids if t != current_t]
            if alt_teachers:
                teacher_schedule = defaultdict(lambda: defaultdict(set))
                for j, item in enumerate(new_solution):
                    if j == idx_to_change:
                        continue
                    t_id = item["teacher"]
                    d_id = item["day"]["_id"]
                    for block_p in item["period"]:
                        teacher_schedule[t_id][d_id].add(block_p["index"])
                day_id = activity_to_change["day"]["_id"]
                period_indices = [bp["index"] for bp in activity_to_change["period"]]
                available_teachers = []
                for t_id in alt_teachers:
                    if all(p_idx not in teacher_schedule[t_id][day_id] for p_idx in period_indices) and \
                       all(get_teacher_availability(t_id, day_id, p_idx) for p_idx in period_indices):
                        available_teachers.append(t_id)
                if available_teachers:
                    new_solution[idx_to_change]["teacher"] = random.choice(available_teachers)
    
    return new_solution

def schedule_single_activity(activity, current_solution):
    """
    Schedules a single activity, given the current solution.
    Returns a list of scheduling entries for that activity.
    """
    result = []
    subgroup_ids = activity.get("subgroup_ids", [])
    subgroup_count = len(subgroup_ids)
    total_students = subgroup_count * STUDENTS_PER_SUBGROUP
    act_type = activity.get("type", "Lecture+Tutorial")
    space_req = activity.get("space_requirements", [])
    
    teacher_schedule = defaultdict(lambda: defaultdict(set))
    room_schedule = defaultdict(lambda: defaultdict(set))
    for item in current_solution:
        t_id = item["teacher"]
        r_code = item["room"]["code"]
        d_id = item["day"]["_id"]
        for p in item["period"]:
            teacher_schedule[t_id][d_id].add(p["index"])
            room_schedule[r_code][d_id].add(p["index"])
    
    valid_rooms = [r for r in facilities if is_space_suitable(r, act_type, space_req)]
    valid_rooms.sort(key=lambda r: r["capacity"], reverse=True)
    if not valid_rooms:
        return result
    
    valid_non_interval_periods = [p for p in periods if not p.get("is_interval", False)]
    teacher_ids = activity.get("teacher_ids", [])
    random.shuffle(teacher_ids)
    
    need_to_split = (act_type == "Lab") and any(r["capacity"] < total_students for r in valid_rooms)
    
    if not need_to_split:
        suitable_rooms = [r for r in valid_rooms if r["capacity"] >= total_students]
        if not suitable_rooms:
            return result
        scheduled = False
        for t_id in teacher_ids:
            if scheduled:
                break
            random_days = random.sample(days, len(days))
            for day in random_days:
                day_id = day["_id"]
                for room in suitable_rooms:
                    free_periods = []
                    for p in valid_non_interval_periods:
                        idx = p["index"]
                        if (idx not in teacher_schedule[t_id][day_id] and
                            idx not in room_schedule[room["code"]][day_id] and
                            get_teacher_availability(t_id, day_id, idx)):
                            free_periods.append(p)
                    blocks = find_consecutive_periods(activity["duration"], free_periods)
                    if blocks:
                        chosen_block = random.choice(blocks)
                        result.append({
                            "session_id" : str(uuid.uuid4()),
                            "subgroup": subgroup_ids,
                            "activity_id": activity["code"],
                            "day": day,
                            "period": chosen_block,
                            "room": room,
                            "teacher": t_id,
                            "duration": activity["duration"],
                            "subject": activity["subject"],
                            "student_count": total_students,
                            "activity_type": act_type
                        })
                        scheduled = True
                        break
                if scheduled:
                    break
        return result
    else:
        lab_rooms = [r for r in valid_rooms if r["capacity"] <= 60 and is_space_suitable(r, "Lab", ["Lab Room"])]
        if not lab_rooms:
            return result
        subgroup_scheduled = [False] * len(subgroup_ids)
        for i, sg in enumerate(subgroup_ids):
            if subgroup_scheduled[i]:
                continue
            random.shuffle(teacher_ids)
            for t_id in teacher_ids:
                if subgroup_scheduled[i]:
                    break
                random_days = random.sample(days, len(days))
                for day in random_days:
                    day_id = day["_id"]
                    random_labs = random.sample(lab_rooms, len(lab_rooms))
                    for r in random_labs:
                        free_periods = []
                        for p in valid_non_interval_periods:
                            idx = p["index"]
                            if (idx not in teacher_schedule[t_id][day_id] and
                                idx not in room_schedule[r["code"]][day_id] and
                                get_teacher_availability(t_id, day_id, idx)):
                                free_periods.append(p)
                        blocks = find_consecutive_periods(activity["duration"], free_periods)
                        if blocks:
                            chosen_block = random.choice(blocks)
                            result.append({
                                "session_id" : str(uuid.uuid4()),
                                "subgroup": [sg],
                                "activity_id": activity["code"],
                                "day": day,
                                "period": chosen_block,
                                "room": r,
                                "teacher": t_id,
                                "duration": activity["duration"],
                                "subject": activity["subject"],
                                "student_count": STUDENTS_PER_SUBGROUP,
                                "activity_type": act_type,
                                "is_split": True
                            })
                            subgroup_scheduled[i] = True
                            for p_obj in chosen_block:
                                p_idx = p_obj["index"]
                                teacher_schedule[t_id][day_id].add(p_idx)
                                room_schedule[r["code"]][day_id].add(p_idx)
                            break
        return result

########################################
# BCO PHASES
########################################

food_sources = []         # Each is a complete timetable solution
food_source_fitness = []  # Fitness of each food source
food_source_trials = []   # Trials (number of times no improvement) for each source
best_solution = None
best_fitness = float('inf')

def initialize_food_sources():
    """
    Initialize the employed bees' food sources.
    """
    global food_sources, food_source_fitness, food_source_trials, best_solution, best_fitness
    food_sources = []
    food_source_fitness = []
    food_source_trials = []
    best_solution = None
    best_fitness = float('inf')
    
    for i in range(NUM_EMPLOYED_BEES):
        sol = construct_solution()
        hc, sc, *_ = evaluate_solution(sol)
        fit = hc + sc
        food_sources.append(sol)
        food_source_fitness.append(fit)
        food_source_trials.append(0)
        if fit < best_fitness:
            best_fitness = fit
            best_solution = sol
            print(f"New best solution during initialization! Fitness = {best_fitness}")
            
def employed_bee_phase():
    """
    Employed bees search in the neighborhood of their current food source.
    """
    global food_sources, food_source_fitness, food_source_trials, best_solution, best_fitness
    for i in range(NUM_EMPLOYED_BEES):
        neighbor = neighborhood_search(food_sources[i])
        hc, sc, *_ = evaluate_solution(neighbor)
        neighbor_fit = hc + sc
        if neighbor_fit < food_source_fitness[i]:
            food_sources[i] = neighbor
            food_source_fitness[i] = neighbor_fit
            food_source_trials[i] = 0
            if neighbor_fit < best_fitness:
                best_fitness = neighbor_fit
                best_solution = neighbor
                print(f"New best solution in employed bee phase! Fitness = {best_fitness}")
        else:
            food_source_trials[i] += 1

def onlooker_bee_phase():
    """
    Onlooker bees choose a food source based on selection probability 
    and explore around that source (neighborhood search).
    """
    global food_sources, food_source_fitness, food_source_trials, best_solution, best_fitness
    max_fitness = max(food_source_fitness) + 1
    inverted_fitness = [max_fitness - f for f in food_source_fitness]
    total_inv_fit = sum(inverted_fitness)
    if total_inv_fit == 0:
        probabilities = [1.0 / NUM_EMPLOYED_BEES] * NUM_EMPLOYED_BEES
    else:
        probabilities = [val / total_inv_fit for val in inverted_fitness]
    for _ in range(NUM_ONLOOKER_BEES):
        selected_idx = np.random.choice(NUM_EMPLOYED_BEES, p=probabilities)
        neighbor = neighborhood_search(food_sources[selected_idx])
        hc, sc, *_ = evaluate_solution(neighbor)
        neighbor_fit = hc + sc
        if neighbor_fit < food_source_fitness[selected_idx]:
            food_sources[selected_idx] = neighbor
            food_source_fitness[selected_idx] = neighbor_fit
            food_source_trials[selected_idx] = 0
            if neighbor_fit < best_fitness:
                best_fitness = neighbor_fit
                best_solution = neighbor
                print(f"New best solution in onlooker bee phase! Fitness = {best_fitness}")
        else:
            food_source_trials[selected_idx] += 1

def scout_bee_phase():
    """
    Scout bees abandon food sources that haven't improved for too long and replace them with new random solutions.
    """
    global food_sources, food_source_fitness, food_source_trials, best_solution, best_fitness
    for i in range(NUM_EMPLOYED_BEES):
        if food_source_trials[i] > LIMIT:
            print(f"Scout bee abandoning food source {i} after {food_source_trials[i]} trials.")
            new_sol = construct_solution()
            hc, sc, *_ = evaluate_solution(new_sol)
            new_fit = hc + sc
            food_sources[i] = new_sol
            food_source_fitness[i] = new_fit
            food_source_trials[i] = 0
            if new_fit < best_fitness:
                best_fitness = new_fit
                best_solution = new_sol
                print(f"New best solution in scout bee phase! Fitness = {best_fitness}")

########################################
# MAIN BCO FUNCTION
########################################

def generate_bco():
    """
    Main function to run Bee Colony Optimization for timetable scheduling.
    """
    global best_solution, best_fitness
    get_data()
    initialize_food_sources()
    for iteration in range(NUM_ITERATIONS):
        print(f"\n=== BCO Iteration {iteration + 1} ===")
        employed_bee_phase()
        onlooker_bee_phase()
        scout_bee_phase()
        print(f"End of iteration {iteration + 1} | Current Best Fitness = {best_fitness}")
    print("\n=== Final Best Solution ===")
    print_solution_stats(best_solution)
    return best_solution
