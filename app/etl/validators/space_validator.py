# app/etl/validators/space_validator.py
import re
import json
from typing import List, Dict, Any

def validate_spaces(spaces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a list of space data dictionaries
    
    Returns:
        Dict with keys:
        - valid: bool, True if all spaces are valid
        - errors: List of error dictionaries with row, field, and message
        - valid_count: Number of valid spaces
        - invalid_count: Number of invalid spaces
    """
    errors = []
    valid_count = 0
    invalid_count = 0
    
    # Track codes to check for duplicates
    seen_codes = set()
    
    for i, space in enumerate(spaces):
        row_errors = []
        
        # Check required fields
        if not space.get('name'):
            row_errors.append({'row': i+2, 'field': 'name', 'message': 'Space name is required'})
        
        if not space.get('long_name'):
            row_errors.append({'row': i+2, 'field': 'long_name', 'message': 'Space long name is required'})
            
        # Check code field
        if not space.get('code'):
            row_errors.append({'row': i+2, 'field': 'code', 'message': 'Space code is required'})
        elif not isinstance(space['code'], str) or not re.match(r"^[A-Z0-9]{3,10}$", space['code']):
            row_errors.append({
                'row': i+2, 
                'field': 'code', 
                'message': 'Space code must be 3-10 uppercase letters or numbers'
            })
        elif space['code'] in seen_codes:
            row_errors.append({'row': i+2, 'field': 'code', 'message': f'Duplicate space code: {space["code"]}'})
        else:
            seen_codes.add(space['code'])
        
        # Check capacity
        if not space.get('capacity'):
            row_errors.append({'row': i+2, 'field': 'capacity', 'message': 'Space capacity is required'})
        else:
            try:
                capacity = int(space['capacity'])
                if capacity <= 0:
                    row_errors.append({'row': i+2, 'field': 'capacity', 'message': 'Space capacity must be greater than 0'})
            except (ValueError, TypeError):
                row_errors.append({'row': i+2, 'field': 'capacity', 'message': 'Space capacity must be a number'})
        
        # Validate attributes if present
        if space.get('attributes'):
            if isinstance(space['attributes'], str):
                try:
                    # Try to parse as JSON
                    json.loads(space['attributes'])
                except json.JSONDecodeError:
                    # Check if it's in the format "key1:value1,key2:value2"
                    if not all(':' in pair for pair in space['attributes'].split(',') if pair.strip()):
                        row_errors.append({
                            'row': i+2, 
                            'field': 'attributes', 
                            'message': 'Attributes must be a valid JSON string or comma-separated key:value pairs'
                        })
        
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