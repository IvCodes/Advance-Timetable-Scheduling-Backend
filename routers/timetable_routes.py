from fastapi import APIRouter, HTTPException, Depends
from utils.database import db
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

