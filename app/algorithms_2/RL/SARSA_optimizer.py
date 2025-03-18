import random
import copy
import numpy as np
import time
import os

from app.algorithms_2.Data_Loading import Activity, spaces_dict, groups_dict, activities_dict, slots, lecturers_dict
from app.algorithms_2.evaluate import evaluate_hard_constraints, evaluate_soft_constraints, evaluate_timetable
from app.algorithms_2.metrics_tracker import MetricsTracker
from app.algorithms_2.timetable_html_generator import generate_timetable_html

def reward(schedule, groups_dict, spaces_dict):
    """
    Calculate reward for the current schedule
    
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
                # Reward for valid placement
                score += 10

                # Teacher conflict penalty
                teacher = activity[2]  # teacher_id
                if teacher in teacher_assignments and teacher_assignments[teacher] == slot:
                    score -= 20
                else:
                    teacher_assignments[teacher] = slot

                # Group conflict penalty
                for group in activity[3]:  # group_ids
                    if group in group_assignments and group_assignments[group] == slot:
                        score -= 15
                    else:
                        group_assignments[group] = slot

                # Room capacity penalty
                if space in spaces_dict:
                    total_students = sum(groups_dict[group].size for group in activity[3] if group in groups_dict)
                    if total_students > spaces_dict[space].size:
                        score -= 30

    return score

def resolve_conflicts(schedule):
    """
    Attempt to resolve conflicts in the schedule
    
    Args:
        schedule: The current timetable schedule
        
    Returns:
        dict: Updated schedule with attempted conflict resolution
    """
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
        best_space = None
        best_score = float('-inf')
        
        # Try each slot and space combination
        for slot in slots:
            for space in spaces_dict:
                if schedule[slot][space] is None:
                    # Temporarily assign activity
                    schedule[slot][space] = activity
                    curr_score = reward(schedule, groups_dict, spaces_dict)
                    
                    # If better score, remember this placement
                    if curr_score > best_score:
                        best_score = curr_score
                        best_slot = slot
                        best_space = space
                    
                    # Remove temporary assignment
                    schedule[slot][space] = None
        
        # Assign activity to best position found
        if best_slot and best_space:
            schedule[best_slot][best_space] = activity
    
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
    
    # Create the schedule dictionary
    schedule = {slot: {space: None for space in spaces_dict} for slot in slots}
    
    # Convert activity objects to tuples for SARSA
    activity_list = [(activity.id, activity.subject, activity.teacher_id, tuple(activity.group_ids), activity.duration) 
                     for activity in activities_dict.values()]
    
    # SARSA parameters
    gamma = 0.9
    alpha = learning_rate
    
    # Initialize Q-table
    spaces = list(spaces_dict.keys())
    Q_table = {key: np.zeros(len(activity_list)) for key in [(slot, space) for slot in slots for space in spaces]}
    
    # Best schedule tracking
    best_schedule = None
    best_reward_value = float('-inf')
    
    # SARSA Training loop
    for epoch in range(episodes):
        # Initialize schedule and activity lists
        current_schedule = {slot: {space: None for space in spaces} for slot in slots}
        activity_list_copy = copy.deepcopy(activity_list)
        
        # Queue of activities to assign
        activities_to_assign = list(enumerate(activity_list_copy))
        random.shuffle(activities_to_assign)
        
        total_reward = 0
        
        # Assign each activity
        for idx, activity in activities_to_assign:
            # Current state: slot-space pair with no activity
            available_slots_spaces = [(s, sp) for s in slots for sp in spaces if current_schedule[s][sp] is None]
            
            if not available_slots_spaces:
                break  # No available slots left
                
            # Choose action based on epsilon-greedy
            if random.random() < epsilon:
                # Exploration - random slot-space pair
                state = random.choice(available_slots_spaces)
            else:
                # Exploitation - best Q-value
                q_values = [(ss, Q_table[ss][idx]) for ss in available_slots_spaces]
                state = max(q_values, key=lambda x: x[1])[0]
            
            # Assign activity to chosen slot-space
            slot, space = state
            current_schedule[slot][space] = activity
            
            # Get reward for this placement
            current_reward = reward(current_schedule, groups_dict, spaces_dict)
            total_reward += current_reward
            
            # Get next state and action
            next_available = [(s, sp) for s in slots for sp in spaces if current_schedule[s][sp] is None]
            
            if activities_to_assign.index((idx, activity)) < len(activities_to_assign) - 1 and next_available:
                next_idx, next_activity = activities_to_assign[activities_to_assign.index((idx, activity)) + 1]
                
                # Choose next action based on epsilon-greedy
                if random.random() < epsilon:
                    next_state = random.choice(next_available)
                else:
                    next_q_values = [(ss, Q_table[ss][next_idx]) for ss in next_available]
                    next_state = max(next_q_values, key=lambda x: x[1])[0]
                
                # Update Q-table (SARSA update rule)
                current_q = Q_table[state][idx]
                next_q = Q_table[next_state][next_idx]
                Q_table[state][idx] = current_q + alpha * (current_reward + gamma * next_q - current_q)
            
        # Resolve conflicts after all assignments
        current_schedule = resolve_conflicts(current_schedule)
        
        # Calculate final reward for this epoch
        final_reward = reward(current_schedule, groups_dict, spaces_dict)
        
        # Update best schedule if better
        if final_reward > best_reward_value:
            best_reward_value = final_reward
            best_schedule = copy.deepcopy(current_schedule)
        
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
        
        # Print progress
        # print(f"Epoch {epoch + 1}/{episodes}, Reward: {final_reward}, Time: {time.time() - start_time:.2f}s")
    
    # Convert best schedule back to Activity objects for final evaluation
    if best_schedule:
        final_schedule = {slot: {} for slot in slots}
        for slot, spaces_dict_inner in best_schedule.items():
            for space, activity_tuple in spaces_dict_inner.items():
                if activity_tuple:
                    activity_id = activity_tuple[0]
                    final_schedule[slot][space] = activities_dict.get(activity_id, None)
                else:
                    final_schedule[slot][space] = None
        
        # Final evaluation of best solution
        print("Optimization completed. Evaluating best solution...")
        
        hard_violations_tuple, final_soft_score = evaluate_timetable(
            final_schedule,
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
        return final_schedule, metrics_tracker.get_metrics()
    
    return {}, metrics_tracker.get_metrics()

if __name__ == "__main__":
    best_schedule, metrics = run_sarsa_optimizer(activities_dict, groups_dict, spaces_dict, lecturers_dict, slots, learning_rate=0.001, episodes=100, epsilon=0.1)
    print(f"Final solution metrics: {metrics}")
    print(f"Execution time: {time.time() - time.time():.2f} seconds")
