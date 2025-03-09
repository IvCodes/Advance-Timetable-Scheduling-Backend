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
    # pop, log, hof, li = generate_ga()
    # save_timetable(li, "GA", current_user)
    sol = generate_co()
    save_timetable(sol, "CO", current_user)
    # bee_sol = generate_bc()
    # save_timetable(bee_sol, "BC", current_user)
    # pso_sol = generate_pso()
    # save_timetable(pso_sol, "PSO", current_user)
    # gen = generate_rl()
    # save_timetable(gen, "RL", current_user)
    eval = evaluate()
    store_latest_score(eval)
    for algorithm, scores in eval.items():
        average_score = sum(scores) / len(scores)
        eval[algorithm] = {
            "average_score": average_score,
        }

    db["notifications"].insert_one({"message": "Latest evaluation results available", "type": "success", "read": False, "recipient": current_user["id"]})
    return {"message": "Timetable generated", "eval": eval }

def map_subgroup_to_semester(subgroup_id):
    """
    Map activity subgroup format (like 'Y1S1.IT.1') to semester format (like 'SEM101')
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
    
    if subgroup_id in mapping:
        return mapping[subgroup_id]
    
    # If the subgroup_id contains a dot, try to get the part before the first dot
    if isinstance(subgroup_id, str) and '.' in subgroup_id:
        parts = subgroup_id.split('.', 1)
        if parts[0] in mapping:
            return mapping[parts[0]]
    
    return None  # No mapping found

def save_timetable(li, algorithm, current_user):
    # Check if li is None
    if li is None:
        print(f"Warning: No timetable data received for algorithm {algorithm}. Nothing to save.")
        db["notifications"].insert_one({
            "message": f"Failed to generate timetable using {algorithm}. No data was produced.",
            "type": "error",
            "read": False,
            "recipient": current_user["id"]
        })
        return

    subgroups = [
        "SEM101", "SEM102", "SEM201", "SEM202",
        "SEM301", "SEM302", "SEM401", "SEM402"
    ]
    # Ensure a proper mapping from semester to activities
    semester_timetables = {semester: [] for semester in subgroups}

    for activity in li:
        # Handle multiple subgroups case
        if isinstance(activity["subgroup"], list):
            subgroup_ids = activity["subgroup"]
        else:
            subgroup_ids = [activity["subgroup"]]
        
        print(f"Processing activity with subgroups: {subgroup_ids}")
        
        # Try to map each subgroup to a semester
        mapped = False
        for subgroup_id in subgroup_ids:
            mapped_id = map_subgroup_to_semester(subgroup_id)
            print(f"Mapped {subgroup_id} to {mapped_id}")
            
            if mapped_id and mapped_id in semester_timetables:
                semester_timetables[mapped_id].append(activity)
                mapped = True
                print(f"Added activity to {mapped_id}")
        
        if not mapped:
            print(f"Warning: Could not map any subgroup in: {subgroup_ids}")
            print(f"Activity will be skipped: {activity}")

    # Ensure order is maintained before inserting into DB
    sorted_semesters = sorted(semester_timetables.keys(), key=lambda x: subgroups.index(x))
    
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

    db["notifications"].insert_one({
        "message": f"New timetable generated using {algorithm}",
        "type": "success",
        "read": False,
        "recipient": current_user["id"]
    })

    

def generate_timetable_code(index, algorithm):
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

@router.put("/timetable/{timetable_id}")
async def edit_timetable(
    timetable_id: str,
    timetable_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Edit an existing timetable with conflict checking and validation
    """
    try:
        # Extract the activities list from the timetable data
        updated_activities = timetable_data.get("timetable", [])
        algorithm = timetable_data.get("algorithm")
        
        if not isinstance(updated_activities, list):
            raise HTTPException(
                status_code=400,
                detail="Invalid timetable format - expected 'timetable' field to be a list"
            )

        if not algorithm:
            raise HTTPException(
                status_code=400,
                detail="Algorithm field is required"
            )

        # Initialize conflict checker
        checker = ConflictChecker(db)
        
        # Validate timetable exists
        timetable = db["Timetable"].find_one({"_id": ObjectId(timetable_id)})
        if not timetable:
            raise HTTPException(status_code=404, detail="Timetable not found")
        
        # Validate activity structure
        validation_errors = checker.validate_activities(updated_activities)
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Invalid activity data",
                    "errors": validation_errors
                }
            )
        
        # Check for conflicts within the updated activities
        internal_conflicts = checker.check_single_timetable_conflicts(timetable_id, updated_activities)
        
        # Check for conflicts with other timetables
        cross_timetable_conflicts = checker.check_cross_timetable_conflicts(
            updated_activities, 
            timetable_id,
            algorithm
        )
        
        # Combine all conflicts
        all_conflicts = internal_conflicts + cross_timetable_conflicts
        
        if all_conflicts:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Conflicts detected",
                    "conflicts": all_conflicts
                }
            )
        
        # Store the previous state for history
        db["timetable_history"].insert_one({
            "timetable_id": ObjectId(timetable_id),
            "previous_state": timetable["timetable"],
            "new_state": updated_activities,
            "modified_by": current_user["id"],
            "modified_at": datetime.now()
        })
        
        # Update only the changed activities in the timetable
        existing_activities = timetable.get("timetable", [])
        updated_activities_dict = {activity["activity_id"]: activity for activity in updated_activities}
        for i, activity in enumerate(existing_activities):
            if activity["activity_id"] in updated_activities_dict:
                existing_activities[i] = updated_activities_dict[activity["activity_id"]]
        
        # Update the timetable with the modified activities
        update_data = {
            "timetable": existing_activities,
            "last_modified": datetime.now(),
            "modified_by": current_user["id"]
        }
        # Add other fields from timetable_data if they exist
        for key in ["code", "algorithm", "semester"]:
            if key in timetable_data:
                update_data[key] = timetable_data[key]

        result = db["Timetable"].update_one(
            {"_id": ObjectId(timetable_id)},
            {"$set": update_data}
        )
       
        if result.modified_count == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to update activity"
            )
        
        # Create notifications for other admin users
        other_admins = list(db["users"].find({
            "role": "admin",
            "id": {"$ne": current_user["id"]}
        }))
        
        # Only insert notifications if there are other admin users
        if other_admins:
            notifications = [
                {
                    "message": f"Activity {activity_id} in timetable {timetable['code']} has been updated",
                    "type": "info",
                    "read": False,
                    "recipient": admin["id"],
                    "created_at": datetime.now(),
                    "timetable_code": timetable["code"],
                    "modified_by": current_user["id"]
                }
                for admin in other_admins
            ]
            if notifications:  # Double check we have notifications to insert
                db["notifications"].insert_many(notifications)
        
        return {
            "message": "Activity updated successfully",
            "timetable_code": timetable["code"],
            "activity_id": timetable_data["timetable"][0]["activity_id"] if timetable_data["timetable"] else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while updating the activity: {str(e)}"
        )

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
