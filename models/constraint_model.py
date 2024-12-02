from pydantic import BaseModel, model_validator
from typing import List, Optional

class Applicability(BaseModel):
    teachers: Optional[List[str]] = []
    students: Optional[List[str]] = []
    activities: Optional[List[str]] = []
    spaces: Optional[List[str]] = []
    all_teachers: Optional[bool] = False
    all_students: Optional[bool] = False
    all_activities: Optional[bool] = False

    @model_validator
    def validate_applicability(cls, values):
        if not any(values.values()):
            raise ValueError("At least one applicability list must be non-empty.")
        return values
