# app/etl/processors/module_processor.py
import pandas as pd
from fastapi import UploadFile
from app.models.module_model import Module
from app.utils.database import db
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
    try:
        # Use the MongoDB collection 'modules' from the database
        modules_collection = db['modules']
        
        # Check for existing modules with the same code
        inserted_count = 0
        updated_count = 0
        
        for module in modules:
            # Check if module with this code already exists
            existing = modules_collection.find_one({"code": module['code']})
            
            if existing:
                # Update existing module
                result = modules_collection.update_one(
                    {"code": module['code']},
                    {"$set": module}
                )
                if result.modified_count > 0:
                    updated_count += 1
            else:
                # Insert new module
                result = modules_collection.insert_one(module)
                if result.inserted_id:
                    inserted_count += 1
        
        return {
            'success': True,
            'message': f"Successfully processed {len(modules)} modules",
            'inserted_count': inserted_count,
            'updated_count': updated_count
        }
    except Exception as e:
        return {
            'success': False,
            'errors': [{'message': f"Database error: {str(e)}"}],
            'valid_count': valid_count,
            'invalid_count': 0
        }