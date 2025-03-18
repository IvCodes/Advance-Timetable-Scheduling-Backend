import numpy as np
from Data_Loading import Activity  # Import Activity class from data loading module


def _check_activity_validity(activity):
    """
    Check if an activity object is valid.
    
    Parameters:
        activity: The activity to check
        
    Returns:
        bool: True if valid, False otherwise
    """
    return activity is not None and isinstance(activity, Activity)


def _check_group_ids_validity(activity):
    """
    Check if an activity's group IDs are valid.
    
    Parameters:
        activity: The activity to check
        
    Returns:
        bool: True if valid, False otherwise
    """
    return hasattr(activity, 'group_ids') and isinstance(activity.group_ids, list)


def _process_activity(activity, activity_id, room, slot, prof_set, sub_group_set, activities_set, 
                      groups_dict, spaces_dict, vacant_rooms):
    """
    Helper function to process a single activity and check constraint violations.
    
    Returns:
        tuple: (room_is_vacant, prof_conflict, room_size_conflict, sub_group_conflict)
    """
    # Check if activity is valid
    if not _check_activity_validity(activity):
        vacant_rooms.append((slot, room))
        return True, 0, 0, 0
    
    # Activity is valid - add to set
    activities_set.add(activity_id)
    
    # Check lecturer conflicts
    prof_conflict = 1 if activity.teacher_id in prof_set else 0
    prof_set.add(activity.teacher_id)
    
    # Check student group conflicts
    sub_group_conflict = len(set(activity.group_ids).intersection(sub_group_set))
    
    # Calculate group size for room capacity check
    room_size_conflict = _check_room_capacity(activity, room, groups_dict, spaces_dict, sub_group_set)
    
    return False, prof_conflict, room_size_conflict, sub_group_conflict


def _check_room_capacity(activity, room, groups_dict, spaces_dict, sub_group_set):
    """
    Check if a room has enough capacity for an activity.
    
    Parameters:
        activity: The activity to check
        room: The room ID
        groups_dict: Dictionary of groups
        spaces_dict: Dictionary of spaces
        sub_group_set: Set of already scheduled groups in this slot
        
    Returns:
        int: 1 if capacity is violated, 0 otherwise
    """
    group_size = 0
    
    # Add each group's size to the total
    for group_id in activity.group_ids:
        if group_id in groups_dict:
            group_size += groups_dict[group_id].size
            sub_group_set.add(group_id)
    
    # Check if the room is big enough
    if group_size > spaces_dict[room].size:
        return 1
    
    return 0


def evaluate_hard_constraints(timetable, activities_dict, groups_dict, spaces_dict):
    """
    Evaluate hard constraints for a timetable solution.
    
    Parameters:
        timetable (dict): The timetable solution to evaluate
        activities_dict (dict): Dictionary of activities
        groups_dict (dict): Dictionary of student groups
        spaces_dict (dict): Dictionary of spaces/rooms
        
    Returns:
        tuple: Counts of different constraint violations
    """
    vacant_rooms = []
    vacant_room_count = 0
    prof_conflicts = 0
    room_size_conflicts = 0
    sub_group_conflicts = 0
    activities_set = set()

    # Process each time slot in the timetable
    for slot in timetable:
        slot_violations = _process_time_slot(
            timetable[slot], slot, activities_set, groups_dict, spaces_dict, vacant_rooms
        )
        
        # Update violation counts
        vacant_room_count += slot_violations[0]
        prof_conflicts += slot_violations[1]
        room_size_conflicts += slot_violations[2]
        sub_group_conflicts += slot_violations[3]

    # Calculate unassigned activities
    unasigned_activities = len(activities_dict) - len(activities_set)

    return (vacant_room_count, prof_conflicts, sub_group_conflicts, room_size_conflicts, unasigned_activities)


def _process_time_slot(slot_data, slot, activities_set, groups_dict, spaces_dict, vacant_rooms):
    """
    Process a single time slot to check for constraint violations.
    
    Parameters:
        slot_data (dict): The data for this time slot
        slot: The slot ID
        activities_set: Set of scheduled activities
        groups_dict: Dictionary of groups
        spaces_dict: Dictionary of spaces
        vacant_rooms: List to track vacant rooms
        
    Returns:
        tuple: Counts of different constraint violations
    """
    prof_set = set()
    sub_group_set = set()
    vacant_room_count = 0
    prof_conflicts = 0
    room_size_conflicts = 0
    sub_group_conflicts = 0
    
    # Process each room in this time slot
    for room in slot_data:
        activity = slot_data[room]
        activity_id = activity.id if _check_activity_validity(activity) else None
        
        # Process this activity
        is_vacant, prof_conflict, room_size_conflict, sub_group_conflict = _process_activity(
            activity, activity_id, room, slot, prof_set, sub_group_set, 
            activities_set, groups_dict, spaces_dict, vacant_rooms
        )
        
        # Add to violation counts
        vacant_room_count += 1 if is_vacant else 0
        prof_conflicts += prof_conflict
        room_size_conflicts += room_size_conflict
        sub_group_conflicts += sub_group_conflict
    
    return (vacant_room_count, prof_conflicts, room_size_conflicts, sub_group_conflicts)


def print_hard_constraint_results(violation_counts):
    """
    Print the results of hard constraint evaluation.
    
    Parameters:
        violation_counts (tuple): Counts of different constraint violations
    """
    vacant_room, prof_conflicts, sub_group_conflicts, room_size_conflicts, unasigned_activities = violation_counts
    
    print("\n--- Hard Constraint Evaluation Results ---")
    print(f"Vacant Rooms Count: {vacant_room}")
    print(f"Lecturer Conflict Violations: {prof_conflicts}")
    print(f"Student Group Conflict Violations: {sub_group_conflicts}")
    print(f"Room Capacity Violations: {room_size_conflicts}")
    print(f"Unassigned Activity Violations: {unasigned_activities}")

    # Final Hard Constraint Violation Score
    total_violations = prof_conflicts + sub_group_conflicts + room_size_conflicts + unasigned_activities
    print(f"\nTotal Hard Constraint Violations: {total_violations}")
    
    return total_violations


def _process_lecture_slot_data(schedule):
    """
    Process the schedule and extract lecture slot data for groups and lecturers.
    
    Parameters:
        schedule (dict): The schedule to process
        
    Returns:
        tuple: Group lecture slots, lecturer lecture slots, lecturer workload
    """
    # Initialize tracking dictionaries
    group_lecture_slots = {}
    lecturer_lecture_slots = {}
    lecturer_workload = {}
    
    # Process each activity in the schedule
    for slot, rooms in schedule.items():
        for room, activity in rooms.items():
            # Skip invalid activities
            if not _check_activity_validity(activity):
                continue
                
            if not _check_group_ids_validity(activity):
                continue
            
            # Process student groups
            _update_group_lecture_slots(activity, slot, group_lecture_slots)
            
            # Process lecturers
            _update_lecturer_data(activity, slot, lecturer_lecture_slots, lecturer_workload)
            
    return group_lecture_slots, lecturer_lecture_slots, lecturer_workload


def _update_group_lecture_slots(activity, slot, group_lecture_slots):
    """
    Update the group lecture slots dictionary.
    
    Parameters:
        activity: The activity to process
        slot: The time slot
        group_lecture_slots: Dictionary to update
    """
    for group_id in activity.group_ids:
        if group_id not in group_lecture_slots:
            group_lecture_slots[group_id] = []
        group_lecture_slots[group_id].append(slot)


def _update_lecturer_data(activity, slot, lecturer_lecture_slots, lecturer_workload):
    """
    Update lecturer-related data.
    
    Parameters:
        activity: The activity to process
        slot: The time slot
        lecturer_lecture_slots: Dictionary of lecture slots per lecturer
        lecturer_workload: Dictionary of workload per lecturer
    """
    lecturer_id = activity.teacher_id
    
    # Update lecture slots
    if lecturer_id not in lecturer_lecture_slots:
        lecturer_lecture_slots[lecturer_id] = []
    lecturer_lecture_slots[lecturer_id].append(slot)
    
    # Update workload
    if lecturer_id not in lecturer_workload:
        lecturer_workload[lecturer_id] = 0
    lecturer_workload[lecturer_id] += activity.duration


def _calculate_idle_time(lecture_slots, slots):
    """
    Calculate idle time for a set of lecture slots.
    
    Parameters:
        lecture_slots (list): List of lecture slots
        slots (list): All available time slots
        
    Returns:
        float: Normalized idle time
    """
    if not lecture_slots:
        return 0
        
    lecture_indices = sorted([slots.index(s) for s in lecture_slots])
    
    # Calculate idle time as gaps between lecture indices
    idle_time = 0
    for i in range(len(lecture_indices) - 1):
        idle_time += lecture_indices[i + 1] - lecture_indices[i] - 1
        
    # Normalize idle time
    return idle_time / (len(slots) - 1) if len(slots) > 1 else 0


def _compute_metrics(entity_dict, lecture_slots_dict, slots):
    """
    Compute fatigue, idle time, and spread metrics.
    
    Parameters:
        entity_dict: Dictionary of entities (groups or lecturers)
        lecture_slots_dict: Dictionary of lecture slots per entity
        slots: List of all time slots
    
    Returns:
        tuple: Dictionaries for fatigue, idle time, and lecture spread
    """
    fatigue = {}
    idle_time = {}
    lecture_spread = {}
    
    # Initialize metrics for each entity
    for entity_id in entity_dict:
        fatigue[entity_id] = 0
        idle_time[entity_id] = 0
        lecture_spread[entity_id] = 0
    
    # Update metrics based on lecture slots
    for entity_id, lectures in lecture_slots_dict.items():
        if entity_id in entity_dict:
            # Fatigue based on number of lectures
            fatigue[entity_id] = len(lectures)
            # Spread factor
            lecture_spread[entity_id] = len(lectures) * 2
            # Idle time
            idle_time[entity_id] = _calculate_idle_time(lectures, slots)
    
    return fatigue, idle_time, lecture_spread


def _normalize_dict(dictionary):
    """
    Normalize the values in a dictionary.
    
    Parameters:
        dictionary: Dictionary to normalize
        
    Returns:
        dict: Normalized dictionary
    """
    max_val = max(dictionary.values(), default=1)
    return {k: v / max_val if max_val else 0 for k, v in dictionary.items()}


def _calculate_workload_balance(workload_values):
    """
    Calculate workload balance factor.
    
    Parameters:
        workload_values: Array of workload values
        
    Returns:
        float: Workload balance factor
    """
    if len(workload_values) <= 1:
        return 1
        
    mean_workload = np.mean(workload_values)
    if mean_workload == 0:
        return 1
        
    # Calculate balance factor (lower variance means better balance)
    return max(0, 1 - (np.var(workload_values) / mean_workload))


def evaluate_soft_constraints(schedule, groups_dict, lecturers_dict, slots):
    """
    Evaluates the soft constraints of a given schedule.
    
    Parameters:
    - schedule (dict): The scheduled activities
    - groups_dict (dict): Dictionary of student groups
    - lecturers_dict (dict): Dictionary of lecturers
    - slots (list): Ordered list of available time slots

    Returns:
    - tuple: Individual soft constraint scores
    - final_score (float): Computed soft constraint score
    """
    # Extract lecture slot data and workload from schedule
    group_slots, lecturer_slots, lecturer_workload = _process_lecture_slot_data(schedule)
    
    # Compute metrics for student groups
    group_fatigue, group_idle_time, group_lecture_spread = _compute_metrics(
        groups_dict, group_slots, slots
    )
    
    # Compute metrics for lecturers
    lecturer_fatigue, lecturer_idle_time, lecturer_lecture_spread = _compute_metrics(
        lecturers_dict, lecturer_slots, slots
    )
    
    # Normalize all metrics
    group_fatigue = _normalize_dict(group_fatigue)
    group_idle_time = _normalize_dict(group_idle_time)
    group_lecture_spread = _normalize_dict(group_lecture_spread)
    lecturer_fatigue = _normalize_dict(lecturer_fatigue)
    lecturer_idle_time = _normalize_dict(lecturer_idle_time)
    lecturer_lecture_spread = _normalize_dict(lecturer_lecture_spread)

    # Compute lecturer workload balance
    workload_values = np.array(list(lecturer_workload.values()))
    lecturer_workload_balance = _calculate_workload_balance(workload_values)

    # Compute final metrics
    final_metrics = _compute_final_metrics(
        group_fatigue, group_idle_time, group_lecture_spread,
        lecturer_fatigue, lecturer_idle_time, lecturer_lecture_spread,
        lecturer_workload_balance
    )
    
    return final_metrics[0], final_metrics[1]


def _compute_final_metrics(group_fatigue, group_idle_time, group_lecture_spread,
                           lecturer_fatigue, lecturer_idle_time, lecturer_lecture_spread,
                           lecturer_workload_balance):
    """
    Compute final metrics and score.
    
    Returns:
        tuple: (individual_scores, final_score)
    """
    # Calculate average values
    student_fatigue_score = np.mean(list(group_fatigue.values()))
    student_idle_time_score = np.mean(list(group_idle_time.values()))
    student_lecture_spread_score = np.mean(list(group_lecture_spread.values()))
    lecturer_fatigue_score = np.mean(list(lecturer_fatigue.values()))
    lecturer_idle_time_score = np.mean(list(lecturer_idle_time.values()))
    lecturer_lecture_spread_score = np.mean(list(lecturer_lecture_spread.values()))
    
    # Calculate final score with weights
    final_score = _calculate_weighted_score(
        student_fatigue_score, student_idle_time_score, student_lecture_spread_score,
        lecturer_fatigue_score, lecturer_idle_time_score, lecturer_lecture_spread_score,
        lecturer_workload_balance
    )
    
    # Package individual scores
    individual_scores = (
        student_fatigue_score,
        student_idle_time_score,
        student_lecture_spread_score,
        lecturer_fatigue_score,
        lecturer_idle_time_score,
        lecturer_lecture_spread_score,
        lecturer_workload_balance
    )
    
    return individual_scores, final_score


def _calculate_weighted_score(student_fatigue, student_idle, student_spread,
                            lecturer_fatigue, lecturer_idle, lecturer_spread,
                            workload_balance):
    """
    Calculate weighted final score.
    
    Returns:
        float: Weighted score
    """
    return (
        student_fatigue * 0.2 +
        (1 - student_idle) * 0.2 +
        (1 - student_spread) * 0.2 +
        (1 - lecturer_fatigue) * 0.1 +
        (1 - lecturer_idle) * 0.1 +
        (1 - lecturer_spread) * 0.1 +
        workload_balance * 0.1
    )


def print_soft_constraint_results(individual_scores, final_score):
    """
    Print the results of soft constraint evaluation.
    
    Parameters:
        individual_scores (tuple): Individual soft constraint scores
        final_score (float): Final soft constraint score
    """
    (
        student_fatigue_score,
        student_idle_time_score,
        student_lecture_spread_score,
        lecturer_fatigue_score,
        lecturer_idle_time_score,
        lecturer_lecture_spread_score,
        lecturer_workload_balance
    ) = individual_scores
    
    print("\n--- Soft Constraint Evaluation Results ---")
    print(f"Student Fatigue Factor: {student_fatigue_score:.2f}")
    print(f"Student Idle Time Factor: {student_idle_time_score:.2f}")
    print(f"Student Lecture Spread Factor: {student_lecture_spread_score:.2f}")
    print(f"Lecturer Fatigue Factor: {lecturer_fatigue_score:.2f}")
    print(f"Lecturer Idle Time Factor: {lecturer_idle_time_score:.2f}")
    print(f"Lecturer Lecture Spread Factor: {lecturer_lecture_spread_score:.2f}")
    print(f"Lecturer Workload Balance Factor: {lecturer_workload_balance:.2f}")
    print(f"\nFinal Soft Constraint Score: {final_score:.2f}")


def evaluate_timetable(timetable, activities_dict, groups_dict, spaces_dict, lecturers_dict, slots, verbose=True):
    """
    Comprehensive evaluation of a timetable, including both hard and soft constraints.
    
    Parameters:
        timetable (dict): The timetable solution to evaluate
        activities_dict (dict): Dictionary of activities
        groups_dict (dict): Dictionary of student groups
        spaces_dict (dict): Dictionary of spaces/rooms
        lecturers_dict (dict): Dictionary of lecturers
        slots (list): List of time slots
        verbose (bool): Whether to print detailed results
        
    Returns:
        tuple: Hard constraint violation counts and soft constraint score
    """
    # Evaluate hard constraints
    hard_violation_counts = evaluate_hard_constraints(timetable, activities_dict, groups_dict, spaces_dict)
    
    # Evaluate soft constraints
    individual_soft_scores, soft_score = evaluate_soft_constraints(timetable, groups_dict, lecturers_dict, slots)
    
    # Print results if verbose
    if verbose:
        total_hard_violations = print_hard_constraint_results(hard_violation_counts)
        print_soft_constraint_results(individual_soft_scores, soft_score)
        
        print("\n--- Overall Evaluation ---")
        print(f"Total Hard Constraint Violations: {total_hard_violations}")
        print(f"Soft Constraint Score: {soft_score:.2f}")
    
    return hard_violation_counts, soft_score


# Test function to demonstrate usage
if __name__ == "__main__":
    from Data_Loading import spaces_dict, groups_dict, activities_dict, slots, lecturers_dict
    
    # Create a sample timetable (this is just a skeleton, would need real data to work)
    sample_timetable = {slot: {space: None for space in spaces_dict} for slot in slots}
    
    # Evaluate the sample timetable
    hard_violations, soft_score = evaluate_timetable(
        sample_timetable, activities_dict, groups_dict, spaces_dict, lecturers_dict, slots
    )
