import random
import copy
import numpy as np

# Create the schedule dictionary
schedule = {slot: {space: None for space in spaces} for slot in slots}

# Convert activity objects to immutable keys (e.g., tuples)
activity_list = [(activity.id, activity.subject, activity.teacher_id, tuple(activity.group_ids), activity.duration) for activity in activities_dict.values()]

# Randomly assign activities to slots initially
random.shuffle(activity_list)
for activity in activity_list:
    assigned = False
    for slot in slots:
        for space in spaces:
            if schedule[slot][space] is None:
                schedule[slot][space] = activity
                assigned = True
                break
        if assigned:
            break

# SARSA parameters
epsilon = 1.0
epsilon_decay = 0.98
epsilon_min = 0.01
gamma = 0.9
alpha = 0.1
epochs = 50

# Initialize Q-table
Q_table = {key: np.zeros(len(activity_list)) for key in [(slot, space) for slot in slots for space in spaces]}

# Function to calculate reward
def reward(schedule):
    score = 0
    teacher_assignments = {}
    group_assignments = {}

    for slot in slots:
        for space, activity in schedule[slot].items():
            if activity:
                activity_id, subject, teacher, group_ids, duration = activity
                score += 10  # Reward for valid placement

                if teacher in teacher_assignments and teacher_assignments[teacher] == slot:
                    score -= 20  # Penalize teacher conflict
                else:
                    teacher_assignments[teacher] = slot

                for group in group_ids:
                    if group in group_assignments and group_assignments[group] == slot:
                        score -= 15  # Penalize group conflict
                    else:
                        group_assignments[group] = slot

                total_students = sum(groups_dict[group].size for group in group_ids)
                if total_students > spaces_dict[space].size:
                    score -= 30  # Penalize overcapacity

    return score

# SARSA Training loop
for epoch in range(epochs):
    state = copy.deepcopy(schedule)
    total_reward = 0

    for slot in slots:
        for space in spaces:
            if schedule[slot][space] is None:
                continue

            activity_index = activity_list.index(schedule[slot][space])

            if random.random() < epsilon:
                next_slot, next_space = random.choice(list(Q_table.keys()))
                next_activity_index = random.choice(range(len(activity_list)))
            else:
                next_slot, next_space = max(Q_table.keys(), key=lambda k: np.max(Q_table[k]))
                next_activity_index = np.argmax(Q_table[(next_slot, next_space)])

            reward_value = reward(state)
            total_reward += reward_value

            next_action_value = Q_table[(next_slot, next_space)][next_activity_index]
            Q_table[(slot, space)][activity_index] += alpha * (
                reward_value + gamma * next_action_value - Q_table[(slot, space)][activity_index]
            )

    epsilon = max(epsilon * epsilon_decay, epsilon_min)
    print(f"Epoch {epoch + 1}, Reward: {total_reward}, Epsilon: {epsilon}")

# Remove activities causing conflicts
def resolve_conflicts(schedule):
    for slot in slots:
        teacher_assignments = {}
        group_assignments = {}
        for space in spaces:
            activity = schedule[slot][space]
            if activity:
                activity_id, subject, teacher, group_ids, duration = activity
                if teacher in teacher_assignments or any(group in group_assignments for group in group_ids):
                    schedule[slot][space] = None  # Remove conflicting activity
                else:
                    teacher_assignments[teacher] = slot
                    for group in group_ids:
                        group_assignments[group] = slot

resolve_conflicts(schedule)

# Print final schedule
from pprint import pprint
pprint(schedule)