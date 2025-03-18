import random
import copy
import time
import os

from app.algorithms_2.Data_Loading import Activity, spaces_dict, groups_dict, activities_dict, slots, lecturers_dict
from app.algorithms_2.evaluate import evaluate_hard_constraints, evaluate_soft_constraints, evaluate_timetable
from app.algorithms_2.metrics_tracker import MetricsTracker
from app.algorithms_2.timetable_html_generator import generate_timetable_html

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
                # Reward for valid placement
                score += 10

                # Check for teacher conflicts
                teacher = activity.teacher_id
                if teacher in teacher_assignments and teacher_assignments[teacher] == slot:
                    score -= 20  # Penalize teacher conflict
                else:
                    teacher_assignments[teacher] = slot

                # Check for group conflicts
                for group in activity.group_ids:
                    if group in group_assignments and group_assignments[group] == slot:
                        score -= 15  # Penalize group conflict
                    else:
                        group_assignments[group] = slot

                # Check for student group clashes within the same time slot
                assigned_groups = set()
                for other_space, other_activity in space_dict.items():
                    if other_activity and other_activity != activity:
                        for group in other_activity.group_ids:
                            if group in assigned_groups:
                                score -= 25  # Higher penalty for student group clashes
                            assigned_groups.add(group)
                
                # Room capacity penalty
                if space in spaces_dict:
                    total_students = sum(groups_dict[group].size for group in activity.group_ids if group in groups_dict)
                    if total_students > spaces_dict[space].size:
                        score -= 30  # Penalize exceeding room capacity

    return score

def find_best_position(activity, schedule, groups_dict, spaces_dict):
    """
    Find the best slot and space for an activity based on the highest reward
    
    Args:
        activity: Activity to place
        schedule: Current schedule
        groups_dict: Dictionary of student groups
        spaces_dict: Dictionary of spaces/rooms
        
    Returns:
        tuple: (best_slot, best_space, best_reward)
    """
    best_slot = None
    best_space = None
    best_reward_value = float('-inf')
    
    # Try placing the activity in each possible slot and space
    for slot in slots:
        for space in spaces_dict:
            if schedule[slot][space] is None:
                # Temporarily place activity
                schedule[slot][space] = activity
                
                # Calculate reward
                current_reward = reward(schedule, groups_dict, spaces_dict)
                
                # If better than previous best, update
                if current_reward > best_reward_value:
                    best_reward_value = current_reward
                    best_slot = slot
                    best_space = space
                
                # Remove temporary placement
                schedule[slot][space] = None
    
    return best_slot, best_space, best_reward_value

def run_implicit_qlearning_optimizer(activities_dict, groups_dict, spaces_dict, lecturers_dict, slots, episodes=100, epsilon=0.1):
    """
    Run the Implicit Q-learning optimization algorithm for timetable scheduling
    
    Args:
        activities_dict: Dictionary of activities.
        groups_dict: Dictionary of groups.
        spaces_dict: Dictionary of spaces.
        lecturers_dict: Dictionary of lecturers.
        slots: List of time slots.
        episodes: Number of episodes to run.
        epsilon: Initial epsilon for epsilon-greedy exploration.
        
    Returns:
        best_schedule: The best schedule found.
        metrics: Dictionary of metrics tracking the optimization process.
    """
    metrics_tracker = MetricsTracker()
    
    # Initialize best schedule and score
    best_schedule = None
    best_score = float('-inf')
    
    # Iterate through episodes
    for episode in range(episodes):
        
        # Create a new schedule for this episode
        current_schedule = {slot: {space: None for space in spaces_dict} for slot in slots}
        
        # Shuffle activities to get different ordering in each episode
        episode_activities = list(activities_dict.values())
        random.shuffle(episode_activities)
        
        # Schedule each activity using epsilon-greedy approach
        for activity in episode_activities:
            # Use epsilon-greedy approach for exploration vs exploitation
            if random.random() < epsilon:
                # Exploration: Choose a random valid slot and space
                valid_slots_spaces = []
                for slot in slots:
                    for space in spaces_dict:
                        if current_schedule[slot][space] is None:
                            valid_slots_spaces.append((slot, space))
                
                if valid_slots_spaces:
                    slot, space = random.choice(valid_slots_spaces)
                    current_schedule[slot][space] = activity
            else:
                # Exploitation: Find best slot and space using greedy search
                best_slot, best_space, _ = find_best_position(activity, current_schedule, groups_dict, spaces_dict)
                if best_slot and best_space:
                    current_schedule[best_slot][best_space] = activity
        
        # Evaluate the current schedule
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
        
        metrics_tracker.add_generation_metrics(
            population=population,
            fitness_values=fitness_values,
            generation=episode
        )
        
        # Calculate reward for the current schedule
        current_reward = reward(current_schedule, groups_dict, spaces_dict)
        
        # Update best schedule if current schedule is better
        if current_reward > best_score:
            best_score = current_reward
            best_schedule = copy.deepcopy(current_schedule)
        
    # Final evaluation
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
        execution_time=time.time() - metrics_tracker.start_time
    )
    
    # Return the best schedule and metrics
    return best_schedule, metrics_tracker.get_metrics()

if __name__ == "__main__":
    best_schedule, metrics = run_implicit_qlearning_optimizer(activities_dict, groups_dict, spaces_dict, lecturers_dict, slots, episodes=100, epsilon=0.1)
    print(f"Final solution metrics: {metrics}")
    print(f"Execution time: {time.time() - time.time():.2f} seconds")
