"""
MongoDB Timetable Format Converter

This module converts the MongoDB stored timetable format to the format 
expected by the timetable_html_generator.py module.
"""

from collections import namedtuple

# Create simple namedtuples to mimic the data structures used by the HTML generator
Activity = namedtuple('Activity', ['id', 'subject', 'teacher_id', 'group_ids', 'duration'])
Group = namedtuple('Group', ['id', 'size'])
Lecturer = namedtuple('Lecturer', ['id', 'first_name', 'last_name'])
Space = namedtuple('Space', ['id', 'size'])

def _process_activity(activity_data, activity_id, activities_dict, groups_dict, lecturers_dict):
    """Process a single activity and update the respective dictionaries"""
    if not activity_data or not isinstance(activity_data, dict):
        return None
        
    # Get activity details
    teacher_id = activity_data.get('teacher_id', 'Unknown')
    group_ids = activity_data.get('group_ids', [])
    subject = activity_data.get('name', activity_id)
    duration = activity_data.get('duration', 1)  # Default duration to 1 if not provided
    
    # Create the Activity
    activity = Activity(id=activity_id, subject=subject, teacher_id=teacher_id, group_ids=group_ids, duration=duration)
    activities_dict[activity_id] = activity
    
    # Create Group objects
    for group_id in group_ids:
        if group_id not in groups_dict:
            groups_dict[group_id] = Group(id=group_id, size=40)  # Default size
    
    # Create Lecturer object
    if teacher_id not in lecturers_dict:
        first_name = "Lecturer"
        last_name = teacher_id.replace("FA", "")
        lecturers_dict[teacher_id] = Lecturer(id=teacher_id, first_name=first_name, last_name=last_name)
        
    return activity

def _process_room(room_id, spaces_dict):
    """Process a room and update the spaces dictionary"""
    if room_id not in spaces_dict:
        spaces_dict[room_id] = Space(id=room_id, size=50)  # Default size

def convert_mongodb_timetable(mongodb_timetable):
    """
    Convert MongoDB timetable format to the format expected by the timetable_html_generator
    
    The MongoDB format looks like:
    {
        "MON1": {
            "LH401": {"id": "AC-177", "teacher_id": "FA0000003", "group_ids": ["Y4S1.5"], ...},
            "LH501": {...},
            ...
        },
        "MON2": {...},
        ...
    }
    
    The expected format is a dictionary where:
    - Keys are combinations of slot and room IDs: (slot_id, room_id)
    - Values are Activity objects
    
    Returns:
        dict: A converted timetable in the format expected by the HTML generator
    """
    converted_timetable = {}
    activities_dict = {}
    groups_dict = {}
    spaces_dict = {}
    lecturers_dict = {}
    
    # Process each time slot
    for slot_id, rooms in mongodb_timetable.items():
        if not isinstance(rooms, dict):
            continue
            
        # Process each room in the time slot
        for room_id, activity_data in rooms.items():
            # Process the room
            _process_room(room_id, spaces_dict)
            
            # Process the activity
            activity_id = activity_data.get('id', f"ACT-{len(activities_dict) + 1}") if activity_data else None
            activity = _process_activity(activity_data, activity_id, activities_dict, groups_dict, lecturers_dict)
            
            # Add to the converted timetable if activity was created
            if activity:
                converted_timetable[(slot_id, room_id)] = activity
    
    return {
        'timetable': converted_timetable,
        'activities_dict': activities_dict,
        'groups_dict': groups_dict,
        'spaces_dict': spaces_dict,
        'lecturers_dict': lecturers_dict
    }

def convert_metrics_to_detailed(metrics_data):
    """
    Convert metrics data from MongoDB to a more detailed format for UI display
    
    Args:
        metrics_data: Dictionary containing metrics from MongoDB
        
    Returns:
        dict: Detailed metrics information
    """
    if not metrics_data:
        return {}
        
    # Convert basic metrics
    detailed_metrics = {
        'summary': {
            'hard_constraints': metrics_data.get('hardConstraintViolations', 0),
            'soft_constraints': metrics_data.get('softConstraintScore', 0.0),
            'unassigned_activities': metrics_data.get('unassignedActivities', 0)
        },
        'hard_constraints': {
            'room_conflicts': 0,
            'time_conflicts': 0, 
            'distribution_conflicts': 0,
            'student_conflicts': 0,
            'capacity_violations': 0
        },
        'soft_constraints': {
            'room_preferences': 0.0,
            'time_preferences': 0.0,
            'distribution_preferences': 0.0
        }
    }
    
    # If there are additional detailed metrics in stats, process them
    stats = metrics_data.get('stats', {})
    if stats and 'constraint_violations' in stats:
        violations = stats['constraint_violations']
        if 'total_counts' in violations:
            total_counts = violations['total_counts']
            
            detailed_metrics['hard_constraints'] = {
                'room_conflicts': total_counts.get('room_conflicts', 0),
                'time_conflicts': total_counts.get('time_conflicts', 0),
                'distribution_conflicts': total_counts.get('distribution_conflicts', 0),
                'student_conflicts': total_counts.get('student_conflicts', 0),
                'capacity_violations': total_counts.get('capacity_violations', 0)
            }
    
    return detailed_metrics
