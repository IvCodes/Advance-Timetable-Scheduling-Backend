from pydantic import BaseModel, Field, validator
from typing import List
from numpy import py 

class SubGroup(BaseModel):
    name: str
    code: str = Field(..., pattern=r"^[A-Z0-9]{3,10}$")  
    capacity: int = Field(..., ge=0)

    class Config:
        schema_extra = {
            "example": {
                "name": "Group A",
                "code": "GRP001",
                "capacity": 30
            }
        }


class Year(BaseModel):
    name: int 
    long_name: str 
    total_capacity: int = Field(..., ge=1) 
    total_students: int = 0 
    subgroups: List[SubGroup] = []

    @validator("subgroups")
    def validate_subgroups(cls, subgroups, values):
        if sum(subgroup.capacity for subgroup in subgroups) > values["total_capacity"]:
            raise ValueError("The total capacity of all subgroups exceeds the year's capacity.")
        return subgroups

    class Config:
        schema_extra = {
            "example": {
                "name": 1,
                "long_name": "First Year",
                "total_capacity": 100,
                "total_students": 0,
                "subgroups": [
                    {"name": "Group A", "code": "GRP001", "capacity": 50},
                    {"name": "Group B", "code": "GRP002", "capacity": 50}
                ]
            }
        }
