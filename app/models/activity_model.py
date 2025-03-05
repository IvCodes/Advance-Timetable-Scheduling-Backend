from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.base_model import MongoBaseModel, PyObjectId

class Activity(MongoBaseModel):
    """
    Activity represents a teaching or learning activity that needs to be scheduled
    """
    code: str = Field(..., description="Unique code identifying the activity")
    name: str = Field(..., description="Name of the activity")
    subject: str = Field(..., description="Module/Subject code this activity is part of")
    activity_type: str = Field(..., description="Type of activity (lecture, lab, tutorial, etc.)")
    duration: int = Field(..., description="Duration in periods")
    teacher_ids: List[str] = Field(..., description="List of teacher IDs who can teach this activity")
    subgroup_ids: List[str] = Field(default_factory=list, description="List of student subgroups that attend this activity")
    required_equipment: List[str] = Field(default_factory=list, description="Equipment needed for this activity")
    special_requirements: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "ACT001",
                "name": "Introduction to Programming",
                "subject": "CSC101",
                "activity_type": "lecture",
                "duration": 2,
                "teacher_ids": ["FAC0000001"],
                "subgroup_ids": ["SEM101"],
                "required_equipment": ["projector", "whiteboard"],
                "special_requirements": "Requires computer lab"
            }
        },
        "populate_by_name": True
    }
