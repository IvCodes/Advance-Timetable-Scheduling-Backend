from generator.data_collector import *
import random
import numpy as np
from skfuzzy import control as ctrl
import skfuzzy as fuzz
from collections import defaultdict


def calculate_conflicts(timetable):
    teacher_schedule = {}
    room_schedule = {}
    conflicts = 0

    for entry in timetable["timetable"]:
        day = entry["day"]["name"]
        teacher = entry["teacher"]
        room = entry["room"]["_id"]
        periods = [period["name"] for period in entry["period"]]

        if teacher not in teacher_schedule:
            teacher_schedule[teacher] = {}
        if day not in teacher_schedule[teacher]:
            teacher_schedule[teacher][day] = []
        if any(period in teacher_schedule[teacher][day] for period in periods):
            conflicts += 1
        teacher_schedule[teacher][day].extend(periods)

        if room not in room_schedule:
            room_schedule[room] = {}
        if day not in room_schedule[room]:
            room_schedule[room][day] = []
        if any(period in room_schedule[room][day] for period in periods):
            conflicts += 1
        room_schedule[room][day].extend(periods)

    return conflicts

def calculate_room_utilization(timetable):
    total_utilization = 0
    total_entries = len(timetable["timetable"])

    for entry in timetable["timetable"]:
        room_capacity = entry["room"]["capacity"]
        students = 100
        utilization = (students / room_capacity) * 100
        total_utilization += utilization

    return total_utilization / total_entries if total_entries > 0 else 0

def calculate_period_overlap(timetable):
    subgroup_schedule = {}
    overlaps = 0

    for entry in timetable["timetable"]:
        day = entry["day"]["name"]
        subgroup = entry["subgroup"]
        periods = [period["name"] for period in entry["period"]]

        if subgroup not in subgroup_schedule:
            subgroup_schedule[subgroup] = {}
        if day not in subgroup_schedule[subgroup]:
            subgroup_schedule[subgroup][day] = []
        if any(period in subgroup_schedule[subgroup][day] for period in periods):
            overlaps += 1
        subgroup_schedule[subgroup][day].extend(periods)

    return overlaps