from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional
import re
from app.models.base_model import MongoBaseModel



class User(MongoBaseModel):
    id: str
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    hashed_password: str
    position: str
    role: str
    faculty: Optional[str] = None
    subjects: Optional[List[str]] = []
    target_hours: Optional[int] = 0
    year: Optional[int] = None
    subgroup: Optional[str] = None

    @field_validator("id")
    def validate_id(cls, v, info):
        values = info.data
        if values.get("role") == "student" and not re.match(r"^ST\d{7}$", v):
            raise ValueError("Student ID must follow the format ST0000001")
        if values.get("role") == "faculty" and not re.match(r"^FA\d{7}$", v):
            raise ValueError("Faculty ID must follow the format FA0000001")
        if values.get("role") == "admin" and not re.match(r"^AD\d{7}$", v):
            raise ValueError("Admin ID must follow the format AD0000001")
        return v

    @field_validator("year")
    def validate_year(cls, v, info):
        values = info.data
        if values.get("role") == "student" and v is None:
            raise ValueError("Year must be specified for students")
        return v

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "ST0000001",
                "first_name": "Jane",
                "last_name": "Doe",
                "username": "janedoe",
                "email": "janedoe@example.com",
                "hashed_password": "hashed_password_example",
                "position": "Undergraduate",
                "role": "student",
                "year": 1,
                "subgroup": "Jan intake",
            }
        }
    }



class UserCreate(BaseModel):
    id: str
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str
    position: str
    role: str
    year: Optional[int] = None  
    subgroup: Optional[str] = None
    faculty: Optional[str] = None


    @field_validator("id")
    def validate_id(cls, v, info):
        values = info.data
        if values.get("role") == "student" and not re.match(r"^ST\d{7}$", v):
            raise ValueError("Student ID must follow the format ST0000001")
        if values.get("role") == "faculty" and not re.match(r"^FA\d{7}$", v):
            raise ValueError("Faculty ID must follow the format FA0000001")
        if values.get("role") == "admin" and not re.match(r"^AD\d{7}$", v):
            raise ValueError("Admin ID must follow the format AD0000001")
        return v
        
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "ST0000001",
                "first_name": "Jane",
                "last_name": "Doe",
                "username": "janedoe",
                "email": "janedoe@example.com",
                "password": "password123",
                "position": "Undergraduate",
                "role": "student",
                "year": 1,
                "subgroup": "Group A"
            }
        }
    }
    

class LoginModel(BaseModel):
    username: str
    password: str
    
    class Config:
        schema_extra = {
            "example": {
                "username": "admin",
                "password": "password123"
            }
        }