from pydantic import BaseModel, Field
from typing import List

class Activity(BaseModel):
    code: str = Field(..., pattern=r"^AC-\d{3}$") 
    name: str
    subject: str
    teacher_ids: List[str] = Field(default_factory=list)
    subgroup_ids: List[str] = Field(default_factory=list)
    duration: int = Field(..., gt=0)

    class Config:
        schema_extra = {
            "example": {
                "code": "AC-001",
                "name": "Calculus Lecture",
                "subject": "Mathematics",
                "teacher_ids": ["T001", "T002"],
                "subgroup_ids": ["SG001", "SG002"],
                "duration": 2
            }
        }
