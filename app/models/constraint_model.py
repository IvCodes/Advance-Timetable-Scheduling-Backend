from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Union, Optional
from datetime import datetime
import re

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

class Constraint(BaseModel):
    code: str = Field(..., regex=r"^[A-Z]{2}-\d{3}$")
    type: str = Field(..., regex=r"^(time|space|miscellaneous)$")
    scope: str = Field(..., regex=r"^(teacher|student|activity|space|general)$")
    name: str
    description: Optional[str] = None
    settings: Dict[str, Union[int, str, float, bool]] = Field(default_factory=dict)
    applicability: Applicability
    weight: int = 100
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @model_validator
    def validate_constraint(cls, values):
        if not values.get("settings"):
            raise ValueError("Settings must be provided for a constraint.")
        return values
