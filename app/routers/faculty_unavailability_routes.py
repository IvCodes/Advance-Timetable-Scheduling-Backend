from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import date, datetime
import uuid
from bson import ObjectId

from app.models.faculty_unavailability_model import (
    UnavailabilityRecord, 
    UnavailabilityRequest, 
    UnavailabilityStatusUpdate, 
    UnavailabilityResponse,
    UnavailabilityStatus,
    UnavailabilityType,
    FacultyAvailabilityStats
)
from app.Services.faculty_notification_service import FacultyNotificationService
from app.utils.database import db
from app.routers.user_router import get_current_user

router = APIRouter()

def get_admin_role(current_user: dict = Depends(get_current_user)):
    """Ensure user has admin role"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="You don't have permission to perform this action.")
    return current_user

def get_faculty_role(current_user: dict = Depends(get_current_user)):
    """Ensure user has faculty role"""
    if current_user["role"] != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty members can perform this action.")
    return current_user

@router.post("/unavailability-requests", response_model=UnavailabilityResponse)
async def submit_unavailability_request(
    request: UnavailabilityRequest, 
    current_user: dict = Depends(get_current_user)
):
    """Submit a new unavailability request"""
    
    # Faculty can only submit requests for themselves
    if current_user["role"] == "faculty" and request.faculty_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Faculty can only submit requests for themselves")
    
    # Verify faculty exists
    faculty = db["Users"].find_one({"id": request.faculty_id, "role": "faculty"})
    if not faculty:
        raise HTTPException(status_code=404, detail=f"Faculty member with ID {request.faculty_id} not found")
    
    # Check if request already exists for this date
    existing_request = db["faculty_unavailability"].find_one({
        "faculty_id": request.faculty_id,
        "date": request.date.isoformat(),
        "status": {"$in": ["pending", "approved"]}
    })
    
    if existing_request:
        raise HTTPException(status_code=400, detail="An unavailability request already exists for this date")
    
    # Create unavailability record
    record = UnavailabilityRecord(
        faculty_id=request.faculty_id,
        date=request.date,
        reason=request.reason,
        unavailability_type=request.unavailability_type,
        status=UnavailabilityStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Convert to dict for MongoDB
    record_dict = record.model_dump()
    record_dict["date"] = record_dict["date"].isoformat()
    record_dict["_id"] = str(ObjectId())
    
    # Insert into database
    db["faculty_unavailability"].insert_one(record_dict)
    
    # Create notification for admins
    faculty_name = f"{faculty.get('first_name', '')} {faculty.get('last_name', '')}"
    FacultyNotificationService.create_unavailability_request_notification(
        faculty_id=request.faculty_id,
        faculty_name=faculty_name,
        date=request.date.isoformat(),
        reason=request.reason
    )
    
    # Return response
    return UnavailabilityResponse(
        record_id=record_dict["_id"],
        faculty_id=request.faculty_id,
        faculty_name=faculty_name,
        department=faculty.get("faculty"),
        date=request.date,
        reason=request.reason,
        unavailability_type=request.unavailability_type,
        status=UnavailabilityStatus.PENDING,
        created_at=record.created_at,
        updated_at=record.updated_at
    )

@router.get("/unavailability-requests", response_model=List[UnavailabilityResponse])
async def get_unavailability_requests(
    status: Optional[UnavailabilityStatus] = Query(None, description="Filter by status"),
    faculty_id: Optional[str] = Query(None, description="Filter by faculty ID"),
    current_user: dict = Depends(get_current_user)
):
    """Get unavailability requests with optional filtering"""
    
    # Build query
    query = {}
    
    # Role-based access control
    if current_user["role"] == "faculty":
        # Faculty can only see their own requests
        query["faculty_id"] = current_user["id"]
    elif current_user["role"] == "admin":
        # Admin can see all requests, with optional filtering
        if faculty_id:
            query["faculty_id"] = faculty_id
    else:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Add status filter if provided
    if status:
        query["status"] = status.value
    
    # Get requests from database
    requests = list(db["faculty_unavailability"].find(query).sort("created_at", -1))
    
    # Convert to response format
    response_list = []
    for req in requests:
        # Get faculty details
        faculty = db["Users"].find_one({"id": req["faculty_id"], "role": "faculty"})
        faculty_name = f"{faculty.get('first_name', '')} {faculty.get('last_name', '')}" if faculty else "Unknown"
        
        # Get substitute name if assigned
        substitute_name = None
        if req.get("substitute_id"):
            substitute = db["Users"].find_one({"id": req["substitute_id"], "role": "faculty"})
            substitute_name = f"{substitute.get('first_name', '')} {substitute.get('last_name', '')}" if substitute else "Unknown"
        
        response_list.append(UnavailabilityResponse(
            record_id=str(req["_id"]),
            faculty_id=req["faculty_id"],
            faculty_name=faculty_name,
            department=faculty.get("faculty") if faculty else None,
            date=date.fromisoformat(req["date"]),
            reason=req.get("reason"),
            unavailability_type=UnavailabilityType(req["unavailability_type"]),
            status=UnavailabilityStatus(req["status"]),
            substitute_id=req.get("substitute_id"),
            substitute_name=substitute_name,
            created_at=req["created_at"],
            updated_at=req["updated_at"],
            approved_by=req.get("approved_by"),
            admin_notes=req.get("admin_notes")
        ))
    
    return response_list

@router.get("/unavailability-requests/pending", response_model=List[UnavailabilityResponse])
async def get_pending_requests(current_user: dict = Depends(get_admin_role)):
    """Get all pending unavailability requests (admin only)"""
    
    # Build query for pending requests
    query = {"status": "pending"}
    
    # Get requests from database
    requests = list(db["faculty_unavailability"].find(query).sort("created_at", -1))
    
    # Convert to response format
    response_list = []
    for req in requests:
        # Get faculty details
        faculty = db["Users"].find_one({"id": req["faculty_id"], "role": "faculty"})
        faculty_name = f"{faculty.get('first_name', '')} {faculty.get('last_name', '')}" if faculty else "Unknown"
        
        # Get substitute name if assigned
        substitute_name = None
        if req.get("substitute_id"):
            substitute = db["Users"].find_one({"id": req["substitute_id"], "role": "faculty"})
            substitute_name = f"{substitute.get('first_name', '')} {substitute.get('last_name', '')}" if substitute else "Unknown"
        
        response_list.append(UnavailabilityResponse(
            record_id=str(req["_id"]),
            faculty_id=req["faculty_id"],
            faculty_name=faculty_name,
            department=faculty.get("faculty") if faculty else None,
            date=date.fromisoformat(req["date"]),
            reason=req.get("reason"),
            unavailability_type=UnavailabilityType(req["unavailability_type"]),
            status=UnavailabilityStatus(req["status"]),
            substitute_id=req.get("substitute_id"),
            substitute_name=substitute_name,
            created_at=req["created_at"],
            updated_at=req["updated_at"],
            approved_by=req.get("approved_by"),
            admin_notes=req.get("admin_notes")
        ))
    
    return response_list

@router.put("/unavailability-requests/{request_id}/status", response_model=UnavailabilityResponse)
async def update_request_status(
    request_id: str,
    status_update: UnavailabilityStatusUpdate,
    current_user: dict = Depends(get_admin_role)
):
    """Update the status of an unavailability request (admin only)"""
    
    # Find the request
    request_doc = db["faculty_unavailability"].find_one({"_id": request_id})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Unavailability request not found")
    
    # Validate substitute if provided
    substitute_name = None
    if status_update.substitute_id:
        substitute = db["Users"].find_one({"id": status_update.substitute_id, "role": "faculty"})
        if not substitute:
            raise HTTPException(status_code=404, detail=f"Substitute faculty with ID {status_update.substitute_id} not found")
        substitute_name = f"{substitute.get('first_name', '')} {substitute.get('last_name', '')}"
    
    # Update the request
    update_data = {
        "status": status_update.status.value,
        "updated_at": datetime.now(),
        "approved_by": current_user["id"]
    }
    
    if status_update.substitute_id:
        update_data["substitute_id"] = status_update.substitute_id
        update_data["substitute_name"] = substitute_name
    
    if status_update.admin_notes:
        update_data["admin_notes"] = status_update.admin_notes
    
    db["faculty_unavailability"].update_one(
        {"_id": request_id},
        {"$set": update_data}
    )
    
    # Get faculty details for notifications
    faculty = db["Users"].find_one({"id": request_doc["faculty_id"], "role": "faculty"})
    faculty_name = f"{faculty.get('first_name', '')} {faculty.get('last_name', '')}" if faculty else "Unknown"
    
    # Send appropriate notifications
    if status_update.status == UnavailabilityStatus.APPROVED:
        FacultyNotificationService.create_request_approved_notification(
            faculty_id=request_doc["faculty_id"],
            faculty_name=faculty_name,
            date=request_doc["date"],
            substitute_name=substitute_name
        )
        
        # Notify substitute if assigned
        if status_update.substitute_id and substitute_name:
            FacultyNotificationService.create_substitute_assignment_notification(
                substitute_id=status_update.substitute_id,
                substitute_name=substitute_name,
                original_faculty_name=faculty_name,
                date=request_doc["date"]
            )
    
    elif status_update.status == UnavailabilityStatus.DENIED:
        FacultyNotificationService.create_request_denied_notification(
            faculty_id=request_doc["faculty_id"],
            faculty_name=faculty_name,
            date=request_doc["date"],
            admin_notes=status_update.admin_notes
        )
    
    # Return updated request
    updated_request = db["faculty_unavailability"].find_one({"_id": request_id})
    if not updated_request:
        raise HTTPException(status_code=404, detail="Updated request not found")
    
    return UnavailabilityResponse(
        record_id=str(updated_request["_id"]),
        faculty_id=updated_request["faculty_id"],
        faculty_name=faculty_name,
        department=faculty.get("faculty") if faculty else None,
        date=date.fromisoformat(updated_request["date"]),
        reason=updated_request.get("reason"),
        unavailability_type=UnavailabilityType(updated_request["unavailability_type"]),
        status=UnavailabilityStatus(updated_request["status"]),
        substitute_id=updated_request.get("substitute_id"),
        substitute_name=updated_request.get("substitute_name"),
        created_at=updated_request["created_at"],
        updated_at=updated_request["updated_at"],
        approved_by=updated_request.get("approved_by"),
        admin_notes=updated_request.get("admin_notes")
    )

@router.delete("/unavailability-requests/{request_id}")
async def cancel_unavailability_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel an unavailability request"""
    
    # Find the request
    request_doc = db["faculty_unavailability"].find_one({"_id": request_id})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Unavailability request not found")
    
    # Check permissions
    if current_user["role"] == "faculty" and request_doc["faculty_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Faculty can only cancel their own requests")
    elif current_user["role"] not in ["faculty", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Only allow cancellation of pending requests
    if request_doc["status"] != "pending":
        raise HTTPException(status_code=400, detail="Only pending requests can be cancelled")
    
    # Delete the request
    db["faculty_unavailability"].delete_one({"_id": request_id})
    
    return {"success": True, "message": "Unavailability request cancelled successfully"}

@router.get("/faculty/{faculty_id}/unavailable-dates", response_model=List[dict])
async def get_faculty_unavailable_dates(
    faculty_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get approved unavailable dates for a faculty member"""
    
    # Check permissions
    if current_user["role"] == "faculty" and faculty_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Faculty can only view their own unavailable dates")
    
    # Get approved unavailability requests
    requests = list(db["faculty_unavailability"].find({
        "faculty_id": faculty_id,
        "status": "approved"
    }))
    
    # Convert to simple date format
    unavailable_dates = []
    for req in requests:
        unavailable_dates.append({
            "date": req["date"],
            "reason": req.get("reason"),
            "substitute_id": req.get("substitute_id"),
            "substitute_name": req.get("substitute_name")
        })
    
    return unavailable_dates

@router.get("/statistics", response_model=FacultyAvailabilityStats)
async def get_availability_statistics(current_user: dict = Depends(get_admin_role)):
    """Get faculty availability statistics (admin only)"""
    
    # Count requests by status
    total_requests = db["faculty_unavailability"].count_documents({})
    pending_requests = db["faculty_unavailability"].count_documents({"status": "pending"})
    approved_requests = db["faculty_unavailability"].count_documents({"status": "approved"})
    denied_requests = db["faculty_unavailability"].count_documents({"status": "denied"})
    assigned_substitutes = db["faculty_unavailability"].count_documents({
        "status": "approved",
        "substitute_id": {"$exists": True, "$ne": None}
    })
    
    return FacultyAvailabilityStats(
        total_requests=total_requests,
        pending_requests=pending_requests,
        approved_requests=approved_requests,
        denied_requests=denied_requests,
        assigned_substitutes=assigned_substitutes
    )

@router.get("/available-substitutes", response_model=List[dict])
async def get_available_substitutes(
    date_str: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_admin_role)
):
    """Get list of faculty members available as substitutes for a specific date"""
    
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get all faculty members
    all_faculty = list(db["Users"].find({"role": "faculty"}))
    
    # Get faculty who are unavailable on this date
    unavailable_faculty_ids = set()
    unavailable_requests = db["faculty_unavailability"].find({
        "date": date_str,
        "status": "approved"
    })
    
    for req in unavailable_requests:
        unavailable_faculty_ids.add(req["faculty_id"])
    
    # Filter available faculty
    available_faculty = []
    for faculty in all_faculty:
        if faculty["id"] not in unavailable_faculty_ids:
            available_faculty.append({
                "id": faculty["id"],
                "name": f"{faculty.get('first_name', '')} {faculty.get('last_name', '')}",
                "department": faculty.get("faculty"),
                "subjects": faculty.get("subjects", [])
            })
    
    return available_faculty 