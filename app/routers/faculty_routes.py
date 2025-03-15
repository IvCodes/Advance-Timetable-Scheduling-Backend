from fastapi import APIRouter, HTTPException, Depends
from app.models.faculty_model import Faculty, UnavailabilityRecord
from app.utils.database import db
from typing import List, Optional
from app.routers.user_router import get_current_user
from datetime import date
from pydantic import BaseModel

router = APIRouter()

# Constants to avoid duplicated string literals
FACULTY_WITH_CODE_MSG = "Faculty with code "
FACULTY_MEMBER_WITH_ID_MSG = "Faculty member with ID "
SUBSTITUTE_FACULTY_MSG = "Substitute faculty with ID "
NOT_FOUND_MSG = " not found"
UNAVAILABILITY_RECORD_NOT_FOUND_MSG = "Unavailability record not found"


def get_admin_role(current_user: dict = Depends(get_current_user)):
    print(current_user)
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="You don't have permission to perform this action.")
    return current_user


# Request models
class UnavailabilityRequest(BaseModel):
    faculty_id: str
    date: date
    reason: Optional[str] = None

class UnavailabilityStatusUpdate(BaseModel):
    status: str  # "approved", "denied"
    substitute_id: Optional[str] = None


@router.post("/faculties", response_model=Faculty)
async def add_faculty(faculty: Faculty, current_user: dict = Depends(get_admin_role)):
    print(faculty)
    existing_faculty = db["faculties"].find_one({"code": faculty.code})
    if existing_faculty:
        raise HTTPException(status_code=400, detail=FACULTY_WITH_CODE_MSG + faculty.code + " already exists.")
    
    db["faculties"].insert_one(faculty.model_dump())
    
    faculties = list(db["faculties"].find())
    return faculties

@router.get("/faculties", response_model=List[Faculty])
async def get_faculties():
    faculties = list(db["faculties"].find())
    return faculties


@router.put("/faculties/{faculty_code}", response_model=Faculty)
async def update_faculty(faculty_code: str, faculty: Faculty, current_user: dict = Depends(get_admin_role)):
    existing_faculty = db["faculties"].find_one({"code": faculty_code})
    if existing_faculty:
        raise HTTPException(status_code=400, detail=FACULTY_WITH_CODE_MSG + faculty_code + " already exists.")
    result = db["faculties"].update_one(
        {"code": faculty_code}, {"$set": faculty.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=FACULTY_WITH_CODE_MSG + faculty_code + NOT_FOUND_MSG)
    faculties = list(db["faculties"].find())
    return faculties

@router.delete("/faculties/{faculty_code}")
async def delete_faculty(faculty_code: str, current_user: dict = Depends(get_admin_role)):
    result = db["faculties"].delete_one({"code": faculty_code})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=FACULTY_WITH_CODE_MSG + faculty_code + NOT_FOUND_MSG)
    faculties = list(db["faculties"].find())
    return faculties

# Faculty Unavailability Endpoints

@router.get("/faculty/unavailable-days/{faculty_id}", response_model=List[dict])
async def get_faculty_unavailable_days(faculty_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get all unavailable days for a faculty member
    """
    # Check if user is either an admin or the faculty member themselves
    if current_user["role"] != "admin" and current_user["id"] != faculty_id:
        raise HTTPException(status_code=403, detail="You don't have permission to view this faculty member's unavailability")
    
    # Find the faculty
    faculty = db["Users"].find_one({"id": faculty_id, "role": "faculty"})
    if not faculty:
        raise HTTPException(status_code=404, detail=FACULTY_MEMBER_WITH_ID_MSG + faculty_id + NOT_FOUND_MSG)
    
    # Return unavailable dates if they exist
    return faculty.get("unavailable_dates", [])

@router.post("/faculty/unavailable-days", response_model=dict)
async def mark_day_as_unavailable(request: UnavailabilityRequest, current_user: dict = Depends(get_current_user)):
    """
    Mark a day as unavailable for a faculty member
    """
    print(f"Received request to mark day as unavailable: {request}")
    print(f"Current user: {current_user}")
    
    faculty_id = request.faculty_id
    
    # Check if user is either an admin or the faculty member themselves
    if current_user["role"] != "admin" and current_user["id"] != faculty_id:
        raise HTTPException(status_code=403, detail="You don't have permission to update this faculty member's availability")
    
    # Find the faculty
    faculty = db["Users"].find_one({"id": faculty_id, "role": "faculty"})
    if not faculty:
        raise HTTPException(status_code=404, detail=FACULTY_MEMBER_WITH_ID_MSG + faculty_id + NOT_FOUND_MSG)
    
    # Check if this date is already marked as unavailable
    unavailable_dates = faculty.get("unavailable_dates", [])
    date_str = request.date.isoformat()
    for unavailable in unavailable_dates:
        if unavailable.get("date") == date_str:
            raise HTTPException(status_code=400, detail="This date is already marked as unavailable")
    
    # Create unavailability record - simplified with no pending approval needed
    unavailability = UnavailabilityRecord(
        date=request.date,
        reason=request.reason,
        status="approved",  # Always approved - simplified workflow
        substitute_id=None
    )
    
    # Convert to dict and ensure date is stored as string
    unavailability_dict = unavailability.model_dump()
    if isinstance(unavailability_dict['date'], date):
        unavailability_dict['date'] = unavailability_dict['date'].isoformat()
    
    # Add to faculty's unavailable dates
    unavailable_dates.append(unavailability_dict)
    
    # Update faculty record
    db["Users"].update_one(
        {"id": faculty_id},
        {"$set": {"unavailable_dates": unavailable_dates}}
    )
    
    return unavailability_dict

@router.post("/faculty/faculty/unavailable-days", response_model=dict)
async def mark_day_as_unavailable_duplicate_route(request: UnavailabilityRequest, current_user: dict = Depends(get_current_user)):
    """
    Duplicate route to handle frontend URL structure
    """
    # Override the faculty_id in the request to always use the current user's ID for security
    # This ensures faculty members can only mark their own availability
    if current_user["role"] == "faculty":
        request.faculty_id = current_user["id"]
    
    # Delegate to the main function
    return await mark_day_as_unavailable(request, current_user)

@router.delete("/faculty/unavailable-days/{faculty_id}/{unavailable_date}", response_model=dict)
async def mark_day_as_available(faculty_id: str, unavailable_date: date, current_user: dict = Depends(get_current_user)):
    """
    Remove an unavailable day (mark as available) for a faculty member
    """
    print(f"Request to mark day {unavailable_date} as available for faculty {faculty_id}")
    print(f"Current user: {current_user}")
    
    # Check if user is either an admin or the faculty member themselves
    if current_user["role"] != "admin" and current_user["id"] != faculty_id:
        raise HTTPException(status_code=403, detail="You don't have permission to update this faculty member's availability")
    
    # Find the faculty
    faculty = db["Users"].find_one({"id": faculty_id, "role": "faculty"})
    if not faculty:
        raise HTTPException(status_code=404, detail=FACULTY_MEMBER_WITH_ID_MSG + faculty_id + NOT_FOUND_MSG)
    
    # Get current unavailable dates
    unavailable_dates = faculty.get("unavailable_dates", [])
    
    # Filter out the date to be removed
    new_unavailable_dates = [
        unavailable for unavailable in unavailable_dates 
        if unavailable.get("date") != unavailable_date.isoformat()
    ]
    
    # Check if any date was removed
    if len(unavailable_dates) == len(new_unavailable_dates):
        raise HTTPException(status_code=404, detail=UNAVAILABILITY_RECORD_NOT_FOUND_MSG)
    
    # Update faculty record
    db["Users"].update_one(
        {"id": faculty_id},
        {"$set": {"unavailable_dates": new_unavailable_dates}}
    )
    
    return {"success": True, "message": "Day marked as available"}

@router.delete("/faculty/faculty/unavailable-days/{faculty_id}/{unavailable_date}", response_model=dict)
async def mark_day_as_available_duplicate_route(faculty_id: str, unavailable_date: date, current_user: dict = Depends(get_current_user)):
    """
    Duplicate route to handle frontend URL structure for DELETE
    """
    # Override faculty_id with current user's ID for faculty users (for security)
    if current_user["role"] == "faculty":
        faculty_id = current_user["id"]
    
    # Delegate to the main function
    return await mark_day_as_available(faculty_id, unavailable_date, current_user)

@router.get("/faculty/pending-unavailability", response_model=List[dict])
async def get_pending_unavailability_requests(current_user: dict = Depends(get_admin_role)):
    """
    Get all pending unavailability requests (admin only)
    """
    # Find all faculty with pending unavailability requests
    faculty_with_pending = []
    
    # Get all faculty users
    faculty_users = list(db["Users"].find({"role": "faculty"}))
    
    # Check each faculty for pending requests
    for faculty in faculty_users:
        unavailable_dates = faculty.get("unavailable_dates", [])
        pending_dates = [
            {**unavailable, "faculty_id": faculty["id"], "faculty_name": f"{faculty.get('first_name', '')} {faculty.get('last_name', '')}"}
            for unavailable in unavailable_dates
            if unavailable.get("status") == "pending"
        ]
        
        faculty_with_pending.extend(pending_dates)
    
    return faculty_with_pending

@router.put("/faculty/unavailable-days/{faculty_id}/{unavailable_date}", response_model=dict)
async def update_unavailability_status(
    faculty_id: str, 
    unavailable_date: date, 
    status_update: UnavailabilityStatusUpdate, 
    current_user: dict = Depends(get_admin_role)
):
    """
    Update the status of an unavailability request (admin only)
    """
    # Find the faculty
    faculty = db["Users"].find_one({"id": faculty_id, "role": "faculty"})
    if not faculty:
        raise HTTPException(status_code=404, detail=FACULTY_MEMBER_WITH_ID_MSG + faculty_id + NOT_FOUND_MSG)
    
    # Get current unavailable dates
    unavailable_dates = faculty.get("unavailable_dates", [])
    
    # Find the specific unavailability record
    found = False
    for i, unavailable in enumerate(unavailable_dates):
        if unavailable.get("date") == unavailable_date.isoformat():
            # Update status
            unavailable_dates[i]["status"] = status_update.status
            
            # Update substitute if provided
            if status_update.substitute_id:
                # Verify substitute exists
                substitute = db["Users"].find_one({"id": status_update.substitute_id, "role": "faculty"})
                if not substitute:
                    raise HTTPException(status_code=404, detail=SUBSTITUTE_FACULTY_MSG + status_update.substitute_id + NOT_FOUND_MSG)
                
                unavailable_dates[i]["substitute_id"] = status_update.substitute_id
            
            found = True
            updated_record = unavailable_dates[i]
            break
    
    if not found:
        raise HTTPException(status_code=404, detail=UNAVAILABILITY_RECORD_NOT_FOUND_MSG)
    
    # Update faculty record
    db["Users"].update_one(
        {"id": faculty_id},
        {"$set": {"unavailable_dates": unavailable_dates}}
    )
    
    # Format date properly before returning
    if isinstance(updated_record["date"], str):
        updated_record["date"] = date.fromisoformat(updated_record["date"])
    
    return updated_record

@router.post("/faculty/initialize-unavailable-dates", response_model=dict)
async def initialize_unavailable_dates(current_user: dict = Depends(get_admin_role)):
    """
    Initialize the unavailable_dates field for all faculty users who don't have it yet.
    This is a one-time migration endpoint.
    """
    # Get all faculty users
    faculty_users = list(db["Users"].find({"role": "faculty"}))
    
    # Track counts for reporting
    updated_count = 0
    already_initialized_count = 0
    
    # Update each faculty user
    for faculty in faculty_users:
        # Check if unavailable_dates already exists
        if "unavailable_dates" not in faculty:
            # Initialize the field with an empty list
            db["Users"].update_one(
                {"id": faculty["id"]},
                {"$set": {"unavailable_dates": []}}
            )
            updated_count += 1
        else:
            already_initialized_count += 1
    
    return {
        "success": True,
        "message": f"Migration complete. Updated {updated_count} faculty records. {already_initialized_count} records were already initialized."
    }