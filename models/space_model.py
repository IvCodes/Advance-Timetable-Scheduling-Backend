from pydantic import BaseModel, Field
from typing import Dict, Optional

class Space(BaseModel):
    name: str
    long_name: str
    code: str = Field(..., pattern=r"^[A-Z0-9]{3,10}$")
    capacity: int = Field(..., gt=0)
    attributes: Optional[Dict[str, str]] = {} 

    class Config:
        schema_extra = {
            "example": {
                "name": "LectureHall1",
                "long_name": "Main Lecture Hall",
                "code": "LH101",
                "capacity": 150,
                "attributes": {
                    "projector": "Yes",
                    "whiteboard": "Yes",
                    "air_conditioned": "No"
                }
            }
        }
