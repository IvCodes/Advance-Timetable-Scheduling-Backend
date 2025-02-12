import numpy as np
import random
import pickle
from data_collector import *
from deap import base, creator, tools, algorithms
import random
from collections import defaultdict
from typing import List, Dict

days = []
facilities = []
modules = []
periods = []
students = []
teachers = []
years = []
activities = []

def get_data():
    global days, facilities, modules, periods, students, teachers, years, activities
    days =  get_days()
    facilities =  get_spaces()
    modules =  get_modules()
    periods =  get_periods()
    students =  get_students()
    teachers =  get_teachers()
    years =  get_years()
    activities =  get_activities()

def print_first():
    print(days[0])
    print(facilities[0])
    print(modules[0])
    print(periods[0])
    print(students[0])
    print(teachers[0])
    print(years[0])
    print(activities[0])

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
        activity, day, periods, room, teacher, subgroup, duration, subject = action
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
            "subgroup": subgroup,
            "duration": duration,
            "subject": subject
        })
        self.state["conflicts"] = conflicts
        done = len(self.state["schedule"]) == len(self.activities)
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
    def __init__(self, env):
        self.env = env
        self.q_table = defaultdict(lambda: np.zeros(len(self.env.periods)))
        self.alpha = 0.1 
        self.gamma = 0.99 
        self.epsilon = 0.1 

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
            print(f"Episode {episode + 1}: Total Reward: {total_reward}")

    def save_model(self, filepath):
        with open(filepath, "wb") as f:
            pickle.dump(dict(self.q_table), f)

    def load_model(self, filepath):
        with open(filepath, "rb") as f:
            self.q_table = defaultdict(lambda: np.zeros(len(self.env.periods)), pickle.load(f))

    def _decode_action(self, action_index):
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
        duration = activity["duration"]
        subject = activity["subject"]
        return activity, day, periods, room, teacher, subgroup, duration, subject


if __name__ == "__main__":
    env = SchedulingEnvironment()
    scheduler = QLearningScheduler(env)

    print("Training the Q-learning scheduler...")
    scheduler.train(episodes=500)
    scheduler.save_model("scheduler_model.pkl")
    print("Model saved successfully!")