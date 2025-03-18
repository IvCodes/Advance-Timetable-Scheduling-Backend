import importlib
import json
import os
import sys
from typing import Dict, Any, Tuple, Optional

# Add the current directory to path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

def run_optimization_algorithm(
    algorithm: str,
    population: int = 20,
    generations: int = 10,
    dataset: str = "sliit",
    enable_plotting: bool = False
) -> Dict[str, Any]:
    """
    Run the specified optimization algorithm
    
    Args:
        algorithm: Algorithm name ('spea2', 'nsga2', 'moead')
        population: Population size
        generations: Number of generations
        dataset: Dataset to use ('sliit' or 'current')
        enable_plotting: Whether to generate plots (default: False)
        
    Returns:
        Dict containing results and metrics
    """
    try:
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
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        # Import the module
        module = importlib.import_module(module_name)
        
        # Get the optimizer function
        optimizer_func = getattr(module, function_name)
        
        # Run the optimization
        best_solution, metrics = optimizer_func(
            population_size=population,
            generations=generations,
            output_dir="app/algorithms_2/output",  # Specify output directory
            enable_plotting=enable_plotting  # Pass plotting flag
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
        else:
            evaluation_solution = best_solution
            
        # Evaluate the solution
        hard_violations = evaluate_hard_constraints(evaluation_solution, activities_dict, groups_dict, spaces_dict)
        
        return {
            "timetable": json_timetable,
            "metrics": metrics,
            "hardConstraintViolations": sum(hard_violations),
            "softConstraintScore": calculate_soft_score(evaluation_solution),
            "unassignedActivities": hard_violations[4] if len(hard_violations) > 4 else 0
        }
    
    except Exception as e:
        # Log the error
        import traceback
        traceback.print_exc()
        raise e

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