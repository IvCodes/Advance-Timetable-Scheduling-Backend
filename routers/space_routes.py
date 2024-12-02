from fastapi import APIRouter, HTTPException, Depends, status
from models.space_model import Space
from database import db
from typing import List
from routers.user_router import get_current_user

router = APIRouter()

@router.post("/spaces", response_model=Space)
async def add_space(space: Space, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    existing_space = db["Spaces"].find_one({"code": space.code})
    if existing_space:
        raise HTTPException(status_code=400, detail="Space with this code already exists")
    
    db["Spaces"].insert_one(space.dict())
    return space

@router.get("/spaces", response_model=List[Space])
async def get_all_spaces(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    spaces = list(db["Spaces"].find())
    return spaces

@router.get("/spaces/{space_code}", response_model=Space)
async def get_space(space_code: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    space = db["Spaces"].find_one({"code": space_code})
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    
    return space

@router.put("/spaces/{space_code}", response_model=Space)
async def update_space(space_code: str, updated_space: Space, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = db["Spaces"].update_one({"code": space_code}, {"$set": updated_space.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Space not found")
    
    return updated_space

@router.delete("/spaces/{space_code}")
async def delete_space(space_code: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = db["Spaces"].delete_one({"code": space_code})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Space not found")
    
    return {"message": "Space deleted successfully"}
