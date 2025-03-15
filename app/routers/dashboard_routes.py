from fastapi import APIRouter, HTTPException
from app.utils.database import db
from bson import ObjectId

router = APIRouter() 

@router.put("/timetable/notifications/mark-all-read")
async def mark_all_notifications_read():
    try:
        # First check if there are any unread notifications
        unread_count = db["notifications"].count_documents({"read": False})
        
        if unread_count == 0:
            return {"success": True, "modified_count": 0, "message": "No unread notifications found"}
            
        # Update all unread notifications
        result = db["notifications"].update_many(
            {"read": False},
            {"$set": {"read": True}}
        )
        
        return {
            "success": True, 
            "modified_count": result.modified_count,
            "matched_count": result.matched_count
        }
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error in mark_all_notifications_read: {error_details}")
        raise HTTPException(status_code=500, detail=str(e))