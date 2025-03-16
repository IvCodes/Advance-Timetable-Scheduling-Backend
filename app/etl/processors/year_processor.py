# app/etl/processors/year_processor.py
import pandas as pd
import json
from fastapi import UploadFile
from app.models.year_model import Year, SubGroup
from typing import List, Dict, Any

async def process(file: UploadFile) -> Dict[str, Any]:
    """Process year data from uploaded file"""
    # Read file based on extension
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file.file)
    else:  # Excel file
        df = pd.read_excel(file.file)
    
    # Basic data cleaning
    df = df.fillna('')
    
    # Transform data to match model
    years_dict = {}  # Use a dictionary to group subgroups by year
    
    for _, row in df.iterrows():
        # Convert row to dictionary
        row_data = row.to_dict()
        
        # Extract year data
        year_name = row_data.get('year_name')
        if not year_name and isinstance(row_data.get('name'), (int, float, str)):
            # Try to use 'name' field if 'year_name' is not present
            year_name = row_data.get('name')
            
        # Skip row if no year name
        if not year_name:
            continue
            
        # Convert to int if possible
        try:
            year_name = int(year_name)
        except (ValueError, TypeError):
            pass
            
        # Extract other year fields
        year_long_name = row_data.get('year_long_name', f'Year {year_name}')
        total_capacity = row_data.get('total_capacity', 0)
        try:
            total_capacity = int(total_capacity)
        except (ValueError, TypeError):
            total_capacity = 0
            
        # Extract subgroup data
        subgroup_name = row_data.get('subgroup_name')
        subgroup_code = row_data.get('subgroup_code')
        subgroup_capacity = row_data.get('subgroup_capacity', 0)
        
        try:
            subgroup_capacity = int(subgroup_capacity)
        except (ValueError, TypeError):
            subgroup_capacity = 0
            
        # Initialize year in dictionary if not exists
        if year_name not in years_dict:
            years_dict[year_name] = {
                'name': year_name,
                'long_name': year_long_name,
                'total_capacity': total_capacity,
                'total_students': 0,  # Default to 0
                'subgroups': []
            }
            
        # Add subgroup if data is present
        if subgroup_name and subgroup_code:
            subgroup = {
                'name': subgroup_name,
                'code': subgroup_code,
                'capacity': subgroup_capacity
            }
            years_dict[year_name]['subgroups'].append(subgroup)
    
    # Convert dictionary to list
    years = list(years_dict.values())
    
    # Validate data
    errors = []
    valid_count = 0
    invalid_count = 0
    
    for i, year in enumerate(years):
        row_errors = []
        
        # Check required fields for year
        if not year.get('name'):
            row_errors.append({'row': i+2, 'field': 'name', 'message': 'Year name is required'})
            
        if not year.get('long_name'):
            row_errors.append({'row': i+2, 'field': 'long_name', 'message': 'Year long name is required'})
            
        if year.get('total_capacity', 0) <= 0:
            row_errors.append({'row': i+2, 'field': 'total_capacity', 'message': 'Total capacity must be greater than 0'})
            
        # Check subgroups
        total_subgroup_capacity = sum(sg.get('capacity', 0) for sg in year.get('subgroups', []))
        if total_subgroup_capacity > year.get('total_capacity', 0):
            row_errors.append({
                'row': i+2, 
                'field': 'subgroups', 
                'message': f'Total capacity of subgroups ({total_subgroup_capacity}) exceeds year capacity ({year.get("total_capacity", 0)})'
            })
            
        # Check each subgroup
        for j, subgroup in enumerate(year.get('subgroups', [])):
            if not subgroup.get('name'):
                row_errors.append({'row': i+2, 'field': f'subgroup_{j+1}_name', 'message': 'Subgroup name is required'})
                
            if not subgroup.get('code'):
                row_errors.append({'row': i+2, 'field': f'subgroup_{j+1}_code', 'message': 'Subgroup code is required'})
            elif not isinstance(subgroup['code'], str) or not subgroup['code'].match(r"^[A-Z0-9]{3,10}$"):
                row_errors.append({
                    'row': i+2, 
                    'field': f'subgroup_{j+1}_code', 
                    'message': 'Subgroup code must be 3-10 uppercase letters or numbers'
                })
                
            if subgroup.get('capacity', 0) <= 0:
                row_errors.append({
                    'row': i+2, 
                    'field': f'subgroup_{j+1}_capacity', 
                    'message': 'Subgroup capacity must be greater than 0'
                })
        
        if row_errors:
            errors.extend(row_errors)
            invalid_count += 1
        else:
            valid_count += 1
    
    if errors:
        return {
            'success': False,
            'errors': errors,
            'valid_count': valid_count,
            'invalid_count': invalid_count
        }
    
    # Insert valid years into database
    # (Implementation would depend on your database access pattern)
    
    return {
        'success': True,
        'message': f"Successfully processed {len(years)} years with their subgroups",
        'inserted_count': len(years)
    }