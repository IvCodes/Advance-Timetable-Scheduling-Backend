import pickle
import numpy as np
from typing import List, Dict
from app.generator.data_collector import *
import random
from collections import defaultdict
import logging

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
            reward = -10 
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
            "subgroup": subgroup,
            "subject": subject
        })
        self.state["conflicts"] = conflicts
        
        # Check if we're done (all activities scheduled)
        done = len(self.state["schedule"]) >= len(self.activities)
        
        return self.state, reward, done

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
    def __init__(self, env, model_path=None):
        self.env = env
        self.q_table = defaultdict(lambda: np.zeros(len(self.env.periods)))
        
        if model_path:
            try:
                self.load_model(model_path)
            except FileNotFoundError:
                # If model doesn't exist, create a basic model
                print(f"Model file {model_path} not found. Using default Q-table.")
                # Train for a few episodes to get a basic model
                self.alpha = 0.1 
                self.gamma = 0.99 
                self.epsilon = 0.1
                self.train(episodes=50)
            except Exception as e:
                print(f"Error loading model: {str(e)}. Using default Q-table.")

    def load_model(self, filepath):
        with open(filepath, "rb") as f:
            self.q_table = defaultdict(lambda: np.zeros(len(self.env.periods)), pickle.load(f))
            
    def train(self, episodes=1000):
        for episode in range(episodes):
            state = self.env.reset()
            total_reward = 0
            
            while True:
                current_state = tuple(state["conflicts"].values())
                if random.uniform(0, 1) < self.epsilon:
                    action_index = random.randint(0, len(self.env.periods) - 1)
                else:
                    action_index = np.argmax(self.q_table[current_state])
                    
                action = self._decode_action(action_index)
                next_state, reward, done = self.env.step(action)
                next_state_tuple = tuple(next_state["conflicts"].values())
                
                old_value = self.q_table[current_state][action_index]
                next_max = np.max(self.q_table[next_state_tuple])
                
                new_value = old_value + self.alpha * (reward + self.gamma * next_max - old_value)
                self.q_table[current_state][action_index] = new_value
                
                state = next_state
                total_reward += reward
                
                if done:
                    break

    def create_schedule(self):
        state = self.env.reset()
        schedule = []

        for activity in self.env.activities:
            current_state = tuple(state["conflicts"].values())

            # Find best action for this activity
            best_action_index = np.argmax(self.q_table[current_state])
            action = self._decode_action(best_action_index, activity)
            
            new_state, reward, done = self.env.step(action)
            if reward > 0: 
                # Format to match the format expected by the frontend
                day_obj = action[1] or {}
                period_obj = action[2][0] if action[2] and len(action[2]) > 0 else {}
                room_obj = action[3] or {}
                
                # Use get() with fallbacks for all dictionary accesses
                schedule.append({
                    "activity": activity.get("code", ""),
                    "day": {
                        "name": day_obj.get("name", ""),
                        "code": day_obj.get("code", ""),
                        "order": day_obj.get("order", 0),
                        "long_name": day_obj.get("long_name", "")
                    },
                    "period": [{
                        "name": period_obj.get("name", ""),
                        "start_time": period_obj.get("start_time", ""),
                        "end_time": period_obj.get("end_time", ""),
                        "order": period_obj.get("order", 0),
                        "long_name": period_obj.get("long_name", ""),
                        "is_interval": period_obj.get("is_interval", False)
                    }] if period_obj else [],
                    "room": {
                        "name": room_obj.get("name", ""),
                        "code": room_obj.get("code", ""),
                        "capacity": room_obj.get("capacity", 0),
                        "type": room_obj.get("type", "classroom")
                    },
                    "teacher": action[4] if len(action) > 4 else "",
                    "subgroup": action[5] if len(action) > 5 else "",
                    "subject": action[6] if len(action) > 6 else "",
                    "duration": activity.get("duration", 1),
                    "algorithm": "RL"  # Add algorithm to be consistent
                })

        return schedule

    def _decode_action(self, action_index, activity=None):
        if activity is None:
            activity = random.choice(self.env.activities)
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
    """
    Generate a timetable using the Reinforcement Learning approach.
    If the model file doesn't exist, it will create and train a simple model on the fly.
    """
    try:
        logging.info("Initializing RL environment...")
        env = SchedulingEnvironment()
        
        model_path = "scheduler_model.pkl"
        logging.info(f"Loading RL model from {model_path}...")
        scheduler = QLearningScheduler(env, model_path)

        logging.info("Generating schedule using the RL model...")
        schedule = scheduler.create_schedule()
        logging.info(f"Schedule generated successfully with {len(schedule)} activities!")
        
        return schedule
    except Exception as e:
        logging.error(f"Error in RL generation: {str(e)}")
        # Return empty schedule on error
        return []
