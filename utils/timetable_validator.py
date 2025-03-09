from typing import List, Dict
from bson import ObjectId

class ConflictChecker:
    def __init__(self, db):
        self.db = db

    def check_single_timetable_conflicts(self, timetable_id: str, updated_activities: List[Dict]) -> List[Dict]:
        """
        Check for conflicts within a single timetable’s activities.
        This function builds a new schedule by replacing any existing activities 
        (matched by 'activity_id') with the updated ones and then checking each day 
        for overlapping bookings in the same room, by the same teacher, or for the same subject.
        """
        conflicts = []
        
        # Retrieve the current timetable from the database
        timetable = self.db["Timetable"].find_one({"_id": ObjectId(timetable_id)})
        if not timetable:
            return conflicts

        # Get all existing activities from the timetable
        existing_activities = timetable.get("timetable", [])
        
        # Collect IDs of activities being updated
        updated_ids = {activity.get("activity_id") for activity in updated_activities if activity.get("activity_id")}
        
        # Exclude activities that are being updated from the existing schedule
        remaining_activities = [act for act in existing_activities if act.get("activity_id") not in updated_ids]

        # Combine the remaining activities with the updated activities to simulate the new timetable
        combined_activities = remaining_activities + updated_activities

        # Group activities by day (using day name)
        activities_by_day = {}
        for activity in combined_activities:
            day = activity.get("day", {}).get("name", "")
            if not day:
                continue  # Skip if no day is provided
            activities_by_day.setdefault(day, []).append(activity)

        # Check each day for conflicts
        for day, activities in activities_by_day.items():
            # Dictionaries to track usage for each resource on that day
            seen_rooms = {}
            seen_teachers = {}
            seen_subjects = {}

            for activity in activities:
                periods = {p.get("name", "") for p in activity.get("period", [])}
                room = activity.get("room", {}).get("code", "")
                teacher = activity.get("teacher", "")
                subject = activity.get("subject", "")

                # --- Room conflict ---
                if room:
                    if room in seen_rooms:
                        for prev in seen_rooms[room]:
                            prev_periods = prev["periods"]
                            # If the periods overlap, record a room conflict
                            if periods.intersection(prev_periods):
                                conflicts.append(self._create_conflict("room_conflict", room, prev["activity"], activity))
                        seen_rooms[room].append({"activity": activity, "periods": periods})
                    else:
                        seen_rooms[room] = [{"activity": activity, "periods": periods}]

                # --- Teacher conflict ---
                if teacher:
                    if teacher in seen_teachers:
                        for prev in seen_teachers[teacher]:
                            prev_periods = prev["periods"]
                            if periods.intersection(prev_periods):
                                conflicts.append(self._create_conflict("lecturer_conflict", teacher, prev["activity"], activity))
                        seen_teachers[teacher].append({"activity": activity, "periods": periods})
                    else:
                        seen_teachers[teacher] = [{"activity": activity, "periods": periods}]

                # --- Subject conflict ---
                if subject:
                    if subject in seen_subjects:
                        for prev in seen_subjects[subject]:
                            prev_periods = prev["periods"]
                            if periods.intersection(prev_periods):
                                conflicts.append(self._create_conflict("subject_conflict", subject, prev["activity"], activity))
                        seen_subjects[subject].append({"activity": activity, "periods": periods})
                    else:
                        seen_subjects[subject] = [{"activity": activity, "periods": periods}]

        return conflicts

    def check_cross_timetable_conflicts(self, activities: List[Dict], timetable_id: str, algorithm: str) -> List[Dict]:
        """
        Check for conflicts between the provided activities and those in other timetables 
        (of the same algorithm). Only room, teacher, and subject conflicts are checked.
        """
        conflicts = []
        days = {activity["day"]["name"] for activity in activities if activity.get("day", {}).get("name")}
        
        # Retrieve other timetables (exclude the current one) that have activities on these days
        other_timetables = list(self.db["Timetable"].find({
            "_id": {"$ne": ObjectId(timetable_id)},
            "algorithm": algorithm,
            "timetable.day.name": {"$in": list(days)}
        }))
        
        all_other_activities = []
        for tt in other_timetables:
            for act in tt.get("timetable", []):
                if act.get("day", {}).get("name", "") in days:
                    all_other_activities.append(act)
        
        for new_activity in activities:
            new_day = new_activity["day"]["name"]
            new_periods = {p["name"] for p in new_activity.get("period", [])}
            new_room = new_activity.get("room", {}).get("code", "")
            new_teacher = new_activity.get("teacher", "")
            new_subject = new_activity.get("subject", "")
            
            for existing_activity in all_other_activities:
                if new_day != existing_activity.get("day", {}).get("name", ""):
                    continue
                
                existing_periods = {p["name"] for p in existing_activity.get("period", [])}
                if not new_periods.intersection(existing_periods):
                    continue
                
                # --- Cross-timetable room conflict ---
                if new_room and (new_room == existing_activity.get("room", {}).get("code", "")):
                    conflicts.append(self._create_conflict("cross_timetable_room_conflict", new_room, new_activity, existing_activity))
                
                # --- Cross-timetable teacher conflict ---
                if new_teacher and (new_teacher == existing_activity.get("teacher", "")):
                    conflicts.append(self._create_conflict("cross_timetable_lecturer_conflict", new_teacher, new_activity, existing_activity))
                
                # --- Cross-timetable subject conflict ---
                if new_subject and (new_subject == existing_activity.get("subject", "")):
                    conflicts.append(self._create_conflict("cross_timetable_subject_conflict", new_subject, new_activity, existing_activity))
        
        return conflicts

    def validate_activities(self, activities: List[Dict]) -> List[str]:
        """
        Validate the structure and data of activities.
        (Subgroup is omitted since it is not used for conflict checking.)
        """
        errors = []
        required_fields = {
            "activity_id": str,
            "day": dict,
            "period": list,
            "room": dict,
            "teacher": str,
            "duration": int,
            "subject": str
        }
        
        for activity in activities:
            for field, field_type in required_fields.items():
                if field not in activity:
                    errors.append(f"Missing required field: {field}")
                elif not isinstance(activity[field], field_type):
                    errors.append(f"Invalid type for field {field}: expected {field_type.__name__}")
            
            if "day" in activity and "name" not in activity["day"]:
                errors.append("Missing day name in day field")
            
            if "room" in activity and "code" not in activity["room"]:
                errors.append("Missing room code in room field")
            
            if "period" in activity:
                if not activity["period"]:
                    errors.append("Period list cannot be empty")
                for period in activity["period"]:
                    if "name" not in period:
                        errors.append("Missing period name in period field")
        
        return errors

    def _create_conflict(self, conflict_type: str, entity: str, activity1: Dict, activity2: Dict) -> Dict:
        """
        Helper function to create a detailed conflict entry with user‐friendly messages.
        """
        conflict_descriptions = {
            "room_conflict": (
                f"Room '{entity}' is double-booked. It is scheduled for more than one activity at the same time."
            ),
            "lecturer_conflict": (
                f"Lecturer '{entity}' is assigned overlapping classes. Please check the schedule to resolve this clash."
            ),
            "subject_conflict": (
                f"Subject '{entity}' has concurrent sessions. Multiple sessions of the same subject should not overlap."
            ),
            "cross_timetable_room_conflict": (
                f"Room '{entity}' is already booked in another timetable. This room is scheduled for different activities at the same time."
            ),
            "cross_timetable_lecturer_conflict": (
                f"Lecturer '{entity}' is teaching in another timetable. They cannot be in two places at once."
            ),
            "cross_timetable_subject_conflict": (
                f"Subject '{entity}' is already scheduled in another timetable at the same time."
            )
        }

        # Determine the overlapping periods between the two activities
        overlapping_periods = list(
            {p.get("name", "") for p in activity1.get("period", [])}.intersection(
                {p.get("name", "") for p in activity2.get("period", [])}
            )
        )
    
        day = activity1.get("day", {}).get("name", "Unknown day")
        period_str = ", ".join(overlapping_periods) if overlapping_periods else "Unknown period(s)"
        
        base_description = conflict_descriptions.get(conflict_type, "Conflict detected")
        
        detailed_description = (
            f"{base_description}"
            # f"Day: {day}\n"
            # f"Overlapping Period(s): {period_str}\n"
            # "Conflicting activities:\n"
            # f" - {activity1.get('subject', 'Unknown subject')} (Activity ID: {activity1.get('activity_id', 'N/A')})\n"
            # f" - {activity2.get('subject', 'Unknown subject')} (Activity ID: {activity2.get('activity_id', 'N/A')})"
        )

        return {
            "type": conflict_type,
            "description": detailed_description,
            # "activities": [activity1, activity2],
            # "day": day,
            # "periods": overlapping_periods,
            # "entity": entity
        }