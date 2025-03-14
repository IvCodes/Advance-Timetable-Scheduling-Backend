from pydantic import BaseModel, Field
from typing import List, Literal

class Activity(BaseModel):
    code: str = Field(..., pattern=r"^AC-\d{3}$") 
    name: str
    subject: str
    teacher_ids: List[str] = Field(default_factory=list)
    subgroup_ids: List[str] = Field(default_factory=list)
    duration: int = Field(..., gt=0)
    type: Literal['Lecture+Tutorial', 'Lab']
    space_requirements: List[str] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "code": "AC-001",
                "name": "Introduction to Programming (IT) Lecture",
                "subject": "IT1120",
                "teacher_ids": ["FA0000001"],
                "subgroup_ids": [
                    "Y1S1.IT.1",
                    "Y1S1.IT.2",
                    "Y1S1.IT.3",
                    "Y1S1.IT.4",
                    "Y1S1.IT.5",
                    "Y1S1.IT.6",
                    "Y1S1.IT.7"
                ],
                "duration": 2,
                "type": "Lecture",
                "space_requirements": ["Lecture Hall"]
            }
        }
