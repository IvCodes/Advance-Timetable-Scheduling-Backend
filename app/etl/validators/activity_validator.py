# app/etl/validators/activity_validator.py
import re
from typing import List, Dict, Any

def validate_activities(activities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a list of activity data dictionaries
    
    Returns:
        Dict with keys:
        - valid: bool, True if all activities are valid
        - errors: List of error dictionaries with row, field, and message
        - valid_count: Number of valid activities
        - invalid_count: Number of invalid activities
    """
    errors = []
    valid_count = 0
    invalid_count = 0
    
    for i, activity in enumerate(activities):
        row_errors = []
        
        # Check required fields
        if not activity.get('code'):
            row_errors.append({'row': i+2, 'field': 'code', 'message': 'Activity code is required'})
        elif not re.match(r'^AC-\d{3}$', str(activity['code'])):
            row_errors.append({'row': i+2, 'field': 'code', 'message': 'Activity code must match format AC-XXX (e.g., AC-001)'})
            
        if not activity.get('name'):
            row_errors.append({'row': i+2, 'field': 'name', 'message': 'Activity name is required'})
            
        if not activity.get('subject'):
            row_errors.append({'row': i+2, 'field': 'subject', 'message': 'Subject code is required'})
            
        if not activity.get('activity_type'):
            row_errors.append({'row': i+2, 'field': 'activity_type', 'message': 'Activity type is required'})
            
        # Check duration
        if not activity.get('duration'):
            row_errors.append({'row': i+2, 'field': 'duration', 'message': 'Duration is required'})
        else:
            try:
                duration = int(activity['duration'])
                if duration <= 0:
                    row_errors.append({'row': i+2, 'field': 'duration', 'message': 'Duration must be a positive integer'})
            except (ValueError, TypeError):
                row_errors.append({'row': i+2, 'field': 'duration', 'message': 'Duration must be a number'})
                
        # Check teacher_ids
        if not activity.get('teacher_ids') or not activity['teacher_ids']:
            row_errors.append({'row': i+2, 'field': 'teacher_ids', 'message': 'At least one teacher ID is required'})
            
        # Check subgroup_ids
        if not activity.get('subgroup_ids') or not activity['subgroup_ids']:
            row_errors.append({'row': i+2, 'field': 'subgroup_ids', 'message': 'At least one subgroup ID is required'})
        
        if row_errors:
            errors.extend(row_errors)
            invalid_count += 1
        else:
            valid_count += 1
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'valid_count': valid_count,
        'invalid_count': invalid_count
    }