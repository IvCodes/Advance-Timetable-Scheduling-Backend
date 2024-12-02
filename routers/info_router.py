from fastapi import APIRouter, HTTPException, Depends, status
from models.info_model import UniversityInfo, PeriodOfOperation, DayOfOperation
from utils.database import db
from typing import List
from fastapi.security import OAuth2PasswordBearer
from routers.user_router import get_current_user

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
        raise HTTPException(status_code=404, detail="University information not found.")
    return university_info


@router.post("/days", response_model=List[DayOfOperation])
async def add_days_of_operation(days: List[DayOfOperation], current_user: dict = Depends(get_admin_role)):
    for day in days:
        existing_day = db["days_of_operation"].find_one({"name": day.name})
        if existing_day:
            raise HTTPException(status_code=400, detail=f"Day {day.name} already exists.")
    
    db["days_of_operation"].insert_many([day.dict() for day in days])
    return days


@router.get("/days", response_model=List[DayOfOperation])
async def get_days_of_operation(current_user: dict = Depends(get_admin_role)):
    days = list(db["days_of_operation"].find())
    return days


@router.put("/days", response_model=List[DayOfOperation])
async def update_days_of_operation(days: List[DayOfOperation], current_user: dict = Depends(get_admin_role)):
    updated_days = []
    for day in days:
        result = db["days_of_operation"].update_one(
            {"name": day.name}, {"$set": day.dict()}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Day {day.name} not found.")
        updated_days.append(day)
    return updated_days


@router.delete("/days", response_model=List[str])
async def delete_days_of_operation(day_names: List[str], current_user: dict = Depends(get_admin_role)):
    deleted_days = []
    for day_name in day_names:
        result = db["days_of_operation"].delete_one({"name": day_name})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"Day {day_name} not found.")
        deleted_days.append(day_name)
    return {"message": f"Days {', '.join(deleted_days)} deleted successfully"}


@router.post("/periods", response_model=List[PeriodOfOperation])
async def add_periods_of_operation(periods: List[PeriodOfOperation], current_user: dict = Depends(get_admin_role)):
    for period in periods:
        existing_period = db["periods_of_operation"].find_one({"name": period.name})
        if existing_period:
            raise HTTPException(status_code=400, detail=f"Period {period.name} already exists.")
    
    db["periods_of_operation"].insert_many([period.dict() for period in periods])
    return periods


@router.get("/periods", response_model=List[PeriodOfOperation])
async def get_periods_of_operation(current_user: dict = Depends(get_admin_role)):
    periods = list(db["periods_of_operation"].find())
    return periods


@router.put("/periods", response_model=List[PeriodOfOperation])
async def update_periods_of_operation(periods: List[PeriodOfOperation], current_user: dict = Depends(get_admin_role)):
    updated_periods = []
    for period in periods:
        result = db["periods_of_operation"].update_one(
            {"name": period.name}, {"$set": period.dict()}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Period {period.name} not found.")
        updated_periods.append(period)
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
