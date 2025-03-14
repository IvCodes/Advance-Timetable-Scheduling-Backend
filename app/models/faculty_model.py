from typing import Optional, List
from datetime import date
from app.models.base_model import MongoBaseModel
from pydantic import Field

class UnavailabilityRecord(MongoBaseModel):
    date: date
    reason: Optional[str] = None
    status: str = "pending"  # "pending", "approved", "denied"
    substitute_id: Optional[str] = None

class Faculty(MongoBaseModel):
    code: str
    short_name: str
    long_name: str
    unavailable_dates: List[UnavailabilityRecord] = Field(default_factory=list)
    
    model_config = {
        "populate_by_name": True
    }
