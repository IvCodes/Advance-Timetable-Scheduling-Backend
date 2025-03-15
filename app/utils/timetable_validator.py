from typing import List, Dict
from bson import ObjectId

class ConflictChecker:
    def __init__(self, db):
        self.db = db

    def check_single_timetable_conflicts(self, timetable_id: str, updated_activities: List[Dict], session_id: str) -> List[Dict]:
        """
        Check for conflicts within the same timetable for the updated activities on their specific day(s).
        Only checks the day(s) of the updated activities.
        Uses session_id to avoid comparing an activity with itself.
        """
        conflicts = []

        # Retrieve the current timetable from the database
        timetable = self.db["Timetable"].find_one({"_id": ObjectId(timetable_id)})
        if not timetable:
            return conflicts

        # Get all existing activities from the timetable
        existing_activities = timetable.get("timetable", [])

        # Group updated activities by day
        updated_activities_by_day = {}
        for activity in updated_activities:
            day = activity.get("day", {}).get("name", "")
            if day:  # Skip activities without a valid day
                updated_activities_by_day.setdefault(day, []).append(activity)

        # Check each day for conflicts
        for day, updated_activities_on_day in updated_activities_by_day.items():
            # Filter existing activities for the same day
            existing_activities_on_day = [
                act for act in existing_activities
                if act.get("day", {}).get("name", "") == day
                and act.get("session_id") != session_id  # Exclude activities from the current session
            ]

            # Check updated activities against existing activities on the same day
            for updated_activity in updated_activities_on_day:
                updated_periods = {p.get("name", "") for p in updated_activity.get("period", [])}
                updated_room = updated_activity.get("room", {}).get("code", "")
                updated_teacher = updated_activity.get("teacher", "")

                print(updated_teacher)

                # --- Room conflict ---
                if updated_room:
                    for existing_activity in existing_activities_on_day:
                        existing_periods = {p.get("name", "") for p in existing_activity.get("period", [])}
                        existing_room = existing_activity.get("room", {}).get("code", "")

                        if updated_room == existing_room and updated_periods & existing_periods:
                            conflicts.append(self._create_conflict(
                                "room_conflict",
                                updated_room,
                                existing_activity,
                                updated_activity
                            ))

                # --- Teacher conflict ---
                if updated_teacher:
                    for existing_activity in existing_activities_on_day:
                        existing_periods = {p.get("name", "") for p in existing_activity.get("period", [])}
                        existing_teacher = existing_activity.get("teacher", "")

                        print(existing_teacher)

                        if updated_teacher == existing_teacher and updated_periods & existing_periods:
                            conflicts.append(self._create_conflict(
                                "lecturer_conflict",
                                updated_teacher,
                                existing_activity,
                                updated_activity
                            ))

            # Also check for conflicts between the updated activities themselves
            for i, activity1 in enumerate(updated_activities_on_day):
                for activity2 in updated_activities_on_day[i+1:]:  # Compare with activities not yet compared
                    activity1_periods = {p.get("name", "") for p in activity1.get("period", [])}
                    activity2_periods = {p.get("name", "") for p in activity2.get("period", [])}
                    
                    # Check for period overlap
                    if activity1_periods & activity2_periods:
                        # Room conflict between updated activities
                        room1 = activity1.get("room", {}).get("code", "")
                        room2 = activity2.get("room", {}).get("code", "")
                        if room1 and room2 and room1 == room2:
                            conflicts.append(self._create_conflict(
                                "room_conflict",
                                room1,
                                activity1,
                                activity2
                            ))
                        
                        # Teacher conflict between updated activities
                        teacher1 = activity1.get("teacher", "")
                        teacher2 = activity2.get("teacher", "")
                        if teacher1 and teacher2 and teacher1 == teacher2:
                            conflicts.append(self._create_conflict(
                                "lecturer_conflict",
                                teacher1,
                                activity1,
                                activity2
                            ))

        return conflicts

    def check_cross_timetable_conflicts(self, updated_activities: List[Dict], timetable_id: str, algorithm: str) -> List[Dict]:
        """
        Check for conflicts between the updated activities and activities in other timetables with the same algorithm.
        Only checks for conflicts on the specific day(s) of the updated activities.
        """
        conflicts = []

        # Get the days of the updated activities
        updated_days = {activity.get("day", {}).get("name", "") for activity in updated_activities}

        # Retrieve other timetables with the same algorithm and overlapping days
        other_timetables = self.db["Timetable"].find({
            "_id": {"$ne": ObjectId(timetable_id)},
            "algorithm": algorithm,
            "timetable.day.name": {"$in": list(updated_days)}
        })

        # Collect all activities from other timetables on the same days as the updated activities
        other_activities = []
        for tt in other_timetables:
            for act in tt.get("timetable", []):
                if act.get("day", {}).get("name", "") in updated_days:
                    other_activities.append(act)

        # Check each updated activity against other activities on the same day
        for updated_activity in updated_activities:
            updated_day = updated_activity.get("day", {}).get("name", "")
            updated_periods = {p.get("name", "") for p in updated_activity.get("period", [])}
            updated_room = updated_activity.get("room", {}).get("code", "")
            updated_teacher = updated_activity.get("teacher", "")

            for other_activity in other_activities:
                if other_activity.get("day", {}).get("name", "") != updated_day:
                    continue  # Skip if not on the same day

                other_periods = {p.get("name", "") for p in other_activity.get("period", [])}
                other_room = other_activity.get("room", {}).get("code", "")
                other_teacher = other_activity.get("teacher", "")

                # --- Cross-timetable room conflict ---
                if updated_room and updated_room == other_room and updated_periods & other_periods:
                    conflicts.append(self._create_conflict(
                        "cross_timetable_room_conflict",
                        updated_room,
                        other_activity,
                        updated_activity
                    ))

                # --- Cross-timetable teacher conflict ---
                if updated_teacher and updated_teacher == other_teacher and updated_periods & other_periods:
                    conflicts.append(self._create_conflict(
                        "cross_timetable_lecturer_conflict",
                        updated_teacher,
                        other_activity,
                        updated_activity
                    ))

        return conflicts

    def validate_activities(self, activities: List[Dict]) -> List[str]:
        """
        Validate the structure and data of activities.
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
        Helper function to create a detailed conflict entry with user-friendly messages.
        """
        conflict_descriptions = {
            "room_conflict": f"Room '{entity}' is double-booked.",
            "lecturer_conflict": f"Lecturer '{entity}' has overlapping classes.",
            "cross_timetable_room_conflict": f"Room '{entity}' is already booked in another timetable.",
            "cross_timetable_lecturer_conflict": f"Lecturer '{entity}' is teaching in another timetable."
        }

        overlapping_periods = list(
            {p.get("name", "") for p in activity1.get("period", [])}.intersection(
                {p.get("name", "") for p in activity2.get("period", [])}
            )
        )

        return {
            "type": conflict_type,
            "description": conflict_descriptions.get(conflict_type, "Conflict detected"),
            "details": {
                "day": activity1.get("day", {}).get("name", "Unknown day"),
                "periods": overlapping_periods,
                "activities": [
                    {"subject": activity1.get("subject"), "activity_id": activity1.get("activity_id")},
                    {"subject": activity2.get("subject"), "activity_id": activity2.get("activity_id")}
                ]
            }
        }