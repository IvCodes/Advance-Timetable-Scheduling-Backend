from typing import Optional, List
from datetime import date, datetime
from app.models.base_model import MongoBaseModel
from pydantic import Field, BaseModel
from enum import Enum

class UnavailabilityStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"

class UnavailabilityType(str, Enum):
    SICK_LEAVE = "sick_leave"
    PERSONAL_LEAVE = "personal_leave"
    CONFERENCE = "conference"
    TRAINING = "training"
    EMERGENCY = "emergency"
    OTHER = "other"

class UnavailabilityRecord(MongoBaseModel):
    faculty_id: str
    date: date
    reason: Optional[str] = None
    unavailability_type: UnavailabilityType = UnavailabilityType.OTHER
    status: UnavailabilityStatus = UnavailabilityStatus.PENDING
    substitute_id: Optional[str] = None
    substitute_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    approved_by: Optional[str] = None  # Admin ID who approved/denied
    admin_notes: Optional[str] = None
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "faculty_id": "FA0000001",
                "date": "2025-03-15",
                "reason": "Medical appointment",
                "unavailability_type": "personal_leave",
                "status": "pending"
            }
        }
    }

class UnavailabilityRequest(BaseModel):
    faculty_id: str
    date: date
    reason: Optional[str] = None
    unavailability_type: UnavailabilityType = UnavailabilityType.OTHER

class UnavailabilityStatusUpdate(BaseModel):
    status: UnavailabilityStatus
    substitute_id: Optional[str] = None
    admin_notes: Optional[str] = None

class UnavailabilityResponse(BaseModel):
    record_id: str
    faculty_id: str
    faculty_name: str
    department: Optional[str] = None
    date: date
    reason: Optional[str] = None
    unavailability_type: UnavailabilityType
    status: UnavailabilityStatus
    substitute_id: Optional[str] = None
    substitute_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    approved_by: Optional[str] = None
    admin_notes: Optional[str] = None

class FacultyAvailabilityStats(BaseModel):
    total_requests: int
    pending_requests: int
    approved_requests: int
    denied_requests: int
    assigned_substitutes: int
