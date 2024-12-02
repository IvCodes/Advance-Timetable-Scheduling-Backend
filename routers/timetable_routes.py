from fastapi import APIRouter, HTTPException, Depends
from database import db
from typing import List
from generator.algorithms.ga.ga import *
from generator.algorithms.co.co_v2 import *
# from generator.algorithms.rl.rl_train import *
from generator.algorithms.rl.rl import *
from generator.algorithms.eval.eval import *

from models.timetable_model import Timetable


router = APIRouter()

@router.post("/generate")
async def generate_timetable():
    pop, log, hof, li = generate_ga()
    save_timetable(li, "GA")
    sol = generate_co()
    save_timetable(sol, "CO")
    gen = generate_rl()
    save_timetable(gen, "RL")
    eval = evaluate()
    for algorithm, scores in eval.items():
        average_score = sum(scores) / len(scores)
        eval[algorithm] = {
            "average_score": average_score,
        }
    return {"message": "Timetable generated", "eval": eval }

def save_timetable(li, algorithm):
    subgroups = [
        "SEM101", "SEM102", "SEM201", "SEM202",
        "SEM301", "SEM302", "SEM401", "SEM402"
    ]
    semester_timetables = {semester: [] for semester in subgroups}  

    for activity in li:
        subgroup_id = activity["subgroup"] 
        semester_timetables[subgroup_id].append(activity)
    index = 0
    for semester, activities in semester_timetables.items():
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
             "timetable": activities},
            upsert=True
        )
        index +=1
#generate unique timetable codes for each algorithm and semester       
def generate_timetable_code(index, algorithm):
    return f"{algorithm}-TT000{index}"

@router.get("/timetables")
async def get_timetables():
    timetables = list(db["Timetable"].find())
    cleaned_timetables = clean_mongo_documents(timetables)
    eval =  evaluate()
    for algorithm, scores in eval.items():
        average_score = sum(scores) / len(scores)
        eval[algorithm] = {
            "average_score": average_score,
        }
    
    out ={
        "timetables": cleaned_timetables,
        "eval": eval
    }
    
    return out

from bson import ObjectId

def clean_mongo_documents(doc):
    if isinstance(doc, list):
        return [clean_mongo_documents(item) for item in doc]
    if isinstance(doc, dict):
        return {key: clean_mongo_documents(value) for key, value in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    return doc