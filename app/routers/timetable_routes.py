import logging
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from bson import ObjectId

# --- Adjust these imports to match your actual paths ---
from app.utils.database import db
from app.Services.timetable_notification import create_timetable_notification
from app.generator.algorithms.ga.ga import generate_ga
from app.generator.algorithms.co.co_v2 import generate_co
from app.generator.algorithms.rl.rl import generate_rl
from app.generator.algorithms.bc.bc_v1 import generate_bco
from app.generator.algorithms.pso.pso_v1 import generate_pso

def get_current_user():
    return {"id": "admin"} 

class ConflictChecker:
    """
    Placeholder for your conflict-checking logic.
    You can replace this with your real code.
    """
    def __init__(self, db):
        self.db = db

    def validate_activities(self, activities):
        return []

    def check_single_timetable_conflicts(self, timetable_id, updated_activities, ignore_session_id=None):
        return []

    def check_cross_timetable_conflicts(self, updated_activities, timetable_id, algorithm):
        return []


router = APIRouter()

class AlgorithmEvaluation(BaseModel):
    """Model for timetable algorithm evaluation input"""
    scores: Dict[str, Dict[str, float]]


def map_subgroup_to_semester(subgroup_id: str) -> Optional[str]:
    """
    Converts subgroup notation like "Y1S1.IT.1" or "Y1S1" to a standardized
    semester code like "SEM101".
    Adjust as needed for your naming convention.
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
    if "." in subgroup_id:
        prefix = subgroup_id.split(".", 1)[0]
        if prefix in mapping:
            return mapping[prefix]
    return None


def generate_timetable_code(index: int, algorithm: str) -> str:
    """Generates a code for each timetable, e.g. 'GA-TT0000'."""
    return f"{algorithm}-TT000{index}"


def clean_mongo_documents(doc):
    """Recursively convert ObjectId fields to strings for JSON-serializable data."""
    if isinstance(doc, list):
        return [clean_mongo_documents(item) for item in doc]
    if isinstance(doc, dict):
        return {key: clean_mongo_documents(value) for key, value in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    return doc


def evaluate_timetables():
    """
    Placeholder function that returns evaluation scores for each algorithm.
    Replace or expand with your actual evaluation logic.
    """
    # Example: dictionary of {algorithm: [scores,...]}
    # or something more sophisticated
    return {
        "GA": [0.85, 0.80],
        "CO": [0.78, 0.82],
        "RL": [0.90, 0.88],
        "BC": [0.75, 0.77],
        "PSO": [0.83, 0.81]
    }


def evaluate():
    """Wrap the above function in a simpler call if you like."""
    return evaluate_timetables()


def save_timetable(li, algorithm, current_user=None):
    """
    Unified save_timetable that:
      - uses map_subgroup_to_semester
      - upserts each semester’s data into the Timetable collection
      - optionally logs to old_timetables
      - optionally notifies current_user
    """
    if not li:
        logging.warning(f"No timetable data to save for algorithm: {algorithm}")
        return False

    valid_semesters = ["SEM101", "SEM102", "SEM201", "SEM202",
                       "SEM301", "SEM302", "SEM401", "SEM402"]
    semester_timetables = {sem: [] for sem in valid_semesters}

    # Group activities by mapped semester
    for activity in li:
        if "algorithm" not in activity:
            activity["algorithm"] = algorithm

        subgroups = activity.get("subgroup", [])
        if isinstance(subgroups, str):
            subgroups = [subgroups]

        mapped_something = False
        for sg in subgroups:
            sem = map_subgroup_to_semester(sg)
            if sem and sem in semester_timetables:
                semester_timetables[sem].append(activity)
                mapped_something = True
                # break if each activity truly belongs to only one semester
                break

        if not mapped_something:
            logging.warning(f"Could not map subgroups {subgroups} to any known semester. Activity: {activity}")

    index = 0
    success = False

    for semester, activities in semester_timetables.items():
        if not activities:
            continue
        try:
            # Upsert into Timetable
            result = db["Timetable"].replace_one(
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
            if result.acknowledged:
                success = True

            # Optionally store history
            db["old_timetables"].insert_one({
                "code": generate_timetable_code(index, algorithm),
                "algorithm": algorithm,
                "semester": semester,
                "timetable": activities,
                "date_created": datetime.now()
            })

            index += 1

        except Exception as e:
            logging.error(f"Failed to save timetable for semester {semester}: {str(e)}")

    # Send a notification if a user is logged in
    if current_user:
        db["notifications"].insert_one({
            "message": f"New timetable generated using {algorithm}",
            "type": "success" if success else "error",
            "read": False,
            "recipient": current_user["id"]
        })

    return success

@router.post("/generate")
async def generate_timetable(current_user: dict = Depends(get_current_user)):
    """
    Launch a background thread that runs GA, CO, RL, BC, PSO in sequence.
    Each algorithm’s result is saved to the Timetable collection.
    """
    logger = logging.getLogger(__name__)

    def generate():
        logger.info("Starting multi-algorithm timetable generation")
        results = {
            "GA": False,
            "CO": False,
            "RL": False,
            "BC": False,
            "PSO": False
        }

        # GA
        try:
            logger.info("Running GA ...")
            time.sleep(0.3)
            pop, log, hof, li_ga = generate_ga()  # or your actual signature
            results["GA"] = save_timetable(li_ga, "GA", current_user)
            create_timetable_notification("GA", results["GA"])
            logger.info(f"GA completed - success: {results['GA']}")
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"GA failed: {str(e)}")
            create_timetable_notification("GA", False)

        # CO
        try:
            logger.info("Running CO ...")
            time.sleep(0.3)
            sol_co = generate_co()
            results["CO"] = save_timetable(sol_co, "CO", current_user)
            create_timetable_notification("CO", results["CO"])
            logger.info(f"CO completed - success: {results['CO']}")
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"CO failed: {str(e)}")
            create_timetable_notification("CO", False)

        # RL
        try:
            logger.info("Running RL ...")
            time.sleep(0.3)
            gen_rl = generate_rl()
            results["RL"] = save_timetable(gen_rl, "RL", current_user)
            create_timetable_notification("RL", results["RL"])
            logger.info(f"RL completed - success: {results['RL']}")
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"RL failed: {str(e)}")
            create_timetable_notification("RL", False)

        # BC
        try:
            logger.info("Running BC ...")
            time.sleep(0.3)
            bc_sol = generate_bco()
            results["BC"] = save_timetable(bc_sol, "BC", current_user)
            create_timetable_notification("BC", results["BC"])
            logger.info(f"BC completed - success: {results['BC']}")
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"BC failed: {str(e)}")
            create_timetable_notification("BC", False)

        # PSO
        try:
            logger.info("Running PSO ...")
            time.sleep(0.3)
            pso_sol = generate_pso()
            results["PSO"] = save_timetable(pso_sol, "PSO", current_user)
            create_timetable_notification("PSO", results["PSO"])
            logger.info(f"PSO completed - success: {results['PSO']}")
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"PSO failed: {str(e)}")
            create_timetable_notification("PSO", False)

        # Evaluate
        logger.info("Evaluating results ...")
        eval_results = evaluate()
        for algo, scores in eval_results.items():
            avg_score = sum(scores) / len(scores)
            logger.info(f"{algo} average score: {avg_score:.2f}")
        time.sleep(0.3)

        # Summarize
        successful_count = sum(1 for r in results.values() if r)
        if successful_count > 0:
            logger.info(f"Timetables generated successfully in {successful_count} of 5 algorithms.")
        else:
            logger.warning("All timetable generation algorithms failed.")

    # Start in background
    thread = threading.Thread(target=generate, daemon=True)
    thread.start()

    return {"status": "processing", "message": "Timetable generation started in background"}


# -------------------------------------------------------------------
# Timetable retrieval & evaluation
# -------------------------------------------------------------------

@router.get("/timetables")
async def get_timetables():
    """Retrieve all timetables from DB, plus a simple summary of evaluations."""
    timetables = list(db["Timetable"].find())
    cleaned_timetables = clean_mongo_documents(timetables)

    eval_scores = evaluate()
    # Convert raw lists to dict with average_score
    final_eval = {}
    for algorithm, scores in eval_scores.items():
        if scores:
            average_score = sum(scores) / len(scores)
            final_eval[algorithm] = {"average_score": average_score}

    return {
        "timetables": cleaned_timetables,
        "eval": final_eval
    }


@router.post("/evaluate-algorithms")
async def evaluate_algorithms(evaluation: AlgorithmEvaluation):
    """
    Example of an endpoint that accepts new evaluation metrics
    and returns some analysis. (In the main code, it uses a large language model.)
    You can adapt this as needed or remove it if you don’t need LLM-based analysis.
    """
    try:
        # Combine the user-provided scores with your local evaluation if desired
        user_scores = evaluation.scores

        # Suppose we just return them, or run a combined analysis:
        combined = {}
        for algo, metric_dict in user_scores.items():
            combined[algo] = {}
            for metric, value in metric_dict.items():
                combined[algo][metric] = value

        # Insert or update in DB if desired
        # db["AlgorithmScores"].insert_one({"timestamp": datetime.now(), "scores": combined})

        return {"analysis": "Stub analysis of your algorithm scores.", "combined": combined}

    except Exception as e:
        logging.error(f"Failed to evaluate algorithms: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/select")
async def select_algorithm(algorithm: dict, current_user: dict = Depends(get_current_user)):
    """
    Store the user’s preferred algorithm in a DB collection (AlgorithmSelection).
    """
    try:
        algorithm_name = algorithm.get("algorithm")
        if not algorithm_name:
            raise HTTPException(status_code=400, detail="Algorithm name is required")
        if algorithm_name not in ["GA", "CO", "RL", "BC", "PSO"]:
            raise HTTPException(status_code=400, detail="Invalid algorithm name")

        selection_exists = db["AlgorithmSelection"].find_one({})
        if selection_exists:
            db["AlgorithmSelection"].update_one(
                {"_id": selection_exists["_id"]},
                {"$set": {"selected_algorithm": algorithm_name}}
            )
        else:
            db["AlgorithmSelection"].insert_one({"selected_algorithm": algorithm_name})

        return {"message": f"Selected algorithm: {algorithm_name}", "success": True}

    except Exception as e:
        logging.error(f"Error selecting algorithm: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error selecting algorithm: {str(e)}")


@router.get("/selected")
async def get_selected_algorithm():
    """
    Return whichever algorithm was last stored as 'selected'.
    """
    try:
        data = db["AlgorithmSelection"].find_one()
        if data:
            return {"selected_algorithm": data.get("selected_algorithm")}
        else:
            return {"selected_algorithm": None}
    except Exception as e:
        logging.error(f"Failed to get selected algorithm: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get selected algorithm: {str(e)}")


@router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    """Get all notifications for the current user (or all, if you prefer)."""
    try:
        if "notifications" not in db.list_collection_names():
            db.create_collection("notifications")

        # Example: only unread for the current user
        notifications = list(db["notifications"].find({
            "recipient": current_user["id"]
        }))

        for n in notifications:
            n["_id"] = str(n["_id"])
        return notifications
    except Exception as e:
        logging.error(f"Error retrieving notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/mark-all-read")
async def mark_all_notifications_read(current_user: dict = Depends(get_current_user)):
    """Mark all unread notifications for the current user as read."""
    try:
        unread_count = db["notifications"].count_documents({
            "recipient": current_user["id"],
            "read": False
        })
        if unread_count == 0:
            return {"success": True, "modified_count": 0, "message": "No unread notifications found"}

        result = db["notifications"].update_many(
            {"recipient": current_user["id"], "read": False},
            {"$set": {"read": True}}
        )

        return {
            "success": True,
            "modified_count": result.modified_count,
            "matched_count": result.matched_count
        }
    except Exception as e:
        logging.error(f"Error marking all notifications as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{notification_id}")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a single notification as read."""
    try:
        result = db["notifications"].update_one(
            {"_id": ObjectId(notification_id), "recipient": current_user["id"]},
            {"$set": {"read": True}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"message": "Notification marked as read"}
    except Exception as e:
        logging.error(f"Error updating notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update notification: {str(e)}")


NO_PUBLISHED_TIMETABLE = "No published timetable found"
NO_ACTIVE_PUBLISHED_TIMETABLE = "No active published timetable found"
SEMESTER_NOT_FOUND = "Semester not found in published timetable"
ENTRY_INDEX_OUT_OF_RANGE = "Entry index is out of range"


@router.post("/publish")
async def publish_timetable(algorithm: str, current_user: dict = Depends(get_current_user)):
    """
    Create a published timetable from the selected algorithm's timetables.
    This timetable becomes the active one for faculty/students.
    """
    try:
        current_user_id = current_user["id"]

        timetables = list(db["Timetable"].find({"algorithm": algorithm}))
        if not timetables:
            raise HTTPException(
                status_code=404,
                detail=f"No timetables found for algorithm {algorithm}"
            )

        # Organize by semester
        semesters = {}
        timetable_ids = []
        for timetable in timetables:
            sem = timetable["semester"]
            timetable_ids.append(str(timetable["_id"]))
            semesters[sem] = timetable["timetable"]

        # Archive existing active timetable
        db["PublishedTimetable"].update_many(
            {"status": "active"},
            {"$set": {"status": "archived"}}
        )

        source = {
            "algorithm": algorithm,
            "timetable_ids": timetable_ids
        }

        published_timetable = {
            "version": 1,
            "status": "active",
            "published_date": datetime.now(),
            "published_by": current_user_id,
            "source": source,
            "semesters": semesters,
        }

        result = db["PublishedTimetable"].insert_one(published_timetable)
        create_timetable_notification(algorithm, True)

        return {
            "success": True,
            "message": f"Timetable from {algorithm} published successfully",
            "id": str(result.inserted_id)
        }

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logging.error(f"Failed to publish timetable: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to publish timetable: {str(e)}")


@router.get("/published")
async def get_published_timetable():
    """Get the active published timetable (all semesters)."""
    try:
        published = db["PublishedTimetable"].find_one({"status": "active"})
        if not published:
            return {"message": NO_ACTIVE_PUBLISHED_TIMETABLE}

        return clean_mongo_documents(published)

    except Exception as e:
        logging.error(f"Failed to get published timetable: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/published/faculty/{faculty_id}")
async def get_faculty_timetable(faculty_id: str):
    """
    Get the published timetable filtered for a specific faculty member.
    (teacher or substitute).
    """
    try:
        published = db["PublishedTimetable"].find_one({"status": "active"})
        if not published:
            return {"message": NO_ACTIVE_PUBLISHED_TIMETABLE}

        faculty_timetable = {}
        for semester, entries in published["semesters"].items():
            fac_entries = []
            for entry in entries:
                if entry.get("teacher") == faculty_id or entry.get("substitute") == faculty_id:
                    fac_entries.append(entry)
            if fac_entries:
                faculty_timetable[semester] = fac_entries

        return {
            "_id": str(published["_id"]),
            "version": published["version"],
            "published_date": published["published_date"],
            "semesters": faculty_timetable
        }

    except Exception as e:
        logging.error(f"Failed to get faculty timetable: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/published/student/{semester}")
async def get_student_timetable(semester: str):
    """
    Get the published timetable for a specific semester (student view).
    """
    try:
        published = db["PublishedTimetable"].find_one({"status": "active"})
        if not published:
            return {"message": NO_ACTIVE_PUBLISHED_TIMETABLE}

        semester_entries = published["semesters"].get(semester, [])
        return {
            "_id": str(published["_id"]),
            "version": published["version"],
            "published_date": published["published_date"],
            "semester": semester,
            "entries": semester_entries
        }

    except Exception as e:
        logging.error(f"Failed to get student timetable: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/published/entry")
async def update_timetable_entry(
    semester: str,
    entry_index: int,
    room: Optional[Dict] = None,
    teacher: Optional[str] = None,
    period: Optional[List[Dict]] = None,
    day: Optional[Dict] = None,
    subject: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update a specific entry in the published timetable (admin use)."""
    try:
        current_user_id = current_user["id"]
        published = db["PublishedTimetable"].find_one({"status": "active"})
        if not published:
            raise HTTPException(status_code=404, detail=NO_ACTIVE_PUBLISHED_TIMETABLE)

        if semester not in published["semesters"]:
            raise HTTPException(status_code=404, detail=SEMESTER_NOT_FOUND)

        if entry_index < 0 or entry_index >= len(published["semesters"][semester]):
            raise HTTPException(status_code=404, detail=ENTRY_INDEX_OUT_OF_RANGE)

        entry = published["semesters"][semester][entry_index]
        if "original_teacher" not in entry:
            entry["original_teacher"] = entry.get("teacher", "Unknown")

        modification = {
            "modified_at": datetime.now(),
            "modified_by": current_user_id,
            "reason": "Administrative update"
        }

        update_fields = {}
        if room is not None:
            update_fields[f"semesters.{semester}.{entry_index}.room"] = room
        if teacher is not None:
            update_fields[f"semesters.{semester}.{entry_index}.teacher"] = teacher
        if period is not None:
            update_fields[f"semesters.{semester}.{entry_index}.period"] = period
        if day is not None:
            update_fields[f"semesters.{semester}.{entry_index}.day"] = day
        if subject is not None:
            update_fields[f"semesters.{semester}.{entry_index}.subject"] = subject

        update_fields[f"semesters.{semester}.{entry_index}.modification"] = modification
        update_fields["version"] = published["version"] + 1

        result = db["PublishedTimetable"].update_one(
            {"_id": published["_id"]},
            {"$set": update_fields}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update timetable entry")

        create_timetable_notification("timetable_update", True)
        return {
            "success": True,
            "message": "Timetable entry updated successfully",
            "semester": semester,
            "entry_index": entry_index
        }

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logging.error(f"Failed to update timetable entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/published/substitute")
async def assign_substitute(
    semester: str,
    entry_index: int,
    substitute: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Assign a substitute teacher to a published timetable entry."""
    try:
        published = db["PublishedTimetable"].find_one({"status": "active"})
        if not published:
            raise HTTPException(status_code=404, detail=NO_ACTIVE_PUBLISHED_TIMETABLE)
        if semester not in published["semesters"]:
            raise HTTPException(status_code=404, detail=SEMESTER_NOT_FOUND)
        if entry_index < 0 or entry_index >= len(published["semesters"][semester]):
            raise HTTPException(status_code=404, detail=ENTRY_INDEX_OUT_OF_RANGE)

        entry = published["semesters"][semester][entry_index]
        if "original_teacher" not in entry:
            entry["original_teacher"] = entry.get("teacher", "Unknown")

        modification = {
            "modified_at": datetime.now(),
            "type": "substitute_assigned",
            "field": "teacher",
            "previous_value": entry.get("teacher"),
            "new_value": substitute,
            "reason": reason or "No reason provided"
        }

        update_fields = {
            f"semesters.{semester}.{entry_index}.substitute": substitute,
            f"semesters.{semester}.{entry_index}.modification": modification,
            "version": published["version"] + 1
        }

        if "original_teacher" in entry and entry["original_teacher"]:
            update_fields[f"semesters.{semester}.{entry_index}.teacher"] = entry["original_teacher"]

        update = {
            "$set": update_fields
        }

        # Optionally remove a previous substitute if you only store one
        # at a time. Otherwise, you can keep them. For example:
        # "$unset": {
        #   f"semesters.{semester}.{entry_index}.substitute": "",
        #   ...
        # }

        result = db["PublishedTimetable"].update_one(
            {"_id": published["_id"]},
            update
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to assign substitute teacher")

        create_timetable_notification("substitute_assigned", True)
        return {
            "success": True,
            "message": "Substitute teacher assigned successfully",
            "semester": semester,
            "entry_index": entry_index,
            "substitute": substitute,
            "original_teacher": entry.get("original_teacher")
        }

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logging.error(f"Failed to assign substitute teacher: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/published/remove-substitute")
async def remove_substitute(
    semester: str,
    entry_index: int,
    current_user: dict = Depends(get_current_user)
):
    """Remove a substitute teacher, restoring the original teacher if recorded."""
    try:
        current_user_id = current_user["id"]
        published = db["PublishedTimetable"].find_one({"status": "active"})
        if not published:
            raise HTTPException(status_code=404, detail=NO_ACTIVE_PUBLISHED_TIMETABLE)
        if semester not in published["semesters"]:
            raise HTTPException(status_code=404, detail=SEMESTER_NOT_FOUND)
        if entry_index < 0 or entry_index >= len(published["semesters"][semester]):
            raise HTTPException(status_code=404, detail=ENTRY_INDEX_OUT_OF_RANGE)

        entry = published["semesters"][semester][entry_index]
        if "substitute" not in entry or not entry["substitute"]:
            return {
                "success": True,
                "message": "No substitute teacher to remove",
                "semester": semester,
                "entry_index": entry_index
            }

        modification = {
            "modified_at": datetime.now(),
            "modified_by": current_user_id,
            "reason": "Substitute teacher removed"
        }

        update_fields = {
            "version": published["version"] + 1,
            f"semesters.{semester}.{entry_index}.modification": modification
        }
        if "original_teacher" in entry and entry["original_teacher"]:
            update_fields[f"semesters.{semester}.{entry_index}.teacher"] = entry["original_teacher"]

        update = {
            "$set": update_fields,
            "$unset": {
                f"semesters.{semester}.{entry_index}.substitute": "",
                f"semesters.{semester}.{entry_index}.original_teacher": ""
            }
        }

        result = db["PublishedTimetable"].update_one(
            {"_id": published["_id"]},
            update
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to remove substitute teacher")

        create_timetable_notification("substitute_removed", True)
        return {
            "success": True,
            "message": "Substitute teacher removed successfully",
            "semester": semester,
            "entry_index": entry_index
        }

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logging.error(f"Failed to remove substitute teacher: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


#Mannual Editing 
@router.patch("/timetable/{timetable_id}/activity/{session_id}")
async def super_update_session(
    timetable_id: str,
    session_id: str,
    partial_data: Dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Partially update (PATCH) a single scheduled session in a timetable.
    Confirms no conflicts before saving. If conflicts -> no update.
    """
    checker = ConflictChecker(db)

    # 1) Retrieve
    timetable = db["Timetable"].find_one({"_id": ObjectId(timetable_id)})
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")

    existing_activities = timetable.get("timetable", [])
    target_session = None
    for activity in existing_activities:
        if activity.get("session_id") == session_id:
            target_session = activity
            break
    if not target_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2) Apply partial changes to a copy
    updated_session = dict(target_session)
    for k, v in partial_data.items():
        if k == "session_id":
            continue  # skip or raise error, as session_id is the key
        updated_session[k] = v

    # 3) Check conflicts
    conflicts_internal = checker.check_single_timetable_conflicts(
        timetable_id,
        [updated_session],
        ignore_session_id=session_id
    )
    algorithm = timetable.get("algorithm", "")
    conflicts_cross = checker.check_cross_timetable_conflicts(
        [updated_session],
        timetable_id,
        algorithm
    )

    all_conflict = conflicts_internal + conflicts_cross

    if all_conflict:
        return {
            "message": "Conflicts detected. Changes not saved.",
            "conflicts": all_conflict,
           
        }

    # 4) No conflicts -> commit
    new_activities = []
    for act in existing_activities:
        if act.get("session_id") == session_id:
            new_activities.append(updated_session)
        else:
            new_activities.append(act)

    db["Timetable"].update_one(
        {"_id": ObjectId(timetable_id)},
        {"$set": {"timetable": new_activities}}
    )

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
    Check for potential internal or cross-timetable conflicts without saving changes.
    """
    checker = ConflictChecker(db)

    validation_errors = checker.validate_activities(activities)
    if validation_errors:
        return {
            "valid": False,
            "validation_errors": validation_errors
        }

    internal_conflicts = checker.check_single_timetable_conflicts(timetable_id, activities)
    algorithm = ""
    existing_tt = db["Timetable"].find_one({"_id": ObjectId(timetable_id)})
    if existing_tt:
        algorithm = existing_tt.get("algorithm", "")

    cross_timetable_conflicts = checker.check_cross_timetable_conflicts(activities, timetable_id, algorithm)

    return {
        "valid": not (internal_conflicts or cross_timetable_conflicts),
        "internal_conflicts": internal_conflicts,
        "cross_timetable_conflicts": cross_timetable_conflicts
    }
