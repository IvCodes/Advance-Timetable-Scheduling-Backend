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


conflicts = ctrl.Antecedent(np.arange(0, 11, 1), 'conflicts')
room_utilization = ctrl.Antecedent(np.arange(0, 101, 1), 'room_utilization')
overlap = ctrl.Antecedent(np.arange(0, 11, 1), 'overlap')

score = ctrl.Consequent(np.arange(0, 101, 1), 'score')

conflicts['low'] = fuzz.trimf(conflicts.universe, [0, 0, 5])
conflicts['medium'] = fuzz.trimf(conflicts.universe, [0, 5, 10])
conflicts['high'] = fuzz.trimf(conflicts.universe, [5, 10, 10])

room_utilization['low'] = fuzz.trimf(room_utilization.universe, [0, 0, 50])
room_utilization['medium'] = fuzz.trimf(room_utilization.universe, [30, 50, 70])
room_utilization['high'] = fuzz.trimf(room_utilization.universe, [50, 100, 100])

overlap['low'] = fuzz.trimf(overlap.universe, [0, 0, 5])
overlap['medium'] = fuzz.trimf(overlap.universe, [0, 5, 10])
overlap['high'] = fuzz.trimf(overlap.universe, [5, 10, 10])

score['low'] = fuzz.trimf(score.universe, [0, 0, 50])
score['medium'] = fuzz.trimf(score.universe, [30, 50, 70])
score['high'] = fuzz.trimf(score.universe, [50, 100, 100])

rules = [
    ctrl.Rule(conflicts['low'] & room_utilization['low'] & overlap['low'], score['high']),
    ctrl.Rule(conflicts['medium'] & room_utilization['medium'] & overlap['medium'], score['medium']),
    ctrl.Rule(conflicts['high'] | room_utilization['high'] | overlap['high'], score['low']),
    ctrl.Rule(conflicts['medium'] & room_utilization['low'] & overlap['low'], score['medium']),
    ctrl.Rule(conflicts['low'] & room_utilization['medium'] & overlap['medium'], score['medium']),
]

scoring_ctrl = ctrl.ControlSystem(rules)
scoring = ctrl.ControlSystemSimulation(scoring_ctrl)

def evaluate_timetable(conflict_count, utilization, overlap_count):
    scoring.input['conflicts'] = conflict_count
    scoring.input['room_utilization'] = utilization
    scoring.input['overlap'] = overlap_count
    scoring.compute()
    return scoring.output['score']

def evaluate():
    timetables = get_timetables()
    results_by_algorithm = defaultdict(list)

    algorithm_scores = defaultdict(list) 
    wins = defaultdict(int)

    timetables_by_semester = defaultdict(list)
    for timetable in timetables:
        timetables_by_semester[timetable["semester"]].append(timetable)

    for semester, schedules in timetables_by_semester.items():
        best_score = -1
        best_algorithm = None

        print(f"Results for Semester: {semester}")
        for timetable in schedules:
            conflict_count = calculate_conflicts(timetable)
            utilization = calculate_room_utilization(timetable)
            overlap_count = calculate_period_overlap(timetable)
            score = evaluate_timetable(conflict_count, utilization, overlap_count)

            algorithm = timetable["algorithm"]
            algorithm_scores[algorithm].append(score)

            print(f"  Algorithm: {algorithm}, Code: {timetable['code']}, Score: {score:.2f}")

            if score > best_score:
                best_score = score
                best_algorithm = algorithm

        if best_algorithm:
            wins[best_algorithm] += 1
            print(f"  Best Algorithm for {semester}: {best_algorithm} (Score: {best_score:.2f})\n")

    print("\nOverall Algorithm Performance:")
    for algorithm, scores in algorithm_scores.items():
        average_score = sum(scores) / len(scores)
        print(f"  Algorithm: {algorithm}")
        print(f"    Average Score: {average_score:.2f}")
        print(f"    Wins: {wins[algorithm]}")

    return algorithm_scores
