from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.Services.faculty_notification_service import FacultyNotificationService
from app.routers.user_router import get_current_user

router = APIRouter()

@router.get("/notifications", response_model=List[Dict[str, Any]])
async def get_user_notifications(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for the current user"""
    
    notifications = FacultyNotificationService.get_notifications_for_user(
        user_id=current_user["id"],
        role=current_user["role"],
        limit=limit
    )
    
    # Convert ObjectId to string for JSON serialization
    for notification in notifications:
        if "_id" in notification:
            notification["id"] = str(notification["_id"])
            del notification["_id"]
    
    return notifications

@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read"""
    
    success = FacultyNotificationService.mark_notification_as_read(
        notification_id=notification_id,
        user_id=current_user["id"]
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found or access denied")
    
    return {"success": True, "message": "Notification marked as read"}

@router.get("/notifications/unread-count", response_model=Dict[str, int])
async def get_unread_notification_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread notifications for the current user"""
    
    count = FacultyNotificationService.get_unread_count(
        user_id=current_user["id"],
        role=current_user["role"]
    )
    
    return {"unread_count": count} 