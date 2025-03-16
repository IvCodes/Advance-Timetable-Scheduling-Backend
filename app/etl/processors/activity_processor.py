# app/etl/processors/activity_processor.py
import pandas as pd
import openpyxl as xl
from fastapi import UploadFile
from app.models.activity_model import Activity
from app.etl.validators.activity_validator import validate_activities
from app.utils.database import db
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
        # Make sure teacher_ids exists and is a string before splitting
        if 'teacher_ids' in activity_data:
            if isinstance(activity_data['teacher_ids'], str) and activity_data['teacher_ids'].strip():
                activity_data['teacher_ids'] = [id.strip() for id in activity_data['teacher_ids'].split(',') if id.strip()]
            else:
                activity_data['teacher_ids'] = []
        else:
            activity_data['teacher_ids'] = []
            
        # Make sure subgroup_ids exists and is a string before splitting
        if 'subgroup_ids' in activity_data:
            if isinstance(activity_data['subgroup_ids'], str) and activity_data['subgroup_ids'].strip():
                activity_data['subgroup_ids'] = [id.strip() for id in activity_data['subgroup_ids'].split(',') if id.strip()]
            else:
                activity_data['subgroup_ids'] = []
        else:
            activity_data['subgroup_ids'] = []
            
        # Handle other array fields if needed
        if 'required_equipment' in activity_data:
            if isinstance(activity_data['required_equipment'], str) and activity_data['required_equipment'].strip():
                activity_data['required_equipment'] = [eq.strip() for eq in activity_data['required_equipment'].split(',') if eq.strip()]
            else:
                activity_data['required_equipment'] = []
        else:
            activity_data['required_equipment'] = []
        
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
    try:
        # Use the MongoDB collection 'Activities' from the database
        activities_collection = db['Activities']
        
        # Check for existing activities with the same code
        inserted_count = 0
        updated_count = 0
        
        for activity in activities:
            # Check if activity with this code already exists
            existing = activities_collection.find_one({"code": activity['code']})
            
            if existing:
                # Update existing activity
                result = activities_collection.update_one(
                    {"code": activity['code']},
                    {"$set": activity}
                )
                if result.modified_count > 0:
                    updated_count += 1
            else:
                # Insert new activity
                result = activities_collection.insert_one(activity)
                if result.inserted_id:
                    inserted_count += 1
        
        return {
            'success': True,
            'message': f"Successfully processed {len(activities)} activities",
            'inserted_count': inserted_count,
            'updated_count': updated_count
        }
    except Exception as e:
        return {
            'success': False,
            'errors': [{'message': f"Database error: {str(e)}"}],
            'valid_count': validation_result['valid_count'],
            'invalid_count': 0
        }