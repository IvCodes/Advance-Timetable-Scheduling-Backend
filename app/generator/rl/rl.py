import pickle
import numpy as np
from typing import List, Dict
from app.generator.data_collector import *
import random

class SchedulingEnvironment:
    def __init__(self):
        self.days = get_days()
        self.facilities = get_spaces()
        self.periods = get_periods()
        self.activities = get_activities()
        self.students = get_students()
        self.teachers = get_teachers()
        self.state = None 

    def reset(self):
        self.state = {
            "schedule": [],
            "conflicts": {"teacher": 0, "room": 0, "interval": 0, "period": 0}
        }
        return self.state

    def step(self, action):
        activity, day, periods, room, teacher, subgroup, subject, duration = action
        num_of_students = len([s for s in self.students if activity["subject"] in s["subjects"]])

        if room["capacity"] < num_of_students:
            return -10 
        else:
            reward = 10 

        conflicts = self._calculate_conflicts(activity, day, periods, room, teacher)
        reward -= sum(conflicts.values()) * 2  

        self.state["schedule"].append({
            "activity_id": activity["code"],
            "day": day,
            "period": periods,
            "room": room,
            "teacher": teacher,
            "duration": activity["duration"],
            
        })
        self.state["conflicts"] = conflicts
        return reward

    def _calculate_conflicts(self, activity, day, periods, room, teacher):
        conflicts = {"teacher": 0, "room": 0, "interval": 0, "period": 0}
        for entry in self.state["schedule"]:
            if entry["day"] == day:
                for period in periods:
                    if period in entry["period"]:
                        if entry["room"]["code"] == room["code"]:
                            conflicts["room"] += 1
                        if entry["teacher"] == teacher:
                            conflicts["teacher"] += 1
        return conflicts


class QLearningScheduler:
    def __init__(self, env, model_path):
        self.env = env
        self.q_table = None
        self.load_model(model_path)

    def load_model(self, filepath):
        with open(filepath, "rb") as f:
            self.q_table = pickle.load(f)

    def create_schedule(self):
        state = self.env.reset()
        schedule = []

        for activity in self.env.activities:
            current_state = tuple(state["conflicts"].values())

            best_action_index = np.argmax(self.q_table[current_state])
            action = self._decode_action(best_action_index, activity)
            
            reward = self.env.step(action)
            if reward > 0: 
                schedule.append({
                    "activity": activity["code"],
                    "day": action[1],
                    "period": action[2],
                    "room": action[3],
                    "teacher": action[4],
                    "subgroup": activity["subgroup_ids"][0],
                    "duration": activity["duration"],
                    "subject": activity["subject"]

                })

        return schedule

    def _decode_action(self, action_index, activity):
        day = random.choice(self.env.days)
        start_period = self.env.periods[action_index]
        duration = activity["duration"]

        period_index = self.env.periods.index(start_period)
        if period_index + duration <= len(self.env.periods):
            periods = self.env.periods[period_index:period_index + duration]
        else:
            periods = self.env.periods[period_index:] + self.env.periods[:(period_index + duration) % len(self.env.periods)]
        room = random.choice(self.env.facilities)
        teacher = random.choice(activity["teacher_ids"])
        subgroup = activity["subgroup_ids"][0]
        subject = activity["subject"]
        duration = activity["duration"]
        return activity, day, periods, room, teacher, subgroup, subject, duration


def generate_rl():
    env = SchedulingEnvironment()
    scheduler = QLearningScheduler(env, "scheduler_model.pkl")

    print("Generating schedule using the trained model...")
    schedule = scheduler.create_schedule()
    print("Schedule generated successfully!")
    for entry in schedule:
        print(entry)
    return schedule
