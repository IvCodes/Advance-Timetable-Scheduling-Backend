# from pydantic import BaseModel, Field
# from typing import Optional, List
# from datetime import date


# class FacultyUnavailability(BaseModel):
#     """
#     Model for tracking faculty unavailability
#     """
#     faculty_id: str
#     date: date
#     reason: Optional[str] = None
#     status: str = "pending"  # "pending", "approved", "denied"
#     substitute_id: Optional[str] = None


# class UnavailabilityRequest(BaseModel):
#     """
#     Model for requesting faculty unavailability
#     """
#     faculty_id: str
#     date: date
#     reason: Optional[str] = None


# class UnavailabilityStatusUpdate(BaseModel):
#     """
#     Model for updating unavailability status
#     """
#     status: str  # "approved" or "denied"
#     substitute_id: Optional[str] = None
