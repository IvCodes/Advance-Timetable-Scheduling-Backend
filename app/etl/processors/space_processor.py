# app/etl/processors/space_processor.py
import pandas as pd
import json
from fastapi import UploadFile
from app.models.space_model import Space
from typing import List, Dict, Any

async def process(file: UploadFile) -> Dict[str, Any]:
    """Process space data from uploaded file"""
    # Read file based on extension
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file.file)
    else:  # Excel file
        df = pd.read_excel(file.file)
    
    # Basic data cleaning
    df = df.fillna('')
    
    # Transform data to match model
    spaces = []
    for _, row in df.iterrows():
        # Convert row to dictionary
        space_data = row.to_dict()
        
        # Handle attributes field (convert from string to dict if needed)
        if isinstance(space_data.get('attributes'), str):
            try:
                # Try parsing as JSON
                if space_data['attributes']:
                    space_data['attributes'] = json.loads(space_data['attributes'])
                else:
                    space_data['attributes'] = {}
            except json.JSONDecodeError:
                # If not valid JSON, try comma-separated key-value pairs
                attributes = {}
                if space_data['attributes']:
                    pairs = space_data['attributes'].split(',')
                    for pair in pairs:
                        if ':' in pair:
                            key, value = pair.split(':', 1)
                            attributes[key.strip()] = value.strip()
                space_data['attributes'] = attributes
        
        spaces.append(space_data)
    
    # Validate data (simplified for now)
    errors = []
    valid_count = 0
    invalid_count = 0
    
    for i, space in enumerate(spaces):
        row_errors = []
        
        # Check required fields
        if not space.get('name'):
            row_errors.append({'row': i+2, 'field': 'name', 'message': 'Space name is required'})
        
        if not space.get('long_name'):
            row_errors.append({'row': i+2, 'field': 'long_name', 'message': 'Space long name is required'})
            
        if not space.get('code'):
            row_errors.append({'row': i+2, 'field': 'code', 'message': 'Space code is required'})
        elif not space['code'].match(r"^[A-Z0-9]{3,10}$"):
            row_errors.append({'row': i+2, 'field': 'code', 'message': 'Space code must be 3-10 uppercase letters or numbers'})
        
        if not space.get('capacity') or not isinstance(space['capacity'], (int, float)) or space['capacity'] <= 0:
            row_errors.append({'row': i+2, 'field': 'capacity', 'message': 'Space capacity must be a positive number'})
        
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
    
    # Insert valid spaces into database
    # (Implementation would depend on your database access pattern)
    
    return {
        'success': True,
        'message': f"Successfully processed {len(spaces)} spaces",
        'inserted_count': len(spaces)
    }