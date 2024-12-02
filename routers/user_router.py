from fastapi import APIRouter, HTTPException, Depends, status
from models.user_model import User, UserCreate, LoginModel
from utils.database import db
from passlib.context import CryptContext
from typing import List
from utils.jwt_util import create_access_token, verify_access_token
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = "TimeTableWhiz" 
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_current_user(token: str = Depends(oauth2_scheme)):
    print(token)
    payload = verify_access_token(token)
    user_id = payload.get("sub")
    user = db["Users"].find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    existing_user = db["Users"].find_one({"$or": [{"username": user.username}, {"id": user.id}, {"email": user.email}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    if user.year:
        year = db["Years"].find_one({"name": user.year})
        if not year:
            raise HTTPException(status_code=404, detail="Year not found")
        
        if user.semester and user.semester not in ["semester_1", "semester_2"]:
            raise HTTPException(status_code=400, detail="Invalid semester specified")
    user_dict = user.dict()
    user_dict["hashed_password"] = hash_password(user_dict.pop("password"))
    result = db["Users"].insert_one(user_dict)
    x = db["Users"].find_one({"_id": result.inserted_id })
    if not x:
        raise HTTPException(status_code=500, detail="Failed to create user.")
    return User(**x)

@router.post("/login")
async def login_user(credentials: LoginModel):
    try:
        user = db["Users"].find_one({"id": credentials.id})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid ID or password")
        
        if not verify_password(credentials.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid ID or password")
        
        access_token = create_access_token(data={"sub": user["id"]})
        return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during login")

@router.get("/all", response_model=List[User])
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    users = list(db["Users"].find())
    return users

@router.get("/faculty", response_model=List[User])
async def get_all_faculty(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    faculty_members = list(db["Users"].find({"role": "faculty"}))
    return faculty_members

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    user = db["Users"].find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, updated_user: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    hashed_password = hash_password(updated_user.password)
    updated_data = updated_user.dict()
    updated_data["hashed_password"] = hashed_password
    updated_data.pop("password", None)

    if "year" in updated_user:
        year = db["Years"].find_one({"name": updated_user["year"]})
        if not year:
            raise HTTPException(status_code=404, detail="Year not found")
    
    if "semester" in updated_user:
        if updated_user["semester"] not in ["semester_1", "semester_2"]:
            raise HTTPException(status_code=400, detail="Invalid semester specified")
        
    result = db["Users"].update_one({"id": user_id}, {"$set": updated_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return db["Users"].find_one({"id": user_id})

@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    result = db["Users"].delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@router.get("/", response_model=List[User])
async def list_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    users = list(db["Users"].find())
    return users

#---------------------------------------------------------------------------------------------------------------

@router.post("/{user_id}/subjects")
async def add_subjects(user_id: str, subjects: List[str], current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    user = db["Users"].find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] != "faculty":
        raise HTTPException(status_code=400, detail="Only faculty members can have subjects")

    updated_subjects = set(user.get("subjects", [])) | set(subjects)
    db["Users"].update_one({"id": user_id}, {"$set": {"subjects": list(updated_subjects)}})
    return {"message": "Subjects added successfully", "subjects": list(updated_subjects)}

@router.delete("/{user_id}/subjects/{subject_code}")
async def remove_subject(user_id: str, subject_code: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    user = db["Users"].find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] != "faculty":
        raise HTTPException(status_code=400, detail="Only faculty members can have subjects")

    updated_subjects = [subj for subj in user.get("subjects", []) if subj != subject_code]
    db["Users"].update_one({"id": user_id}, {"$set": {"subjects": updated_subjects}})
    return {"message": f"Subject {subject_code} removed successfully", "subjects": updated_subjects}

@router.put("/{user_id}/target_hours")
async def update_target_hours(user_id: str, target_hours: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    user = db["Users"].find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] != "faculty":
        raise HTTPException(status_code=400, detail="Only faculty members can have target hours")

    db["Users"].update_one({"id": user_id}, {"$set": {"target_hours": target_hours}})
    return {"message": f"Target hours updated successfully to {target_hours}"}

#---------------------------------------------------------------------------------------------------------

@router.put("/users/{user_id}/year")
async def assign_year_to_student(user_id: str, year: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    user = db["Users"].find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] != "student":
        raise HTTPException(status_code=400, detail="Year can only be assigned to students")
    valid_year = db["Years"].find_one({"name": year})
    if not valid_year:
        raise HTTPException(status_code=400, detail="Invalid year")
    db["Users"].update_one({"id": user_id}, {"$set": {"year": year}})
    return {"message": f"Year {year} assigned to user {user_id}"}

@router.delete("/users/{user_id}/year")
async def remove_year_from_student(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    user = db["Users"].find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] != "student":
        raise HTTPException(status_code=400, detail="Year can only be removed from students")
    db["Users"].update_one({"id": user_id}, {"$unset": {"year": ""}})
    return {"message": f"Year removed from user {user_id}"}
