from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models.activity_model import Activity 
from utils.database import db 
from routers.user_router import get_current_user

router = APIRouter()

@router.post("/activities", response_model=Activity)
async def create_activity(activity: Activity, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    existing_activity = db["Activities"].find_one({"code": activity.code})
    if existing_activity:
        raise HTTPException(status_code=400, detail="Activity code must be unique")
    
    db["Activities"].insert_one(activity.model_dump())
    return activity

@router.get("/activities", response_model=List[Activity])
async def get_all_activities(current_user: dict = Depends(get_current_user)):
    activities = list(db["Activities"].find())
    return [Activity(**activity) for activity in activities]

@router.get("/activities/{activity_code}", response_model=Activity)
async def get_activity(activity_code: str, current_user: dict = Depends(get_current_user)):
    activity = db["Activities"].find_one({"code": activity_code})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return Activity(**activity)

@router.put("/activities/{activity_code}", response_model=Activity)
async def update_activity(activity_code: str, updated_activity: Activity, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    existing_activity = db["Activities"].find_one({"code": activity_code})
    if not existing_activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    db["Activities"].update_one({"code": activity_code}, {"$set": updated_activity.model_dump()})
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
