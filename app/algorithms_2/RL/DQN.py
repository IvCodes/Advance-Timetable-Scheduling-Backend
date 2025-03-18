import random
import copy
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque

# Define the neural network for Deep Q-Learning
class DQN(nn.Module):
    def _init_(self, input_size, output_size):
        super(DQN, self)._init_()
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, output_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)

# Make a copy of the activities dictionary
activities_copy = copy.deepcopy(activities_dict)

# Assign activities strategically
activity_list = sorted(activities_copy.values(), key=lambda x: x.duration, reverse=True)


# Convert activity IDs to numeric values
activity_id_map = {activity.id: idx + 1 for idx, activity in enumerate(activity_list)}

# Define replay buffer
replay_buffer = deque(maxlen=10000)

# Reward function to evaluate schedule quality
def reward(schedule):
    score = 0
    teacher_assignments = {}
    group_assignments = {}

    for slot, space_dict in schedule.items():
        for space, activity in space_dict.items():
            if activity:
                score += 10  # Reward for valid placement

                # Teacher conflict penalty
                teacher = activity.teacher_id
                if teacher in teacher_assignments and teacher_assignments[teacher] == slot:
                    score -= 20
                else:
                    teacher_assignments[teacher] = slot

                # Group conflict penalty
                for group in activity.group_ids:
                    if group in group_assignments and group_assignments[group] == slot:
                        score -= 15
                    else:
                        group_assignments[group] = slot

                # Overlapping groups in same slot penalty
                assigned_groups = set()
                for other_space, other_activity in space_dict.items():
                    if other_activity and other_activity != activity:
                        for group in other_activity.group_ids:
                            if group in assigned_groups:
                                score -= 25
                            assigned_groups.add(group)

                # Room capacity penalty
                total_students = sum(groups_dict[group].size for group in activity.group_ids)
                if total_students > spaces_dict[space].size:
                    score -= 30

    return score

# Convert schedule to state representation
def schedule_to_state(schedule):
    state = []
    for slot in slots:
        for space in spaces:
            activity = schedule[slot][space]
            if activity:
                state.append(activity_id_map.get(activity.id, 0))  # Map activity ID to numeric value
            else:
                state.append(0)
    return np.array(state, dtype=np.float32)

# Training parameters
epsilon = 1.0
epsilon_decay = 0.995
epsilon_min = 0.01
gamma = 0.9
learning_rate = 0.00001
batch_size = 16
epochs = 25

# Initialize DQN
state_size = len(slots) * len(spaces)
action_size = len(slots) * len(spaces)
dqn = DQN(state_size, action_size)
optimizer = optim.Adam(dqn.parameters(), lr=learning_rate)
loss_fn = nn.MSELoss()

# Training loop
for epoch in range(epochs):
    # Reset schedule and activity list each epoch
    schedule = {slot: {space: None for space in spaces} for slot in slots}
    activity_list_copy = copy.deepcopy(activity_list)

    state = schedule_to_state(schedule)
    total_reward = 0

    for _ in range(len(activity_list_copy)):
        if random.random() < epsilon:
            action = random.randint(0, action_size - 1)  # Exploration
        else:
            with torch.no_grad():
                q_values = dqn(torch.tensor(state, dtype=torch.float32))
                action = torch.argmax(q_values).item()  # Exploitation

        slot_idx = action // len(spaces)
        space_idx = action % len(spaces)
        slot = slots[slot_idx]
        space = spaces[space_idx]

        if schedule[slot][space] is None and activity_list_copy:
            activity = activity_list_copy.pop()
            schedule[slot][space] = activity

            new_state = schedule_to_state(schedule)
            reward_value = reward(schedule)
            total_reward += reward_value

            replay_buffer.append((state, action, reward_value, new_state))
            state = new_state

    # Training step
    if len(replay_buffer) > batch_size:
        minibatch = random.sample(replay_buffer, batch_size)
        for state, action, reward_value, new_state in minibatch:
            q_values = dqn(torch.tensor(state, dtype=torch.float32))
            next_q_values = dqn(torch.tensor(new_state, dtype=torch.float32))

            target_q = q_values.clone()
            target_q[action] = reward_value + gamma * next_q_values.max().item()

            optimizer.zero_grad()
            loss = loss_fn(q_values, target_q)
            loss.backward()
            optimizer.step()

    # Decay epsilon
    epsilon = max(epsilon * epsilon_decay, epsilon_min)
    #print(f"Epoch {epoch + 1}, Reward: {total_reward}, Epsilon: {epsilon}")

# Print final schedule
from pprint import pprint
pprint(schedule)
#print("Final Schedule Reward Score:", reward(schedule))