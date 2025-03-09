import logging
from datetime import datetime
from app.utils.database import db
 
def create_timetable_notification(algorithm, success):
    """Create a notification when a timetable is generated"""
    try:
        notification = {
            "title": f"Timetable Generation {algorithm}",
            "message": f"Timetable generation with {algorithm} {'succeeded' if success else 'failed'}",
            "timestamp": datetime.now(),
            "type": "success" if success else "error",
            "read": False
        }
        
        db["notifications"].insert_one(notification)
        return True
    except Exception as e:
        logging.error(f"Failed to create notification: {str(e)}")
        return False