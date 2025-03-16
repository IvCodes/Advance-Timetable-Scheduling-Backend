# app/etl/validators/module_validator.py
import re
from typing import List, Dict, Any

def validate_modules(modules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a list of module data dictionaries
    
    Returns:
        Dict with keys:
        - valid: bool, True if all modules are valid
        - errors: List of error dictionaries with row, field, and message
        - valid_count: Number of valid modules
        - invalid_count: Number of invalid modules
    """
    errors = []
    valid_count = 0
    invalid_count = 0
    
    # Track codes to check for duplicates
    seen_codes = set()
    
    for i, module in enumerate(modules):
        row_errors = []
        
        # Check required fields
        if not module.get('code'):
            row_errors.append({'row': i+2, 'field': 'code', 'message': 'Module code is required'})
        elif module['code'] in seen_codes:
            row_errors.append({'row': i+2, 'field': 'code', 'message': f'Duplicate module code: {module["code"]}'})
        else:
            seen_codes.add(module['code'])
            
        if not module.get('name'):
            row_errors.append({'row': i+2, 'field': 'name', 'message': 'Module name is required'})
            
        if not module.get('long_name'):
            row_errors.append({'row': i+2, 'field': 'long_name', 'message': 'Module long name is required'})
        
        # Check name length
        if module.get('name') and len(str(module['name'])) > 50:
            row_errors.append({'row': i+2, 'field': 'name', 'message': 'Module name must be 50 characters or less'})
            
        if module.get('long_name') and len(str(module['long_name'])) > 100:
            row_errors.append({'row': i+2, 'field': 'long_name', 'message': 'Module long name must be 100 characters or less'})
            
        # Check description length if present
        if module.get('description') and len(str(module['description'])) > 500:
            row_errors.append({'row': i+2, 'field': 'description', 'message': 'Module description must be 500 characters or less'})
        
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