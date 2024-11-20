from fastapi import APIRouter, HTTPException, Depends
from models.faculty_model import Faculty
from database import db
from typing import List
from routers.user_router import get_current_user

router = APIRouter()


def get_admin_role(current_user: dict = Depends(get_current_user)):
    print(current_user)
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="You don't have permission to perform this action.")
    return current_user


@router.post("/faculties", response_model=Faculty)
async def add_faculty(faculty: Faculty, current_user: dict = Depends(get_admin_role)):
    existing_faculty = db["faculties"].find_one({"code": faculty.code})
    if existing_faculty:
        raise HTTPException(status_code=400, detail=f"Faculty with code {faculty.code} already exists.")
    
    db["faculties"].insert_one(faculty.model_dump())
    return faculty


@router.get("/faculties", response_model=List[Faculty])
async def get_faculties():
    faculties = list(db["faculties"].find())
    return faculties


@router.put("/faculties/{faculty_code}", response_model=Faculty)
async def update_faculty(faculty_code: str, faculty: Faculty, current_user: dict = Depends(get_admin_role)):
    result = db["faculties"].update_one(
        {"code": faculty_code}, {"$set": faculty.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Faculty with code {faculty_code} not found.")
    return faculty


@router.delete("/faculties/{faculty_code}")
async def delete_faculty(faculty_code: str, current_user: dict = Depends(get_admin_role)):
    result = db["faculties"].delete_one({"code": faculty_code})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Faculty with code {faculty_code} not found.")
    return {"message": f"Faculty with code {faculty_code} deleted successfully"}
