# app/etl/processors/activity_processor.py
import pandas as pd
import openpyxl as xl
from fastapi import UploadFile
from app.models.activity_model import Activity
from app.etl.validators.activity_validator import validate_activities
from typing import List, Dict, Any

async def process(file: UploadFile) -> Dict[str, Any]:
    """Process activity data from uploaded file"""
    # Read file based on extension
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file.file)
    else:  # Excel file
        df = pd.read_excel(file.file)
    
    # Basic data cleaning
    df = df.fillna('')
    
    # Transform data to match model
    activities = []
    for _, row in df.iterrows():
        # Convert row to dictionary
        activity_data = row.to_dict()
        
        # Handle list fields (teacher_ids, subgroup_ids)
        if isinstance(activity_data['teacher_ids'], str):
            activity_data['teacher_ids'] = [id.strip() for id in activity_data['teacher_ids'].split(',') if id.strip()]
            
        if isinstance(activity_data['subgroup_ids'], str):
            activity_data['subgroup_ids'] = [id.strip() for id in activity_data['subgroup_ids'].split(',') if id.strip()]
        
        activities.append(activity_data)
    
    # Validate data
    validation_result = validate_activities(activities)
    if not validation_result['valid']:
        return {
            'success': False,
            'errors': validation_result['errors'],
            'valid_count': validation_result['valid_count'],
            'invalid_count': validation_result['invalid_count']
        }
    
    # Insert valid activities into database
    # (Implementation would depend on your database access pattern)
    
    return {
        'success': True,
        'message': f"Successfully processed {len(activities)} activities",
        'inserted_count': len(activities)
    }