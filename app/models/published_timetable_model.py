from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

class Source(BaseModel):
    """Source information about the timetable's origin"""
    algorithm: str  # "GA", "CO", or "RL"
    timetable_ids: List[str]  # Original document IDs for reference

class EntryModification(BaseModel):
    """Modification metadata for a timetable entry"""
    modified_at: datetime = Field(default_factory=datetime.now)
    modified_by: str  # User ID who made the change
    reason: Optional[str] = None  # Reason for modification

class TimetableEntry(BaseModel):
    """Individual timetable entry/activity"""
    day: Dict  # {name: str, long_name: str}
    period: List[Dict]  # [{name: str, start_time: str, end_time: str}]
    subject: str
    room: Dict  # {name: str, code: str}
    teacher: str
    substitute: Optional[str] = None
    original_teacher: Optional[str] = None
    duration: Optional[float] = 1.0
    modification: Optional[EntryModification] = None

class PublishedTimetable(BaseModel):
    """A published, official timetable that is active in the system"""
    version: int = 1
    status: str = "active"  # "active" or "archived"
    published_date: datetime = Field(default_factory=datetime.now)
    published_by: str  # Admin ID
    source: Source
    semesters: Dict[str, List[TimetableEntry]]  # Semester code to list of entries
    semester_map: Optional[Dict] = None  # Optional map for efficient lookups
