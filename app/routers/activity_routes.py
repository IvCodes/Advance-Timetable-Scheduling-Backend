from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.activity_model import Activity
from app.utils.database import db
from app.routers.user_router import get_current_user

router = APIRouter()

@router.post("/activities", response_model=Activity)
async def create_activity(activity: Activity, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    # Check if the activity code is unique
    existing_activity = db["Activities"].find_one({"code": activity.code})
    if existing_activity:
        raise HTTPException(status_code=400, detail="Activity code must be unique")

    # Use model_dump instead of model_dump (Pydantic v2 change)
    activity_data = activity.model_dump()
    
    # Ensure we have all required fields with defaults
    if 'activity_type' not in activity_data or not activity_data['activity_type']:
        activity_data['activity_type'] = "lecture"
        
    if 'duration' not in activity_data or not activity_data['duration']:
        activity_data['duration'] = 1
        
    if 'teacher_ids' not in activity_data or not activity_data['teacher_ids']:
        activity_data['teacher_ids'] = ["FAC0000001"]
        
    # Insert the activity into the database
    db["Activities"].insert_one(activity_data)
    return activity

@router.get("/activities", response_model=List[Activity])
async def get_all_activities(current_user: dict = Depends(get_current_user)):
    activities = list(db["Activities"].find())
    processed_activities = []
    
    for activity in activities:
        # Ensure all required fields exist
        if 'code' not in activity:
            activity['code'] = f"ACT{len(processed_activities):03d}"
        
        if 'name' not in activity:
            activity['name'] = f"Activity {len(processed_activities)}"
            
        if 'subject' not in activity:
            activity['subject'] = "UNKNOWN"
            
        if 'activity_type' not in activity:
            activity['activity_type'] = "lecture"  # Default type
            
        if 'duration' not in activity:
            activity['duration'] = 1  # Default duration
            
        if 'teacher_ids' not in activity:
            activity['teacher_ids'] = ["FAC0000001"]  # Default teacher
            
        processed_activities.append(Activity(**activity))
        
    return processed_activities

@router.get("/activities/{activity_code}", response_model=Activity)
async def get_activity(activity_code: str, current_user: dict = Depends(get_current_user)):
    activity = db["Activities"].find_one({"code": activity_code})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Ensure all required fields exist
    if 'code' not in activity:
        activity['code'] = activity_code
    
    if 'name' not in activity:
        activity['name'] = f"Activity {activity_code}"
        
    if 'subject' not in activity:
        activity['subject'] = "UNKNOWN"
        
    if 'activity_type' not in activity:
        activity['activity_type'] = "lecture"  # Default type
        
    if 'duration' not in activity:
        activity['duration'] = 1  # Default duration
        
    if 'teacher_ids' not in activity:
        activity['teacher_ids'] = ["FAC0000001"]  # Default teacher
    
    return Activity(**activity)

@router.put("/activities/{activity_code}", response_model=Activity)
async def update_activity(activity_code: str, updated_activity: Activity, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    existing_activity = db["Activities"].find_one({"code": activity_code})
    if not existing_activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Use model_dump instead of dict (Pydantic v2 change)
    activity_data = updated_activity.model_dump()
    
    # Ensure required fields have valid values
    if 'activity_type' not in activity_data or not activity_data['activity_type']:
        activity_data['activity_type'] = "lecture"
        
    if 'duration' not in activity_data or not activity_data['duration']:
        activity_data['duration'] = 1
        
    if 'teacher_ids' not in activity_data or not activity_data['teacher_ids']:
        activity_data['teacher_ids'] = ["FAC0000001"]

    db["Activities"].update_one({"code": activity_code}, {"$set": activity_data})
    return updated_activity

@router.delete("/activities/{activity_code}")
async def delete_activity(activity_code: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    activity = db["Activities"].find_one({"code": activity_code})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    db["Activities"].delete_one({"code": activity_code})
    return {"message": "Activity deleted successfully"}
