import random
import copy
import numpy as np
import time
import os

from app.algorithms_2.Data_Loading import Activity, spaces_dict, groups_dict, activities_dict, slots, lecturers_dict
from app.algorithms_2.evaluate import evaluate_hard_constraints, evaluate_soft_constraints, evaluate_timetable
from app.algorithms_2.metrics_tracker import MetricsTracker
from app.algorithms_2.timetable_html_generator import generate_timetable_html

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

def resolve_conflicts(schedule):
    """
    Attempt to resolve conflicts in the schedule
    
    Args:
        schedule: The current timetable schedule
        
    Returns:
        dict: Updated schedule with attempted conflict resolution
    """
    try:
        # Find all activities
        all_activities = []
        for slot, spaces in schedule.items():
            for space, activity in spaces.items():
                if activity:
                    all_activities.append((slot, space, activity))
        
        # Random shuffle to avoid bias
        random.shuffle(all_activities)
        
        # Remove all activities from schedule
        for slot, space, _ in all_activities:
            schedule[slot][space] = None
        
        # Reassign activities with priority
        for _, _, activity in all_activities:
            best_slot = None
            best_room = None
            best_score = float('-inf')
            
            # Try each starting slot
            for slot in slots:
                if can_place_activity(activity, slot, schedule, groups_dict, spaces_dict):
                    room_id = find_suitable_room(activity, slot, schedule, groups_dict, spaces_dict)
                    if room_id:
                        # Temporarily assign activity
                        place_activity(activity, slot, room_id, schedule)
                        curr_score = reward(schedule, groups_dict, spaces_dict)
                        
                        # If better score, remember this placement
                        if curr_score > best_score:
                            best_score = curr_score
                            best_slot = slot
                            best_room = room_id
                        
                        # Remove temporary assignment
                        slot_index = slots.index(slot)
                        duration = activity.duration
                        required_slots = slots[slot_index:slot_index + duration]
                        for temp_slot in required_slots:
                            schedule[temp_slot][room_id] = None
            
            # Assign activity to best position found
            if best_slot and best_room:
                place_activity(activity, best_slot, best_room, schedule)
        
        return schedule
    except Exception as e:
        print(f"Error in resolve_conflicts: {e}")
        return schedule

def run_sarsa_optimizer(activities_dict, groups_dict, spaces_dict, lecturers_dict, slots, learning_rate=0.001, episodes=100, epsilon=0.1):
    """
    Run the SARSA optimization algorithm for timetable scheduling
    
    Args:
        activities_dict: Dictionary of activities.
        groups_dict: Dictionary of groups.
        spaces_dict: Dictionary of spaces.
        lecturers_dict: Dictionary of lecturers.
        slots: List of time slots.
        learning_rate: Learning rate for the algorithm.
        episodes: Number of episodes to run.
        epsilon: Initial epsilon for epsilon-greedy exploration.
        
    Returns:
        best_schedule: The best schedule found.
        metrics: Dictionary of metrics tracking the optimization process.
    """
    start_time = time.time()
    metrics_tracker = MetricsTracker()
    
    print(f"🚀 Starting SARSA optimization with {len(activities_dict)} activities")
    
    # Sort activities by duration and size for better scheduling
    activity_list = sorted(activities_dict.values(), 
                          key=lambda x: (x.duration, get_activity_size(x, groups_dict)), 
                          reverse=True)
    
    print(f"📋 Activity list prepared: {len(activity_list)} activities")
    
    # SARSA parameters
    gamma = 0.9
    alpha = learning_rate
    
    # Initialize Q-table: (activity_id, slot) -> Q-value
    Q_table = {}
    for activity in activity_list:
        for slot in slots:
            Q_table[(activity.id, slot)] = 0.0
    
    # Best schedule tracking
    best_schedule = None
    best_reward_value = float('-inf')
    
    # SARSA Training loop
    for epoch in range(episodes):
        # Initialize schedule
        current_schedule = {slot: {space: None for space in spaces_dict} for slot in slots}
        unassigned_activities = copy.deepcopy(activity_list)
        
        total_reward = 0
        activities_placed_this_episode = 0
        
        # Try to assign each activity
        while unassigned_activities:
            activity = unassigned_activities[0]
            
            # Get valid starting slots for this activity
            valid_slots = []
            for slot in slots:
                if can_place_activity(activity, slot, current_schedule, groups_dict, spaces_dict):
                    room_id = find_suitable_room(activity, slot, current_schedule, groups_dict, spaces_dict)
                    if room_id:
                        valid_slots.append(slot)
            
            if not valid_slots:
                # Can't place this activity, remove it and continue
                unassigned_activities.pop(0)
                continue
            
            # Choose action based on epsilon-greedy
            if random.random() < epsilon or len(valid_slots) == 1:
                # Exploration or only one choice
                chosen_slot = random.choice(valid_slots)
            else:
                # Exploitation - choose slot with highest Q-value
                q_values = [(slot, Q_table.get((activity.id, slot), 0.0)) for slot in valid_slots]
                chosen_slot = max(q_values, key=lambda x: x[1])[0]
            
            # Find room and place activity
            room_id = find_suitable_room(activity, chosen_slot, current_schedule, groups_dict, spaces_dict)
            if room_id:
                place_activity(activity, chosen_slot, room_id, current_schedule)
                unassigned_activities.pop(0)
                activities_placed_this_episode += 1
                
                # Get reward for this placement
                current_reward = reward(current_schedule, groups_dict, spaces_dict)
                total_reward += current_reward
                
                # SARSA update: need next state and action
                if unassigned_activities:
                    next_activity = unassigned_activities[0]
                    
                    # Get valid slots for next activity
                    next_valid_slots = []
                    for slot in slots:
                        if can_place_activity(next_activity, slot, current_schedule, groups_dict, spaces_dict):
                            next_room_id = find_suitable_room(next_activity, slot, current_schedule, groups_dict, spaces_dict)
                            if next_room_id:
                                next_valid_slots.append(slot)
                    
                    if next_valid_slots:
                        # Choose next action based on epsilon-greedy
                        if random.random() < epsilon or len(next_valid_slots) == 1:
                            next_chosen_slot = random.choice(next_valid_slots)
                        else:
                            next_q_values = [(slot, Q_table.get((next_activity.id, slot), 0.0)) for slot in next_valid_slots]
                            next_chosen_slot = max(next_q_values, key=lambda x: x[1])[0]
                        
                        # Update Q-table (SARSA update rule)
                        current_q = Q_table.get((activity.id, chosen_slot), 0.0)
                        next_q = Q_table.get((next_activity.id, next_chosen_slot), 0.0)
                        Q_table[(activity.id, chosen_slot)] = current_q + alpha * (current_reward + gamma * next_q - current_q)
                    else:
                        # No valid next action, terminal update
                        current_q = Q_table.get((activity.id, chosen_slot), 0.0)
                        Q_table[(activity.id, chosen_slot)] = current_q + alpha * (current_reward - current_q)
                else:
                    # Last activity, terminal update
                    current_q = Q_table.get((activity.id, chosen_slot), 0.0)
                    Q_table[(activity.id, chosen_slot)] = current_q + alpha * (current_reward - current_q)
            else:
                # Couldn't place activity, remove it
                unassigned_activities.pop(0)
        
        # Resolve conflicts after all assignments
        current_schedule = resolve_conflicts(current_schedule)
        
        # Calculate final reward for this epoch
        final_reward = reward(current_schedule, groups_dict, spaces_dict)
        
        # Update best schedule if better
        if final_reward > best_reward_value:
            best_reward_value = final_reward
            best_schedule = copy.deepcopy(current_schedule)
            print(f"🎯 New best schedule found at episode {epoch}: {activities_placed_this_episode} activities, reward: {final_reward}")
        
        # Evaluate current schedule
        hard_violations, soft_score = evaluate_timetable(
            current_schedule,
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
        population = [current_schedule]
        fitness_values = [(total_hard_violations, soft_score)]
        
        # Record metrics
        metrics_tracker.add_generation_metrics(
            population=population,
            fitness_values=fitness_values,
            generation=epoch
        )
        
        # Decay epsilon
        epsilon = max(epsilon * 0.995, 0.01)
        
        # Print progress every 10 episodes
        if epoch % 10 == 0:
            assigned_count = len(set(activity.id for slot_dict in current_schedule.values() 
                                   for activity in slot_dict.values() if activity))
            print(f"Episode {epoch}: Assigned {assigned_count}/{len(activities_dict)} activities, Reward: {final_reward}")
    
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
    best_schedule, metrics = run_sarsa_optimizer(activities_dict, groups_dict, spaces_dict, lecturers_dict, slots, learning_rate=0.001, episodes=100, epsilon=0.1)
    print(f"Final solution metrics: {metrics}")
