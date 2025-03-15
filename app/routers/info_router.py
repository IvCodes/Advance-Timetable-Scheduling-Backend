from fastapi import APIRouter, HTTPException, Depends, status
from pymongo import ReplaceOne
from app.models.info_model import UniversityInfo, PeriodOfOperation, DayOfOperation
from app.utils.database import db
from typing import List
from fastapi.security import OAuth2PasswordBearer
from app.routers.user_router import get_current_user

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_admin_role(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="You don't have permission to perform this action.")
    return current_user

@router.get("/university", response_model=UniversityInfo)
async def get_university_info(current_user: dict = Depends(get_admin_role)):
    university_info = db["university_info"].find_one()
    if not university_info:
        raise HTTPException(status_code=404, detail="University information not found.")
    return university_info


@router.put("/university", response_model=UniversityInfo)
async def update_university_info(university_info: UniversityInfo, current_user: dict = Depends(get_admin_role)):
    result = db["university_info"].update_one(
        {}, {"$set": university_info.dict()}
    )
    if result.matched_count == 0:
        db["university_info"].insert_one(university_info.model_dump())
    return university_info


@router.post("/days", response_model=List[DayOfOperation])
async def add_days_of_operation(days: List[DayOfOperation], current_user: dict = Depends(get_admin_role)):
    days_collection = db["days_of_operation"]
    existing_days = list(days_collection.find())
    existing_days = {day['name'] for day in existing_days}

    print("Existing days: ", existing_days)
    print("New days: ", {day.name for day in days})

    for day in days:
        if day.name not in existing_days:
            days_collection.insert_one(day.model_dump())
    
    for day in existing_days:
        if day not in {day.name for day in days}:
            days_collection.delete_one({"name": day})

    return list(days_collection.find())


@router.get("/days", response_model=List[DayOfOperation])
async def get_days_of_operation():
    # Removed the authentication dependency to allow all users to access this endpoint
    days = list(db["days_of_operation"].find())
    return days




@router.post("/periods", response_model=List[PeriodOfOperation])
async def add_periods_of_operation(periods: List[PeriodOfOperation], current_user: dict = Depends(get_admin_role)):
    for period in periods:
        existing_period = db["periods_of_operation"].find_one({"name": period.name})
        if existing_period:
            raise HTTPException(status_code=400, detail=f"Period {period.name} already exists.")
    
    db["periods_of_operation"].insert_many([period.dict() for period in periods])
    return periods


@router.get("/periods", response_model=List[PeriodOfOperation])
async def get_periods_of_operation(current_user: dict = Depends(get_current_user)):
    periods = list(db["periods_of_operation"].find())
    return periods


@router.put("/periods", response_model=List[PeriodOfOperation])
async def update_periods_of_operation(periods: List[PeriodOfOperation], current_user: dict = Depends(get_admin_role)):
    collection = db["periods_of_operation"]

    existing_periods = list(collection.find())  
    existing_period_names = {period['name'] for period in existing_periods}

    updated_periods = []
    for period in periods:
        period_data = period.model_dump()
        if period.name not in existing_period_names:
            collection.insert_one(period_data) 
        else:
            collection.replace_one({"name": period.name}, period_data)  
        updated_periods.append(period)

    incoming_period_names = {period.name for period in periods}
    for period in existing_periods:
        if period['name'] not in incoming_period_names:
            collection.delete_one({"name": period['name']})

    return updated_periods


@router.delete("/periods", response_model=List[str])
async def delete_periods_of_operation(period_names: List[str], current_user: dict = Depends(get_admin_role)):
    deleted_periods = []
    for period_name in period_names:
        result = db["periods_of_operation"].delete_one({"name": period_name})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"Period {period_name} not found.")
        deleted_periods.append(period_name)
    return {"message": f"Periods {', '.join(deleted_periods)} deleted successfully"}
