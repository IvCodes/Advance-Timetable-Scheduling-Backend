# app/etl/validators/year_validator.py
import re
from typing import List, Dict, Any

def validate_years(years: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a list of year data dictionaries
    
    Returns:
        Dict with keys:
        - valid: bool, True if all years are valid
        - errors: List of error dictionaries with row, field, and message
        - valid_count: Number of valid years
        - invalid_count: Number of invalid years
    """
    errors = []
    valid_count = 0
    invalid_count = 0
    
    # Track year names and subgroup codes to check for duplicates
    seen_year_names = set()
    seen_subgroup_codes = set()
    
    for i, year in enumerate(years):
        row_errors = []
        
        # Check required fields for year
        if not year.get('name'):
            row_errors.append({'row': i+2, 'field': 'name', 'message': 'Year name is required'})
        elif year['name'] in seen_year_names:
            # This is a warning, not an error, as we might have multiple entries for the same year
            # with different subgroups
            pass
        else:
            seen_year_names.add(year['name'])
            
        if not year.get('long_name'):
            row_errors.append({'row': i+2, 'field': 'long_name', 'message': 'Year long name is required'})
            
        # Check total capacity
        if not year.get('total_capacity'):
            row_errors.append({'row': i+2, 'field': 'total_capacity', 'message': 'Total capacity is required'})
        else:
            try:
                total_capacity = int(year['total_capacity'])
                if total_capacity <= 0:
                    row_errors.append({'row': i+2, 'field': 'total_capacity', 'message': 'Total capacity must be greater than 0'})
            except (ValueError, TypeError):
                row_errors.append({'row': i+2, 'field': 'total_capacity', 'message': 'Total capacity must be a number'})
        
        # Check subgroups
        if not year.get('subgroups') or not isinstance(year['subgroups'], list) or len(year['subgroups']) == 0:
            row_errors.append({'row': i+2, 'field': 'subgroups', 'message': 'At least one subgroup is required'})
        else:
            total_subgroup_capacity = 0
            
            for j, subgroup in enumerate(year['subgroups']):
                # Check required subgroup fields
                if not subgroup.get('name'):
                    row_errors.append({'row': i+2, 'field': f'subgroup_{j+1}_name', 'message': 'Subgroup name is required'})
                    
                # Check subgroup code
                if not subgroup.get('code'):
                    row_errors.append({'row': i+2, 'field': f'subgroup_{j+1}_code', 'message': 'Subgroup code is required'})
                elif not isinstance(subgroup['code'], str) or not re.match(r"^[A-Z0-9]{3,10}$", subgroup['code']):
                    row_errors.append({
                        'row': i+2, 
                        'field': f'subgroup_{j+1}_code', 
                        'message': 'Subgroup code must be 3-10 uppercase letters or numbers'
                    })
                elif subgroup['code'] in seen_subgroup_codes:
                    row_errors.append({
                        'row': i+2, 
                        'field': f'subgroup_{j+1}_code', 
                        'message': f'Duplicate subgroup code: {subgroup["code"]}'
                    })
                else:
                    seen_subgroup_codes.add(subgroup['code'])
                    
                # Check subgroup capacity
                if not subgroup.get('capacity'):
                    row_errors.append({'row': i+2, 'field': f'subgroup_{j+1}_capacity', 'message': 'Subgroup capacity is required'})
                else:
                    try:
                        capacity = int(subgroup['capacity'])
                        if capacity <= 0:
                            row_errors.append({
                                'row': i+2, 
                                'field': f'subgroup_{j+1}_capacity', 
                                'message': 'Subgroup capacity must be greater than 0'
                            })
                        else:
                            total_subgroup_capacity += capacity
                    except (ValueError, TypeError):
                        row_errors.append({
                            'row': i+2, 
                            'field': f'subgroup_{j+1}_capacity', 
                            'message': 'Subgroup capacity must be a number'
                        })
            
            # Check if total subgroup capacity exceeds year capacity
            if total_subgroup_capacity > 0 and year.get('total_capacity') and total_subgroup_capacity > int(year['total_capacity']):
                row_errors.append({
                    'row': i+2, 
                    'field': 'subgroups', 
                    'message': f'Total capacity of subgroups ({total_subgroup_capacity}) exceeds year capacity ({year["total_capacity"]})'
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