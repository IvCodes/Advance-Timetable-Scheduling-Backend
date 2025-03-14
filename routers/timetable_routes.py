from fastapi import APIRouter, HTTPException, Depends
from routers.user_router import get_current_user
from utils.database import db
from typing import List, Dict
from generator.algorithms.ga.ga import *
from generator.algorithms.co.co_v2 import *
# from generator.algorithms.rl.rl_train import *
from generator.algorithms.rl.rl import *
from generator.algorithms.eval.eval import *
from generator.algorithms.bc.bc_v1 import *
from generator.algorithms.pso.pso_v1 import *
from datetime import datetime
from bson import ObjectId
from models.timetable_model import Timetable
from utils.timetable_validator import ConflictChecker


router = APIRouter()

@router.post("/generate")
async def generate_timetable(current_user: dict = Depends(get_current_user)):
    # Example usage of your scheduling algorithm:
    aco = generate_co()
    save_timetable(aco, "CO", current_user)
    bco = generate_bco()
    save_timetable(bco , "BC" , current_user)
    pso = generate_pso()
    save_timetable(pso , "PSO" , current_user)
    
    return {"message": "Timetable generated"}

def map_subgroup_to_semester(subgroup_id: str):
    """
    Map activity subgroup format (like 'Y1S1.IT.1') to a semester format (like 'SEM101').
    Adjust as necessary for your naming convention.
    """
    mapping = {
        "Y1S1": "SEM101",
        "Y1S2": "SEM102",
        "Y2S1": "SEM201",
        "Y2S2": "SEM202",
        "Y3S1": "SEM301",
        "Y3S2": "SEM302",
        "Y4S1": "SEM401",
        "Y4S2": "SEM402"
    }
    
    # If the entire subgroup_id is exactly in the mapping, return it
    if subgroup_id in mapping:
        return mapping[subgroup_id]
    
    # Otherwise, try splitting on the first dot
    if '.' in subgroup_id:
        prefix = subgroup_id.split('.', 1)[0]
        if prefix in mapping:
            return mapping[prefix]
    
    return None  # No known mapping

def save_timetable(li, algorithm, current_user):
    """
    Saves the timetable solution to the DB, mapped by semester.
    
    Fix #1: only append each activity once per solution.
    Fix #2: remove the stray period in generate_timetable_code.
    """
    # If no solution was returned
    if li is None:
        print(f"Warning: No timetable data received for algorithm {algorithm}. Nothing to save.")
        db["notifications"].insert_one({
            "message": f"Failed to generate timetable using {algorithm}. No data was produced.",
            "type": "error",
            "read": False,
            "recipient": current_user["id"]
        })
        return

    # List all valid semester codes you expect
    subgroups = [
        "SEM101", "SEM102", "SEM201", "SEM202",
        "SEM301", "SEM302", "SEM401", "SEM402"
    ]
    
    # Create dict to hold final activities for each semester
    semester_timetables = {semester: [] for semester in subgroups}

    for activity in li:
        # Some activities have multiple subgroups
        if isinstance(activity["subgroup"], list):
            subgroup_ids = activity["subgroup"]
        else:
            subgroup_ids = [activity["subgroup"]]

        # We'll break after the first successful mapping if the activity 
        # can only truly belong to one semester.
        mapped = False
        for subgroup_id in subgroup_ids:
            mapped_id = map_subgroup_to_semester(subgroup_id)
            if mapped_id and mapped_id in semester_timetables:
                # Add the activity to this semester
                semester_timetables[mapped_id].append(activity)
                mapped = True
                # Avoid duplicating the same activity multiple times 
                # if multiple subgroups map to the same semester
                break  
        
        if not mapped:
            print(f"Warning: Could not map any subgroup in: {subgroup_ids}")
            print(f"Skipping activity: {activity}")

    # Sort your semester keys in a fixed order
    sorted_semesters = sorted(semester_timetables.keys(), key=lambda x: subgroups.index(x))

    # Write to DB
    for index, semester in enumerate(sorted_semesters):
        activities = semester_timetables[semester]
        
        db["Timetable"].replace_one(
            {
                "$and": [
                    {"semester": semester},
                    {"algorithm": algorithm}
                ]
            },
            {
                "code": generate_timetable_code(index, algorithm),
                "algorithm": algorithm,
                "semester": semester,
                "timetable": activities
            },
            upsert=True
        )

        db["old_timetables"].insert_one({
            "code": generate_timetable_code(index, algorithm),
            "algorithm": algorithm,
            "semester": semester,
            "timetable": activities,
            "date_created": datetime.now()
        })

    # Send a notification to the user
    db["notifications"].insert_one({
        "message": f"New timetable generated using {algorithm}",
        "type": "success",
        "read": False,
        "recipient": current_user["id"]
    })

def generate_timetable_code(index, algorithm):
    """
    Example code generator for stored timetables.
    Fix #2: removed the trailing period.
    """
    return f"{algorithm}-TT000{index}"

@router.get("/timetables")
async def get_timetables():
    timetables = list(db["Timetable"].find())
    cleaned_timetables = clean_mongo_documents(timetables)
    eval =  db["settings"].find_one({"option": "latest_score"})
    eval = clean_mongo_documents(eval)
    
    for algorithm, scores in eval["value"].items():
        average_score = sum(scores) / len(scores)
        eval[algorithm] = {
            "average_score": average_score,
        }
    
    out ={
        "timetables": cleaned_timetables,
        "eval": eval
    }
    
    return out

@router.post("/select")
async def select_algorithm(algo: dict, current_user: dict = Depends(get_current_user)):
    result = db["settings"].find_one({"option": "selected_algorithm"})
    if result:
        db["settings"].update_one(
            {"option": "selected_algorithm"},
            {"$set": {"value": algo["algorithm"]}}
        )
    else:
        db["settings"].insert_one({"option": "selected_algorithm", "value": algo})
    return {"message": "Algorithm selected", "selected_algorithm": algo}

@router.get("/selected")
async def get_selected_algorithm(current_user: dict = Depends(get_current_user)):
    result = db["settings"].find_one({"option": "selected_algorithm"})
    if result:
        return {"selected_algorithm": result["value"]}
    return {"selected_algorithm": None}

@router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    notifications = list(db["notifications"].find({
        "recipient": current_user["id"],
        "read": False
    }))
    notifications = clean_mongo_documents(notifications)
    return notifications

@router.put("/notifications/{notification_id}")
async def mark_notification_as_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    result = db["notifications"].update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"read": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}

@router.patch("/timetable/{timetable_id}/activity/{session_id}")
async def super_update_session(
    timetable_id: str,
    session_id: str,
    partial_data: Dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Partially update (PATCH) a single scheduled session in a timetable. 
    The request body can contain only the fields to be changed, or multiple fields. 
    We do a conflict check before saving changes. 
    If conflicts are found, we discard the changes and return an error.
    """
    checker = ConflictChecker(db)

    # 1) Retrieve the timetable
    timetable = db["Timetable"].find_one({"_id": ObjectId(timetable_id)})
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")

    existing_activities = timetable.get("timetable", [])

    # 2) Locate the session to patch
    target_session = None
    for activity in existing_activities:
        if activity.get("session_id") == session_id:
            target_session = activity
            break
    if not target_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 3) Make an in-memory copy of the entire timetable for conflict checks
    updated_activities = []
    for act in existing_activities:
        if act.get("session_id") == session_id:
            # Create a copy so we can merge partial_data into it
            updated_act = dict(act)  # shallow copy
            for k, v in partial_data.items():
                # If you're not allowing session_id changes, skip that key
                if k == "session_id":
                    continue
                updated_act[k] = v
            updated_activities.append(updated_act)
        else:
            # Everyone else remains unchanged
            updated_activities.append(act)

    # 4) Optional partial validation:
    #    We only strictly need 'session_id' to identify the session. 
    #    But if your logic requires certain fields, validate them:
    # validation_errors = checker.validate_patch_activities([partial_data]) 
    # if validation_errors:
    #    raise HTTPException(400, detail={"message": "Validation failed", "errors": validation_errors})

    # 5) Run conflict checks on the *entire updated timetable*
    #    a) internal conflicts
    conflicts_internal = checker.check_single_timetable_conflicts_in_memory(updated_activities)
    #    b) cross-timetable conflicts (comparing updated sessions to other timetables)
    #       pass only the updated sessions or the entire updated_activities depending on your needs:
    #       often we pass the updated_activities since you might want to see if ANY changes conflict
    algorithm = timetable.get("algorithm", "")
    conflicts_cross = checker.check_cross_timetable_conflicts(updated_activities, timetable_id, algorithm)

    all_conflicts = conflicts_internal + conflicts_cross
    if all_conflicts:
        # 6) If we have conflicts, return an error (and do NOT persist changes).
        return {
            "message": "Conflicts detected. Changes were not saved.",
            "conflicts": all_conflicts
        }

    # 7) If no conflicts, commit the updated_activities to DB
    db["Timetable"].update_one(
        {"_id": ObjectId(timetable_id)},
        {"$set": {"timetable": updated_activities}}
    )

    # 8) Optionally store a history record or send notifications
    # db["timetable_history"].insert_one(...)

    return {
        "message": "Session updated successfully. No conflicts found.",
        "updated_session_id": session_id
    }


@router.get("/timetable/{timetable_id}/conflicts")
async def check_timetable_conflicts(
    timetable_id: str,
    activities: List[Dict],
    current_user: dict = Depends(get_current_user)
):
    """
    Check for conflicts without actually updating the timetable
    """
    checker = ConflictChecker(db)
    
    # Validate activity structure
    validation_errors = checker.validate_activities(activities)
    if validation_errors:
        return {
            "valid": False,
            "validation_errors": validation_errors
        }
    
    # Check all types of conflicts
    internal_conflicts = checker.check_single_timetable_conflicts(activities)
    cross_timetable_conflicts = checker.check_cross_timetable_conflicts(
        activities, 
        timetable_id
    )
    
    return {
        "valid": not (internal_conflicts or cross_timetable_conflicts),
        "internal_conflicts": internal_conflicts,
        "cross_timetable_conflicts": cross_timetable_conflicts
    }


def clean_mongo_documents(doc):
    if isinstance(doc, list):
        return [clean_mongo_documents(item) for item in doc]
    if isinstance(doc, dict):
        return {key: clean_mongo_documents(value) for key, value in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    return doc

def store_latest_score(score):
    db["settings"].update_one(
        {"option": "latest_score"},
        {"$set": {"value": score}},
        upsert=True
    )
    db["old_scores"].insert_one({"value": score})

