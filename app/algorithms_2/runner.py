import json
import os
import sys
import importlib
import time
from typing import Dict, Any, Tuple, Optional

# Add the current directory to path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Define a constant for the output directory to reduce duplicated literals
OUTPUT_DIR = "app/algorithms_2/output"

def run_optimization_algorithm(
    algorithm: str,
    population: int = 20,
    generations: int = 10,
    enable_plotting: bool = False,
    learning_rate: float = 0.001,
    episodes: int = 100,
    epsilon: float = 0.1
) -> Dict[str, Any]:
    """
    Run the specified optimization algorithm
    
    Args:
        algorithm: Algorithm name ('spea2', 'nsga2', 'moead', 'dqn', 'sarsa', 'implicit_q')
        population: Population size for evolutionary algorithms
        generations: Number of generations for evolutionary algorithms
        enable_plotting: Whether to generate plots (default: False)
        learning_rate: Learning rate for RL algorithms (default: 0.001)
        episodes: Number of episodes for RL algorithms (default: 100)
        epsilon: Exploration rate for RL algorithms (default: 0.1)
        
    Returns:
        Dict containing results and metrics
    """
    try:
        start_time = time.time()
        
        # Dynamically import the module based on algorithm name
        if algorithm == 'nsga2':
            module_name = 'app.algorithms_2.Nsga_II_optimized'
            function_name = 'run_nsga2_optimizer'
        elif algorithm == 'spea2':
            module_name = 'app.algorithms_2.spea2'
            function_name = 'run_spea2_optimizer'
        elif algorithm == 'moead':
            module_name = 'app.algorithms_2.moead_optimized'
            function_name = 'run_moead_optimizer'
        elif algorithm == 'dqn':
            module_name = 'app.algorithms_2.RL.DQN_optimizer'
            function_name = 'run_dqn_optimizer'
        elif algorithm == 'sarsa':
            module_name = 'app.algorithms_2.RL.SARSA_optimizer'
            function_name = 'run_sarsa_optimizer'
        elif algorithm == 'implicit_q':
            module_name = 'app.algorithms_2.RL.ImplicitQlearning_optimizer'
            function_name = 'run_implicit_qlearning_optimizer'
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        # Import the module
        module = importlib.import_module(module_name)
        
        # Get the optimizer function
        optimizer_func = getattr(module, function_name)
        
        # Run the optimization
        if algorithm in ['dqn', 'sarsa', 'implicit_q']:
            learning_rate_param = learning_rate if learning_rate is not None else 0.001
            episodes_param = episodes if episodes is not None else 100
            epsilon_param = epsilon if epsilon is not None else 0.1
            
            # Get required data structures for the algorithm
            from app.algorithms_2.Data_Loading import activities_dict, groups_dict, spaces_dict, lecturers_dict, slots
            
            if algorithm == 'implicit_q':
                # Implicit Q-learning doesn't use learning rate parameter
                best_solution, metrics = optimizer_func(
                    activities_dict=activities_dict,
                    groups_dict=groups_dict,
                    spaces_dict=spaces_dict,
                    lecturers_dict=lecturers_dict,
                    slots=slots,
                    episodes=episodes_param,
                    epsilon=epsilon_param
                )
            else:
                # For DQN and SARSA
                best_solution, metrics = optimizer_func(
                    activities_dict=activities_dict,
                    groups_dict=groups_dict,
                    spaces_dict=spaces_dict,
                    lecturers_dict=lecturers_dict,
                    slots=slots,
                    learning_rate=learning_rate_param,
                    episodes=episodes_param,
                    epsilon=epsilon_param
                )
        else:
            # For evolutionary algorithms (NSGA-II, SPEA2, MOEAD)
            if algorithm == 'nsga2' or algorithm == 'moead':
                # NSGA-II and MOEAD use num_generations parameter
                best_solution, metrics = optimizer_func(
                    population_size=population,
                    num_generations=generations,
                    output_dir=OUTPUT_DIR
                )
            else:
                # SPEA2 uses generations parameter and enable_plotting
                best_solution, metrics = optimizer_func(
                    population_size=population,
                    generations=generations,
                    output_dir=OUTPUT_DIR,
                    enable_plotting=enable_plotting
                )
        
        # Convert the timetable to a JSON-serializable format
        json_timetable = timetable_to_json(best_solution)
        
        # Get evaluation metrics
        from app.algorithms_2.evaluate import evaluate_timetable
        from app.algorithms_2.Data_Loading import activities_dict, groups_dict, spaces_dict, lecturers_dict, slots
        
        # Convert solution if needed for evaluation
        if algorithm == 'spea2':
            # SPEA2 uses activity IDs instead of activity objects
            converted_solution = {}
            for slot in best_solution:
                converted_solution[slot] = {}
                for room, activity_id in best_solution[slot].items():
                    if activity_id is not None:
                        converted_solution[slot][room] = activities_dict.get(activity_id)
                    else:
                        converted_solution[slot][room] = None
            evaluation_solution = converted_solution
        elif algorithm == 'sarsa':
            # SARSA uses activity tuples instead of activity objects
            converted_solution = {}
            for slot in best_solution:
                converted_solution[slot] = {}
                for room, activity_tuple in best_solution[slot].items():
                    if activity_tuple is not None:
                        activity_id = activity_tuple[0]  # First element is the activity ID
                        converted_solution[slot][room] = activities_dict.get(activity_id)
                    else:
                        converted_solution[slot][room] = None
            evaluation_solution = converted_solution
        else:
            evaluation_solution = best_solution
        
        # Evaluate the solution using the comprehensive evaluation function
        hard_violations, soft_score = evaluate_timetable(
            evaluation_solution, 
            activities_dict, 
            groups_dict, 
            spaces_dict, 
            lecturers_dict, 
            slots,
            verbose=False  # Don't print to console
        )
        
        # Calculate additional metrics
        # Room utilization: percentage of room-slots that have activities assigned
        total_slots = len(slots)
        total_rooms = len(spaces_dict)
        total_room_slots = total_slots * total_rooms
        assigned_room_slots = sum(
            1 for slot in evaluation_solution for room in evaluation_solution.get(slot, {})
            if evaluation_solution[slot][room] is not None
        )
        room_utilization = (assigned_room_slots / total_room_slots) * 100 if total_room_slots > 0 else 0
        
        # Estimate teacher and student satisfaction from soft constraints score
        # Higher soft constraint score means higher satisfaction
        # Normalize to 0-100 range where 100 is best
        normalized_soft_score = min(100, max(0, soft_score * 10))
        teacher_satisfaction = normalized_soft_score
        student_satisfaction = normalized_soft_score
        
        # Time efficiency: measure of how well time slots are utilized across the week
        time_efficiency = min(100, max(0, (1 - hard_violations[4] / len(activities_dict)) * 100)) if activities_dict else 0
        
        execution_time = time.time() - start_time
        
        # Handle MetricsTracker object if present
        algorithm_metrics = {}
        if hasattr(metrics, 'get_metrics'):
            # It's a MetricsTracker object
            algorithm_metrics = metrics.get_metrics()
        elif isinstance(metrics, dict):
            # It's already a dictionary
            algorithm_metrics = metrics
        else:
            # Try to convert to dictionary if it has __dict__ attribute
            try:
                algorithm_metrics = vars(metrics)
            except (TypeError, AttributeError) as e:
                # If all else fails, use string representation
                algorithm_metrics = {"raw_metrics": str(metrics)}
        
        # Compile all metrics
        enhanced_metrics = {
            "hardConstraintViolations": sum(hard_violations[:4]),  # Exclude unassigned activities
            "softConstraintScore": soft_score,
            "unassignedActivities": hard_violations[4],
            "room_utilization": room_utilization,
            "teacher_satisfaction": teacher_satisfaction,
            "student_satisfaction": student_satisfaction,
            "time_efficiency": time_efficiency
        }
        
        return {
            "timetable": json_timetable,
            "metrics": enhanced_metrics,
            "stats": {
                "execution_time": execution_time,
                "original_metrics": algorithm_metrics,  # Convert to serializable dictionary
                "constraint_violations": {
                    "total_counts": {
                        "room_conflicts": hard_violations[0],
                        "time_conflicts": hard_violations[1],
                        "student_conflicts": hard_violations[2],
                        "capacity_violations": hard_violations[3],
                        "unassigned_activities": hard_violations[4]
                    }
                }
            }
        }
    
    except Exception as e:
        # Log the error
        import traceback
        traceback.print_exc()
        # Re-raise the exception with a more informative error message
        raise RuntimeError(f"An error occurred during optimization: {str(e)}") from e

def timetable_to_json(timetable):
    """Convert timetable solution to JSON-serializable format"""
    json_timetable = {}
    
    for slot, rooms in timetable.items():
        json_timetable[slot] = {}
        for room, activity in rooms.items():
            if hasattr(activity, 'id'):
                # For object-based representation (NSGA-II, MOEAD)
                json_timetable[slot][room] = {
                    "id": activity.id,
                    "name": activity.name if hasattr(activity, 'name') else "",
                    "teacher_id": activity.teacher_id if hasattr(activity, 'teacher_id') else "",
                    "group_ids": activity.group_ids if hasattr(activity, 'group_ids') else []
                }
            elif isinstance(activity, str):
                # For ID-based representation (SPEA2)
                from app.algorithms_2.Data_Loading import activities_dict
                act_obj = activities_dict.get(activity)
                if act_obj:
                    json_timetable[slot][room] = {
                        "id": act_obj.id,
                        "name": act_obj.name if hasattr(act_obj, 'name') else "",
                        "teacher_id": act_obj.teacher_id if hasattr(act_obj, 'teacher_id') else "",
                        "group_ids": act_obj.group_ids if hasattr(act_obj, 'group_ids') else []
                    }
                else:
                    json_timetable[slot][room] = None
            else:
                json_timetable[slot][room] = None
    
    return json_timetable

# Helper function to evaluate hard constraints
def evaluate_hard_constraints(timetable, activities_dict, groups_dict, spaces_dict):
    from app.algorithms_2.evaluate import evaluate_hard_constraints
    return evaluate_hard_constraints(timetable, activities_dict, groups_dict, spaces_dict)

# Helper function to calculate soft constraint score
def calculate_soft_score(timetable):
    # Import required data dictionaries
    try:
        from app.algorithms_2.evaluate import evaluate_soft_constraints
        from app.algorithms_2.Data_Loading import groups_dict, lecturers_dict, slots
        
        # Get soft constraint scores - use _ to indicate we're not using individual_scores
        _, final_score = evaluate_soft_constraints(timetable, groups_dict, lecturers_dict, slots)
        
        # Return only the final score as that's what we need for the fitness function
        return final_score
    except ImportError:
        # Return a default value if the function doesn't exist
        return 0.8  # Default score