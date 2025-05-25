from fastapi import APIRouter, HTTPException
from app.utils.database import db
from bson import ObjectId
from typing import Dict, List
import logging

router = APIRouter() 

@router.get("/teacher-allocation")
async def get_teacher_allocation_report():
    """
    Get teacher allocation report data
    """
    try:
        # Get published timetable
        published_timetable = db["PublishedTimetable"].find_one({"status": "active"})
        
        # Get all faculty users
        faculty_users = list(db["Users"].find({"role": "faculty"}))
        
        if not published_timetable:
            # Return empty allocation data
            return {
                "teachers": [
                    {
                        "id": teacher["id"],
                        "name": f"{teacher['first_name']} {teacher['last_name']}",
                        "faculty": teacher.get("faculty", "Unassigned"),
                        "totalSlots": 0,
                        "workloadHours": 0,
                        "workloadPercentage": 0,
                        "subjects": []
                    }
                    for teacher in faculty_users
                ],
                "hasPublishedTimetable": False
            }
        
        # Process teacher allocations
        teacher_allocations = {}
        
        # Initialize teacher data
        for teacher in faculty_users:
            teacher_name = f"{teacher['first_name']} {teacher['last_name']}"
            teacher_allocations[teacher["id"]] = {
                "id": teacher["id"],
                "name": teacher_name,
                "faculty": teacher.get("faculty", "Unassigned"),
                "totalSlots": 0,
                "workloadHours": 0,
                "workloadPercentage": 0,
                "subjects": {}
            }
        
        # Count allocations from published timetable
        for semester_entries in published_timetable["semesters"].values():
            for entry in semester_entries:
                # Find teacher by name match
                teacher = next((t for t in faculty_users if 
                              entry.get("teacher") == f"{t['first_name']} {t['last_name']}" or
                              entry.get("teacher") == t["id"] or
                              entry.get("teacher") == t["username"]), None)
                
                if teacher and teacher["id"] in teacher_allocations:
                    teacher_data = teacher_allocations[teacher["id"]]
                    teacher_data["totalSlots"] += 1
                    
                    # Track subjects
                    subject = entry.get("subject", "Unknown")
                    if subject not in teacher_data["subjects"]:
                        teacher_data["subjects"][subject] = 0
                    teacher_data["subjects"][subject] += 1
                    
                    # Add workload hours
                    duration = entry.get("duration", 1)
                    teacher_data["workloadHours"] += duration
        
        # Calculate workload percentages and format subjects
        full_workload = 20  # Assuming 20 hours per week is full workload
        
        for teacher_data in teacher_allocations.values():
            teacher_data["workloadPercentage"] = min((teacher_data["workloadHours"] / full_workload) * 100, 100)
            teacher_data["subjects"] = [
                {"subject": subject, "count": count}
                for subject, count in teacher_data["subjects"].items()
            ]
        
        return {
            "teachers": list(teacher_allocations.values()),
            "hasPublishedTimetable": True
        }
        
    except Exception as e:
        logging.error(f"Error generating teacher allocation report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate teacher allocation report: {str(e)}")

@router.get("/space-occupancy")
async def get_space_occupancy_report():
    """
    Get space occupancy report data
    """
    try:
        # Get published timetable
        published_timetable = db["PublishedTimetable"].find_one({"status": "active"})
        
        # Get all spaces
        spaces = list(db["Spaces"].find())
        
        # Get days and periods for total slot calculation
        days = list(db["days_of_operation"].find())
        periods = list(db["periods_of_operation"].find())
        total_possible_slots = len(days) * len(periods)
        
        if not published_timetable:
            # Return empty occupancy data
            return {
                "spaces": [
                    {
                        "id": str(space["_id"]),
                        "name": space["name"],
                        "type": space.get("attributes", {}).get("type", "Lecture Hall"),
                        "capacity": space.get("capacity", 30),
                        "totalSlots": total_possible_slots,
                        "occupiedSlots": 0,
                        "occupancyRate": 0,
                        "dayOccupancy": {},
                        "periodOccupancy": {},
                        "details": []
                    }
                    for space in spaces
                ],
                "hasPublishedTimetable": False
            }
        
        # Process space occupancy
        space_occupancy = {}
        
        # Initialize space data
        for space in spaces:
            space_occupancy[space["name"]] = {
                "id": str(space["_id"]),
                "name": space["name"],
                "type": space.get("attributes", {}).get("type", "Lecture Hall"),
                "capacity": space.get("capacity", 30),
                "totalSlots": total_possible_slots,
                "occupiedSlots": 0,
                "occupancyRate": 0,
                "dayOccupancy": {},
                "periodOccupancy": {},
                "details": []
            }
        
        # Count occupancies from published timetable
        for semester_entries in published_timetable["semesters"].values():
            for entry in semester_entries:
                room_name = entry.get("room", {}).get("name") if isinstance(entry.get("room"), dict) else entry.get("room")
                
                if room_name and room_name in space_occupancy:
                    space_data = space_occupancy[room_name]
                    space_data["occupiedSlots"] += 1
                    
                    # Track day occupancy
                    day_name = entry.get("day", {}).get("name") if isinstance(entry.get("day"), dict) else entry.get("day")
                    if day_name:
                        if day_name not in space_data["dayOccupancy"]:
                            space_data["dayOccupancy"][day_name] = 0
                        space_data["dayOccupancy"][day_name] += 1
                    
                    # Track period occupancy
                    period_info = entry.get("period", [])
                    if isinstance(period_info, list) and len(period_info) > 0:
                        period_name = period_info[0].get("name") if isinstance(period_info[0], dict) else period_info[0]
                    else:
                        period_name = period_info
                    
                    if period_name:
                        if period_name not in space_data["periodOccupancy"]:
                            space_data["periodOccupancy"][period_name] = 0
                        space_data["periodOccupancy"][period_name] += 1
                    
                    # Add detailed info
                    space_data["details"].append({
                        "day": day_name,
                        "period": period_name,
                        "subject": entry.get("subject"),
                        "teacher": entry.get("teacher"),
                        "studentGroup": entry.get("subgroup", "-")
                    })
        
        # Calculate occupancy rates
        for space_data in space_occupancy.values():
            if space_data["totalSlots"] > 0:
                space_data["occupancyRate"] = (space_data["occupiedSlots"] / space_data["totalSlots"]) * 100
        
        return {
            "spaces": list(space_occupancy.values()),
            "hasPublishedTimetable": True
        }
        
    except Exception as e:
        logging.error(f"Error generating space occupancy report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate space occupancy report: {str(e)}")

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