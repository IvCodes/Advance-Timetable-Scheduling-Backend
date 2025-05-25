import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.utils.database import db
from app.models.faculty_unavailability_model import UnavailabilityStatus, UnavailabilityRecord

logger = logging.getLogger(__name__)

class FacultyNotificationService:
    """Service to handle notifications for faculty unavailability management"""
    
    @staticmethod
    def create_unavailability_request_notification(faculty_id: str, faculty_name: str, date: str, reason: Optional[str] = None) -> bool:
        """Create notification when faculty submits unavailability request"""
        try:
            notification = {
                "title": "New Faculty Unavailability Request",
                "message": f"{faculty_name} has requested to be unavailable on {date}" + (f" - {reason}" if reason else ""),
                "timestamp": datetime.now(),
                "type": "info",
                "category": "faculty_unavailability",
                "read": False,
                "target_roles": ["admin"],
                "data": {
                    "faculty_id": faculty_id,
                    "date": date,
                    "action_required": True
                }
            }
            
            db["notifications"].insert_one(notification)
            logger.info(f"Created unavailability request notification for faculty {faculty_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create unavailability request notification: {str(e)}")
            return False
    
    @staticmethod
    def create_request_approved_notification(faculty_id: str, faculty_name: str, date: str, substitute_name: Optional[str] = None) -> bool:
        """Create notification when admin approves unavailability request"""
        try:
            substitute_msg = f" A substitute ({substitute_name}) has been assigned." if substitute_name else ""
            notification = {
                "title": "Unavailability Request Approved",
                "message": f"Your unavailability request for {date} has been approved.{substitute_msg}",
                "timestamp": datetime.now(),
                "type": "success",
                "category": "faculty_unavailability",
                "read": False,
                "target_user_id": faculty_id,
                "data": {
                    "date": date,
                    "status": "approved",
                    "substitute_assigned": substitute_name is not None
                }
            }
            
            db["notifications"].insert_one(notification)
            logger.info(f"Created approval notification for faculty {faculty_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create approval notification: {str(e)}")
            return False
    
    @staticmethod
    def create_request_denied_notification(faculty_id: str, faculty_name: str, date: str, admin_notes: Optional[str] = None) -> bool:
        """Create notification when admin denies unavailability request"""
        try:
            notes_msg = f" Reason: {admin_notes}" if admin_notes else ""
            notification = {
                "title": "Unavailability Request Denied",
                "message": f"Your unavailability request for {date} has been denied.{notes_msg}",
                "timestamp": datetime.now(),
                "type": "warning",
                "category": "faculty_unavailability",
                "read": False,
                "target_user_id": faculty_id,
                "data": {
                    "date": date,
                    "status": "denied",
                    "admin_notes": admin_notes
                }
            }
            
            db["notifications"].insert_one(notification)
            logger.info(f"Created denial notification for faculty {faculty_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create denial notification: {str(e)}")
            return False
    
    @staticmethod
    def create_substitute_assignment_notification(substitute_id: str, substitute_name: str, original_faculty_name: str, date: str) -> bool:
        """Create notification when faculty is assigned as substitute"""
        try:
            notification = {
                "title": "Substitute Teaching Assignment",
                "message": f"You have been assigned as a substitute for {original_faculty_name} on {date}",
                "timestamp": datetime.now(),
                "type": "info",
                "category": "substitute_assignment",
                "read": False,
                "target_user_id": substitute_id,
                "data": {
                    "original_faculty": original_faculty_name,
                    "date": date,
                    "role": "substitute"
                }
            }
            
            db["notifications"].insert_one(notification)
            logger.info(f"Created substitute assignment notification for faculty {substitute_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create substitute assignment notification: {str(e)}")
            return False
    
    @staticmethod
    def create_timetable_update_notification(affected_users: List[str], date: str, changes: str) -> bool:
        """Create notification for timetable changes due to faculty unavailability"""
        try:
            for user_id in affected_users:
                notification = {
                    "title": "Timetable Update",
                    "message": f"Your timetable has been updated for {date}. Changes: {changes}",
                    "timestamp": datetime.now(),
                    "type": "info",
                    "category": "timetable_update",
                    "read": False,
                    "target_user_id": user_id,
                    "data": {
                        "date": date,
                        "changes": changes
                    }
                }
                
                db["notifications"].insert_one(notification)
            
            logger.info(f"Created timetable update notifications for {len(affected_users)} users")
            return True
        except Exception as e:
            logger.error(f"Failed to create timetable update notifications: {str(e)}")
            return False
    
    @staticmethod
    def get_notifications_for_user(user_id: str, role: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notifications for a specific user"""
        try:
            query = {
                "$or": [
                    {"target_user_id": user_id},
                    {"target_roles": role}
                ]
            }
            
            notifications = list(db["notifications"].find(query).sort("timestamp", -1).limit(limit))
            return notifications
        except Exception as e:
            logger.error(f"Failed to get notifications for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def mark_notification_as_read(notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        try:
            result = db["notifications"].update_one(
                {"_id": notification_id, "$or": [{"target_user_id": user_id}, {"target_roles": {"$exists": True}}]},
                {"$set": {"read": True}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            return False
    
    @staticmethod
    def get_unread_count(user_id: str, role: str) -> int:
        """Get count of unread notifications for a user"""
        try:
            query = {
                "read": False,
                "$or": [
                    {"target_user_id": user_id},
                    {"target_roles": role}
                ]
            }
            
            count = db["notifications"].count_documents(query)
            return count
        except Exception as e:
            logger.error(f"Failed to get unread count for user {user_id}: {str(e)}")
            return 0 