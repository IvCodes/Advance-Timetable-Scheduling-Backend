from pydantic import Field
from typing import Dict, Optional
from app.models.base_model import MongoBaseModel

class Space(MongoBaseModel):
    name: str
    long_name: str
    code: str = Field(..., pattern=r"^[A-Z0-9]{3,10}$")
    capacity: int = Field(..., gt=0)
    attributes: Optional[Dict[str, str]] = {}

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
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
    }
