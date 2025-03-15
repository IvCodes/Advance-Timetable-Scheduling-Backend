from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Module(BaseModel):
    code: str
    name: str
    long_name: str
    description: str = ""  # Adding description field with default empty string
    semester: str
    lecture_hours: int
    tutorial_hours: int
    lab_hours: int
    has_lab: bool
    specialization: List[str]
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    class Config:
        schema_extra = {
            "example": {
                "code": "CS3030",
                "name": "ML",
                "long_name": "Machine Learning",
                "description": "This course covers machine learning concepts",
                "semester": "Y3S1",
                "lecture_hours": 2,
                "tutorial_hours": 1,
                "lab_hours": 2,
                "has_lab": True,
                "specialization": ["CS", "DS"]
            }
        }

