from fastapi import APIRouter, HTTPException, Depends
from app.models.year_model import Year, SubGroup
from utils.database import db
from typing import List
from app.routers.user_router import get_current_user

router = APIRouter()

@router.post("/years", response_model=Year)
async def add_year(year: Year, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    existing_year = db["Years"].find_one({"name": year.name})
    if existing_year:
        raise HTTPException(status_code=400, detail="Year already exists")
    
    existing_subgroups = db["Years"].aggregate([
        {"$unwind": "$subgroups"},
        {"$project": {"code": "$subgroups.code"}}
    ])
    existing_codes = {subgroup["code"] for subgroup in existing_subgroups}

    for subgroup in year.subgroups:
        if subgroup.code in existing_codes:
            raise HTTPException(
                status_code=400,
                detail=f"Subgroup code '{subgroup.code}' is already in use."
            )
    year_dict = year.dict()
    db["Years"].insert_one(year_dict)
    return year




@router.get("/years", response_model=List[Year])
async def list_years():
    
    years = list(db["Years"].find())
    return [Year(**year) for year in years]

@router.put("/years/{year_name}", response_model=Year)
async def update_year(year_name: int, updated_year: Year, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    existing_year = db["Years"].find_one({"name": year_name})
    if not existing_year:
        raise HTTPException(status_code=404, detail="Year not found")
    
    result = db["Years"].update_one({"name": year_name}, {"$set": updated_year.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Year update failed")
    
    return updated_year




@router.delete("/years/{year_name}")
async def delete_year(year_name: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    existing_year = db["Years"].find_one({"name": year_name})
    if not existing_year:
        raise HTTPException(status_code=404, detail="Year not found")
    
    db["Users"].update_many({"year": year_name}, {"$unset": {"year": ""}})
    result = db["Years"].delete_one({"name": year_name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete year")
    
    return {"message": "Year deleted successfully"}

@router.post("/years/{year_name}/subgroups", response_model=Year)
async def add_subgroup(year_name: int, subgroup: SubGroup, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    year = db["Years"].find_one({"name": year_name})
    if not year:
        raise HTTPException(status_code=404, detail="Year not found")

    existing_subgroups = db["Years"].aggregate([
        {"$unwind": "$subgroups"},
        {"$project": {"code": "$subgroups.code"}}
    ])
    existing_codes = {subgroup["code"] for subgroup in existing_subgroups}

    if subgroup.code in existing_codes:
        raise HTTPException(
            status_code=400,
            detail=f"Subgroup code '{subgroup.code}' is already in use."
        )

    year_obj = Year(**year)
    year_obj.subgroups.append(subgroup)
    db["Years"].update_one({"name": year_name}, {"$set": {"subgroups": [sg.dict() for sg in year_obj.subgroups]}})
    return year_obj


@router.put("/years/{year_name}/subgroups/{subgroup_code}", response_model=Year)
async def update_subgroup(year_name: int, subgroup_code: str, updated_subgroup: SubGroup, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    year = db["Years"].find_one({"name": year_name})
    if not year:
        raise HTTPException(status_code=404, detail="Year not found")
    
    year_obj = Year(**year)
    for sg in year_obj.subgroups:
        if sg.code == subgroup_code:
            sg.name = updated_subgroup.name
            sg.capacity = updated_subgroup.capacity
            break
    else:
        raise HTTPException(status_code=404, detail="Subgroup not found")
    
    if sum(sg.capacity for sg in year_obj.subgroups) > year_obj.total_capacity:
        raise HTTPException(status_code=400, detail="Total subgroup capacity exceeds the year's total capacity")
    
    db["Years"].update_one({"name": year_name}, {"$set": {"subgroups": [sg.dict() for sg in year_obj.subgroups]}})
    return year_obj




