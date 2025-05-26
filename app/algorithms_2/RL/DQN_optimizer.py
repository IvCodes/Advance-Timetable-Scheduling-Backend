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

def get_activity_size(activity, groups_dict):
    """Calculate total students for an activity"""
    total_students = 0
    for group_id in activity.group_ids:
        if group_id in groups_dict:
            total_students += groups_dict[group_id].size
    return total_students

def can_place_activity(activity, start_slot, schedule, groups_dict, spaces_dict):
    """Check if an activity can be placed starting at a specific slot"""
    try:
        slot_index = slots.index(start_slot)
        duration = activity.duration
        
        # Check if we have enough consecutive slots
        if slot_index + duration > len(slots):
            return False
        
        # Get required slots
        required_slots = slots[slot_index:slot_index + duration]
        
        # Check for conflicts in each required slot
        for slot in required_slots:
            # Check lecturer conflicts
            for room_id, existing_activity in schedule[slot].items():
                if existing_activity and existing_activity.teacher_id == activity.teacher_id:
                    return False
            
            # Check group conflicts
            for room_id, existing_activity in schedule[slot].items():
                if existing_activity:
                    for group_id in activity.group_ids:
                        if group_id in existing_activity.group_ids:
                            return False
        
        return True
    except Exception as e:
        print(f"Error in can_place_activity: {e}")
        return False

def find_suitable_room(activity, start_slot, schedule, groups_dict, spaces_dict):
    """Find a suitable room for an activity starting at a specific slot"""
    try:
        activity_size = get_activity_size(activity, groups_dict)
        slot_index = slots.index(start_slot)
        duration = activity.duration
        required_slots = slots[slot_index:slot_index + duration]
        
        # Sort rooms by capacity (largest first) to prefer bigger rooms for bigger activities
        sorted_rooms = sorted(spaces_dict.items(), key=lambda x: x[1].size, reverse=True)
        
        # Check each room
        for room_id, room in sorted_rooms:
            # Check room capacity with some flexibility (allow 90% capacity utilization)
            if room.size < activity_size * 0.9:
                continue
            
            # Check if room is available for all required slots
            room_available = True
            for slot in required_slots:
                if schedule[slot][room_id] is not None:
                    room_available = False
                    break
            
            if room_available:
                return room_id
        
        # If no room found with strict capacity, try with relaxed capacity (allow overcrowding)
        for room_id, room in sorted_rooms:
            # Allow up to 120% capacity utilization as fallback
            if room.size < activity_size * 0.8:
                continue
                
            # Check if room is available for all required slots
            room_available = True
            for slot in required_slots:
                if schedule[slot][room_id] is not None:
                    room_available = False
                    break
            
            if room_available:
                print(f"Warning: Placing activity {activity.id} in room {room_id} with overcrowding")
                return room_id
        
        return None
    except Exception as e:
        print(f"Error in find_suitable_room: {e}")
        return None

def place_activity(activity, start_slot, room_id, schedule):
    """Place an activity in the schedule for its full duration"""
    try:
        slot_index = slots.index(start_slot)
        duration = activity.duration
        required_slots = slots[slot_index:slot_index + duration]
        
        for slot in required_slots:
            schedule[slot][room_id] = activity
    except Exception as e:
        print(f"Error in place_activity: {e}")

def reward(schedule, groups_dict, spaces_dict):
    """
    Enhanced reward function to evaluate schedule quality
    
    Args:
        schedule: The current timetable schedule
        groups_dict: Dictionary of student groups
        spaces_dict: Dictionary of spaces/rooms
        
    Returns:
        int: Reward score for the schedule
    """
    score = 0
    
    # Count assigned activities
    assigned_activities = set()
    total_activity_slots = 0
    
    for slot, space_dict in schedule.items():
        for space, activity in space_dict.items():
            if activity:
                assigned_activities.add(activity.id)
                total_activity_slots += 1
                score += 20  # Higher reward for valid placement
    
    # Major bonus for assigning more unique activities
    unique_activities_bonus = len(assigned_activities) * 50
    score += unique_activities_bonus
    
    # Bonus for efficient room utilization
    if total_activity_slots > 0:
        score += total_activity_slots * 5
    
    # Check for conflicts and penalize
    conflict_penalty = 0
    for slot, space_dict in schedule.items():
        teacher_assignments = set()
        group_assignments = set()
        
        for space, activity in space_dict.items():
            if activity:
                # Teacher conflict penalty
                if activity.teacher_id in teacher_assignments:
                    conflict_penalty += 100
                teacher_assignments.add(activity.teacher_id)
                
                # Group conflict penalty
                for group_id in activity.group_ids:
                    if group_id in group_assignments:
                        conflict_penalty += 80
                    group_assignments.add(group_id)
                
                # Room capacity penalty (less severe)
                activity_size = get_activity_size(activity, groups_dict)
                if space in spaces_dict and activity_size > spaces_dict[space].size:
                    conflict_penalty += 20  # Reduced penalty for overcrowding

    score -= conflict_penalty
    
    # Ensure minimum positive score for any assignment
    if len(assigned_activities) > 0:
        score = max(score, len(assigned_activities) * 10)
    
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
                state.append(activity_id_map.get(activity.id, 0))
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
    
    print(f"🚀 Starting DQN optimization with {len(activities_dict)} activities")
    
    # Sort activities by duration and size for better scheduling
    activity_list = sorted(activities_dict.values(), 
                          key=lambda x: (x.duration, get_activity_size(x, groups_dict)), 
                          reverse=True)
    
    print(f"📋 Activity list prepared: {len(activity_list)} activities")
    
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
    action_size = len(slots)  # Actions are starting time slots
    dqn = DQN(state_size, action_size)
    optimizer = optim.Adam(dqn.parameters(), lr=learning_rate, weight_decay=1e-5)
    loss_fn = nn.MSELoss()
    
    # Best schedule tracking
    best_schedule = None
    best_reward = float('-inf')
    
    # Training loop
    for episode in range(episodes):
        # Reset schedule for each episode
        schedule = {slot: {space: None for space in spaces} for slot in slots}
        unassigned_activities = copy.deepcopy(activity_list)
        
        state = schedule_to_state(schedule, activity_id_map, slots, spaces)
        
        activities_placed_this_episode = 0
        
        # Try to place each activity
        while unassigned_activities:
            activity = unassigned_activities[0]
            
            # Get valid starting slots for this activity
            valid_slots = []
            for slot in slots:
                if can_place_activity(activity, slot, schedule, groups_dict, spaces_dict):
                    room_id = find_suitable_room(activity, slot, schedule, groups_dict, spaces_dict)
                    if room_id:
                        valid_slots.append(slot)
            
            if not valid_slots:
                # Can't place this activity, remove it and continue
                unassigned_activities.pop(0)
                continue
            
            # Choose action using epsilon-greedy
            if random.random() < epsilon or len(valid_slots) == 1:
                # Exploration or only one choice
                chosen_slot = random.choice(valid_slots)
            else:
                # Exploitation using DQN
                with torch.no_grad():
                    q_values = dqn(torch.tensor(state, dtype=torch.float32))
                    
                    # Get Q-values for valid slots only
                    valid_slot_indices = [slots.index(slot) for slot in valid_slots]
                    valid_q_values = [(idx, q_values[idx].item()) for idx in valid_slot_indices]
                    
                    # Choose slot with highest Q-value
                    best_slot_idx = max(valid_q_values, key=lambda x: x[1])[0]
                    chosen_slot = slots[best_slot_idx]
            
            # Find room and place activity
            room_id = find_suitable_room(activity, chosen_slot, schedule, groups_dict, spaces_dict)
            if room_id:
                place_activity(activity, chosen_slot, room_id, schedule)
                unassigned_activities.pop(0)
                activities_placed_this_episode += 1
                
                # Update state and store experience
                new_state = schedule_to_state(schedule, activity_id_map, slots, spaces)
                reward_value = reward(schedule, groups_dict, spaces_dict)
                
                action_idx = slots.index(chosen_slot)
                replay_buffer.append((state, action_idx, reward_value, new_state))
                state = new_state
            else:
                # Couldn't place activity, remove it
                unassigned_activities.pop(0)
        
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
        hard_violations, soft_score = evaluate_timetable(
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
        population = [schedule]
        fitness_values = [(total_hard_violations, soft_score)]
        
        metrics_tracker.add_generation_metrics(
            population=population,
            fitness_values=fitness_values,
            generation=episode
        )
        
        # Update best schedule if better
        if current_reward > best_reward:
            best_reward = current_reward
            best_schedule = copy.deepcopy(schedule)
            print(f"🎯 New best schedule found at episode {episode}: {activities_placed_this_episode} activities, reward: {current_reward}")
        
        # Print progress every 10 episodes
        if episode % 10 == 0:
            assigned_count = len(set(activity.id for slot_dict in schedule.values() 
                                   for activity in slot_dict.values() if activity))
            print(f"Episode {episode}: Assigned {assigned_count}/{len(activities_dict)} activities, Reward: {current_reward}")
    
    # Final evaluation of best solution
    if best_schedule:
        print("✅ Optimization completed. Evaluating best solution...")
        
        # Count final assignments
        final_assigned = len(set(activity.id for slot_dict in best_schedule.values() 
                               for activity in slot_dict.values() if activity))
        print(f"📊 Final result: {final_assigned}/{len(activities_dict)} activities assigned")
        
        hard_violations_tuple, final_soft_score = evaluate_timetable(
            best_schedule,
            activities_dict,
            groups_dict,
            spaces_dict,
            lecturers_dict,
            slots,
            verbose=True
        )
        
        # Sum up the relevant hard violations
        _, prof_conflicts, sub_group_conflicts, room_size_conflicts, time_constraint_violations, unasigned_activities = hard_violations_tuple
        final_hard_violations = prof_conflicts + sub_group_conflicts + room_size_conflicts + time_constraint_violations + unasigned_activities
        
        # Set final metrics
        metrics_tracker.set_final_metrics(
            hard_violations=final_hard_violations,
            soft_score=final_soft_score,
            execution_time=time.time() - start_time
        )
        
        return best_schedule, metrics_tracker.get_metrics()
    
    # Return empty schedule if no solution found
    print("❌ No valid schedule found")
    empty_schedule = {slot: {space: None for space in spaces_dict} for slot in slots}
    return empty_schedule, metrics_tracker.get_metrics()

if __name__ == "__main__":
    best_schedule, metrics = run_dqn_optimizer(activities_dict, groups_dict, spaces_dict, lecturers_dict, slots, learning_rate=0.001, episodes=100, epsilon=0.1)
    print(f"Final solution metrics: {metrics}")
