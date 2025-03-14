from pydantic import BaseModel, Field, EmailStr, constr, field_validator, validator
from typing import List, Optional
from bson import ObjectId

class User(BaseModel):
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
    year_group: Optional[str] = None
    specialization : Optional[str] = None
    attend_days: Optional[str] = None  # Changed field name

    @validator("id")
    def validate_id(cls, v, values):
        if values.get("role") == "student" and not re.match(r"^IT\d{7}$", v):
            raise ValueError("Student ID must follow the format IT0000001")
        if values.get("role") == "faculty" and not re.match(r"^FA\d{7}$", v):
            raise ValueError("Faculty ID must follow the format FA0000001")
        if values.get("role") == "admin" and not re.match(r"^AD\d{7}$", v):
            raise ValueError("Admin ID must follow the format AD0000001")
        return v

    @validator("year")
    def validate_year(cls, v, values):
        if values.get("role") == "student" and v is None:
            raise ValueError("Year must be specified for students")
        return v
    

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "id": "IT0000001",
                "first_name": "Jane",
                "last_name": "Doe",
                "username": "janedoe",
                "email": "janedoe@example.com",
                "hashed_password": "hashed_password_example",
                "position": "Undergraduate",
                "role": "student",
                "year": 1,
                "subgroup": "Jan intake",
                "year_group" "Y2S2.1"
                "specialization" : "SE",
                "attend_days": "weekday"  # Example value
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
    year_group: Optional[str] = None
    faculty: Optional[str] = None
    specialization : Optional[str] = None
    attend_days: Optional[str] = None  # Changed field name

    @validator("id")
    def validate_id(cls, v, values):
        if values.get("role") == "student" and not re.match(r"^IT\d{7}$", v):
            raise ValueError("Student ID must follow the format IT0000001")
        if values.get("role") == "faculty" and not re.match(r"^FA\d{7}$", v):
            raise ValueError("Faculty ID must follow the format FA0000001")
        if values.get("role") == "admin" and not re.match(r"^AD\d{7}$", v):
            raise ValueError("Admin ID must follow the format AD0000001")
        return v


class LoginModel(BaseModel):
    id: str
    password: str


