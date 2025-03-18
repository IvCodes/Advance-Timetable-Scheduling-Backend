import random
import copy
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import time
import os

from app.algorithms_2.Data_Loading import Activity, spaces_dict, groups_dict, activities_dict, slots, lecturers_dict
from app.algorithms_2.evaluate import evaluate_hard_constraints, evaluate_soft_constraints, evaluate_timetable
from app.algorithms_2.metrics_tracker import MetricsTracker
from app.algorithms_2.timetable_html_generator import generate_timetable_html

# Define the neural network for Deep Q-Learning
class DQN(nn.Module):
    def __init__(self, input_size, output_size):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, output_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)

def reward(schedule, groups_dict, spaces_dict):
    """
    Reward function to evaluate schedule quality
    
    Args:
        schedule: The current timetable schedule
        groups_dict: Dictionary of student groups
        spaces_dict: Dictionary of spaces/rooms
        
    Returns:
        int: Reward score for the schedule
    """
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
                total_students = sum(groups_dict[group].size for group in activity.group_ids if group in groups_dict)
                if space in spaces_dict and total_students > spaces_dict[space].size:
                    score -= 30

    return score

def schedule_to_state(schedule, activity_id_map, slots, spaces):
    """
    Convert schedule to state representation
    
    Args:
        schedule: The current timetable schedule
        activity_id_map: Mapping of activity IDs to numeric values
        slots: Available time slots
        spaces: Available spaces/rooms
        
    Returns:
        numpy.ndarray: State representation of the schedule
    """
    state = []
    for slot in slots:
        for space in spaces:
            activity = schedule[slot][space]
            if activity:
                state.append(activity_id_map.get(activity.id, 0))  # Map activity ID to numeric value
            else:
                state.append(0)
    return np.array(state, dtype=np.float32)

def run_dqn_optimizer(activities_dict, groups_dict, spaces_dict, lecturers_dict, slots, learning_rate=0.001, episodes=100, epsilon=0.1):
    """
    Run the Deep Q-Network optimizer to generate a timetable.
    
    Args:
        activities_dict: Dictionary of activities.
        groups_dict: Dictionary of groups.
        spaces_dict: Dictionary of spaces.
        lecturers_dict: Dictionary of lecturers.
        slots: List of time slots.
        learning_rate: Learning rate for the DQN algorithm.
        episodes: Number of episodes to run.
        epsilon: Initial epsilon for epsilon-greedy exploration.
        
    Returns:
        best_schedule: The best schedule found.
        metrics: Dictionary of metrics tracking the optimization process.
    """
    
    start_time = time.time()
    metrics_tracker = MetricsTracker()
    
    # Make a copy of the activities dictionary
    activities_copy = copy.deepcopy(activities_dict)
    
    # Sort activities by duration for prioritization
    activity_list = sorted(activities_copy.values(), key=lambda x: x.duration, reverse=True)
    
    # Create activity ID mapping for state representation
    activity_id_map = {activity.id: idx + 1 for idx, activity in enumerate(activity_list)}
    
    # Initialize spaces list
    spaces = list(spaces_dict.keys())
    
    # DQN parameters
    gamma = 0.9
    batch_size = 16
    
    # Initialize replay buffer
    replay_buffer = deque(maxlen=10000)
    
    # Initialize DQN
    state_size = len(slots) * len(spaces)
    action_size = len(slots) * len(spaces)
    dqn = DQN(state_size, action_size)
    optimizer = optim.Adam(dqn.parameters(), lr=learning_rate, weight_decay=1e-5)
    loss_fn = nn.MSELoss()
    
    # Best schedule tracking
    best_schedule = None
    best_reward = float('-inf')
    
    # Training loop
    for episode in range(episodes):
        # Reset schedule and activity list each episode
        schedule = {slot: {space: None for space in spaces} for slot in slots}
        activity_list_copy = copy.deepcopy(activity_list)
        
        state = schedule_to_state(schedule, activity_id_map, slots, spaces)
        
        # Place activities using DQN
        for _ in range(len(activity_list_copy)):
            if random.random() < epsilon:
                action = random.randint(0, action_size - 1)  # Exploration
            else:
                with torch.no_grad():
                    q_values = dqn(torch.tensor(state, dtype=torch.float32))
                    action = torch.argmax(q_values).item()  # Exploitation
            
            slot_idx = action // len(spaces)
            space_idx = action % len(spaces)
            
            if slot_idx < len(slots) and space_idx < len(spaces):
                slot = slots[slot_idx]
                space = spaces[space_idx]
                
                if schedule[slot][space] is None and activity_list_copy:
                    activity = activity_list_copy.pop()
                    schedule[slot][space] = activity
                    
                    new_state = schedule_to_state(schedule, activity_id_map, slots, spaces)
                    reward_value = reward(schedule, groups_dict, spaces_dict)
                    
                    replay_buffer.append((state, action, reward_value, new_state))
                    state = new_state
        
        # Training step
        if len(replay_buffer) > batch_size:
            minibatch = random.sample(replay_buffer, batch_size)
            for s, a, r, ns in minibatch:
                q_values = dqn(torch.tensor(s, dtype=torch.float32))
                next_q_values = dqn(torch.tensor(ns, dtype=torch.float32))
                
                target_q = q_values.clone()
                target_q[a] = r + gamma * next_q_values.max().item()
                
                optimizer.zero_grad()
                loss = loss_fn(q_values, target_q)
                loss.backward()
                optimizer.step()
        
        # Decay epsilon
        epsilon = max(epsilon * 0.995, 0.01)
        
        # Evaluate the current solution
        current_reward = reward(schedule, groups_dict, spaces_dict)

        # Evaluate the current schedule
        hard_violations, _ = evaluate_timetable(
            schedule,
            activities_dict,
            groups_dict,
            spaces_dict,
            lecturers_dict,
            slots,
            verbose=False
        )
        
        # Calculate total hard violations
        total_hard_violations = sum(hard_violations)
        
        # Create a single-solution population and fitness values list for metrics tracking
        # The MetricsTracker expects lists of populations and fitness values
        population = [schedule]
        fitness_values = [(total_hard_violations, 0)]
        
        metrics_tracker.add_generation_metrics(
            population=population,
            fitness_values=fitness_values,
            generation=episode
        )
        
        # Update best schedule if better
        if current_reward > best_reward:
            best_reward = current_reward
            best_schedule = copy.deepcopy(schedule)
        
        # Print progress
        # print(f"Episode {episode + 1}/{episodes}, Reward: {current_reward}, Time: {time.time() - start_time:.2f}s")
    
    # Final evaluation of best solution
    if best_schedule:
        print("Optimization completed. Evaluating best solution...")
        
        hard_violations_tuple, final_soft_score = evaluate_timetable(
            best_schedule,
            activities_dict,
            groups_dict,
            spaces_dict,
            lecturers_dict,
            slots,
            verbose=True
        )
        
        # Sum up the relevant hard violations (excluding vacant rooms as they're not actual violations)
        # The tuple has (vacant_room_count, prof_conflicts, sub_group_conflicts, room_size_conflicts, unasigned_activities)
        _, prof_conflicts, sub_group_conflicts, room_size_conflicts, unasigned_activities = hard_violations_tuple
        final_hard_violations = prof_conflicts + sub_group_conflicts + room_size_conflicts + unasigned_activities
        
        # Set final metrics
        metrics_tracker.set_final_metrics(
            hard_violations=final_hard_violations,
            soft_score=final_soft_score,
            execution_time=time.time() - start_time
        )
        
        # Return the best schedule and metrics
        return best_schedule, metrics_tracker.get_metrics()

if __name__ == "__main__":
    best_schedule, metrics = run_dqn_optimizer(activities_dict, groups_dict, spaces_dict, lecturers_dict, slots, learning_rate=0.001, episodes=100, epsilon=0.1)
    print(f"Final solution hard violations: {metrics.hard_violations}")
    print(f"Final solution soft score: {metrics.soft_score}")
    print(f"Execution time: {metrics.execution_time:.2f} seconds")
