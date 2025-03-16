# app/etl/processors/module_processor.py
import pandas as pd
from fastapi import UploadFile
from app.models.module_model import Module
from typing import List, Dict, Any

async def process(file: UploadFile) -> Dict[str, Any]:
    """Process module data from uploaded file"""
    # Read file based on extension
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file.file)
    else:  # Excel file
        df = pd.read_excel(file.file)
    
    # Basic data cleaning
    df = df.fillna('')
    
    # Transform data to match model
    modules = []
    for _, row in df.iterrows():
        # Convert row to dictionary
        module_data = row.to_dict()
        modules.append(module_data)
    
    # Validate data (simplified for now)
    errors = []
    valid_count = 0
    invalid_count = 0
    
    for i, module in enumerate(modules):
        row_errors = []
        
        # Check required fields
        if not module.get('code'):
            row_errors.append({'row': i+2, 'field': 'code', 'message': 'Module code is required'})
        
        if not module.get('name'):
            row_errors.append({'row': i+2, 'field': 'name', 'message': 'Module name is required'})
            
        if not module.get('long_name'):
            row_errors.append({'row': i+2, 'field': 'long_name', 'message': 'Module long name is required'})
        
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
    
    # Insert valid modules into database
    # (Implementation would depend on your database access pattern)
    
    return {
        'success': True,
        'message': f"Successfully processed {len(modules)} modules",
        'inserted_count': len(modules)
    }