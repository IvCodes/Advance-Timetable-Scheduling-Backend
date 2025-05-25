"""
Time Constraints for SLIIT Timetable Scheduling

This module defines time-based constraints including:
- Lunch break (12:30-13:30) - no classes scheduled
- Teaching hours (8:30 AM - 4:30 PM) on weekdays
- Weekend restrictions (no classes on weekends)
"""

def is_lunch_break_slot(slot):
    """
    Check if a slot is during lunch break (12:30-13:30).
    
    Args:
        slot (str): Slot identifier like 'MON5', 'TUE5', etc.
        
    Returns:
        bool: True if slot is during lunch break, False otherwise
    """
    if len(slot) < 4:
        return False
    
    slot_num = slot[3:]
    return slot_num == '5'  # Slot 5 is 12:30-13:30

def is_valid_teaching_slot(slot):
    """
    Check if a slot is within valid teaching hours.
    
    Args:
        slot (str): Slot identifier like 'MON1', 'TUE2', etc.
        
    Returns:
        bool: True if slot is valid for teaching, False otherwise
    """
    if len(slot) < 4:
        return False
    
    day_code = slot[:3]
    slot_num = slot[3:]
    
    # Only weekdays are allowed
    valid_days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    if day_code not in valid_days:
        return False
    
    # Valid time slots: 1-4 (morning), 6-8 (afternoon)
    # Slot 5 (12:30-13:30) is lunch break
    try:
        slot_number = int(slot_num)
        return slot_number in [1, 2, 3, 4, 6, 7, 8]
    except ValueError:
        return False

def get_blocked_slots():
    """
    Get a list of all blocked time slots (lunch break).
    
    Returns:
        list: List of slot identifiers that are blocked
    """
    blocked_slots = []
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    
    for day in days:
        blocked_slots.append(f"{day}5")  # Lunch break slot
    
    return blocked_slots

def get_valid_teaching_slots():
    """
    Get a list of all valid teaching time slots.
    
    Returns:
        list: List of slot identifiers that are valid for teaching
    """
    valid_slots = []
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    valid_slot_numbers = [1, 2, 3, 4, 6, 7, 8]  # Excluding slot 5 (lunch)
    
    for day in days:
        for slot_num in valid_slot_numbers:
            valid_slots.append(f"{day}{slot_num}")
    
    return valid_slots

def get_time_slot_info(slot):
    """
    Get human-readable time information for a slot.
    
    Args:
        slot (str): Slot identifier like 'MON1', 'TUE2', etc.
        
    Returns:
        dict: Dictionary with time information
    """
    if len(slot) < 4:
        return {'day': 'Unknown', 'time': 'Unknown', 'is_lunch': False, 'is_valid': False}
    
    day_map = {
        'MON': 'Monday',
        'TUE': 'Tuesday', 
        'WED': 'Wednesday',
        'THU': 'Thursday',
        'FRI': 'Friday',
        'SAT': 'Saturday',
        'SUN': 'Sunday'
    }
    
    time_map = {
        '1': '08:30 - 09:30',
        '2': '09:30 - 10:30',
        '3': '10:30 - 11:30', 
        '4': '11:30 - 12:30',
        '5': '12:30 - 13:30',  # Lunch break
        '6': '13:30 - 14:30',
        '7': '14:30 - 15:30',
        '8': '15:30 - 16:30'
    }
    
    day_code = slot[:3]
    slot_num = slot[3:]
    
    return {
        'day': day_map.get(day_code, 'Unknown'),
        'time': time_map.get(slot_num, 'Unknown'),
        'is_lunch': is_lunch_break_slot(slot),
        'is_valid': is_valid_teaching_slot(slot),
        'slot_number': slot_num,
        'day_code': day_code
    }

def validate_timetable_time_constraints(timetable):
    """
    Validate that a timetable respects time constraints.
    
    Args:
        timetable (dict): Timetable dictionary with slot keys
        
    Returns:
        dict: Validation results with violations and statistics
    """
    violations = []
    lunch_violations = 0
    invalid_time_violations = 0
    total_assignments = 0
    
    for slot, rooms in timetable.items():
        if not isinstance(rooms, dict):
            continue
            
        for room, activity in rooms.items():
            if activity is not None:
                total_assignments += 1
                
                # Check lunch break violation
                if is_lunch_break_slot(slot):
                    lunch_violations += 1
                    violations.append({
                        'type': 'lunch_break_violation',
                        'slot': slot,
                        'room': room,
                        'activity': getattr(activity, 'id', 'Unknown'),
                        'message': f"Activity scheduled during lunch break in {slot}"
                    })
                
                # Check invalid teaching time
                if not is_valid_teaching_slot(slot):
                    invalid_time_violations += 1
                    violations.append({
                        'type': 'invalid_time_violation',
                        'slot': slot,
                        'room': room,
                        'activity': getattr(activity, 'id', 'Unknown'),
                        'message': f"Activity scheduled outside teaching hours in {slot}"
                    })
    
    return {
        'violations': violations,
        'lunch_violations': lunch_violations,
        'invalid_time_violations': invalid_time_violations,
        'total_violations': len(violations),
        'total_assignments': total_assignments,
        'is_valid': len(violations) == 0
    }

# Constants for easy access
LUNCH_BREAK_SLOTS = get_blocked_slots()
VALID_TEACHING_SLOTS = get_valid_teaching_slots()
TEACHING_HOURS = "08:30 - 16:30"
LUNCH_BREAK_TIME = "12:30 - 13:30" 