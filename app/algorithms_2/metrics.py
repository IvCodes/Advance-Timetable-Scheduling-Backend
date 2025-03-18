"""
Metrics module for optimization algorithms.
Contains implementations of various performance metrics.
"""

import numpy as np
from evaluate import evaluate_hard_constraints, evaluate_soft_constraints

# Global reference point for hypervolume calculation
REFERENCE_POINT = [1.0, 1.0]  # Default reference point for 2D objectives

def _calculate_simple_hypervolume(points, reference_point):
    """Helper function to calculate hypervolume for cases with limited dimension variation."""
    hypervolume = 1.0
    for i in range(points.shape[1]):
        dimension_min = np.min(points[:, i])
        hypervolume *= (reference_point[i] - dimension_min)
    return hypervolume

def _calculate_2d_hypervolume(points, reference_point):
    """Helper function to calculate hypervolume for 2D fronts."""
    # Sort points by first objective
    sorted_points = points[points[:, 0].argsort()]
    
    # Calculate hypervolume as sum of rectangles
    hypervolume = 0.0
    for i in range(len(sorted_points)):
        if i == 0:
            width = reference_point[0] - sorted_points[i, 0]
            height = reference_point[1] - sorted_points[i, 1]
        else:
            width = sorted_points[i-1, 0] - sorted_points[i, 0]
            height = reference_point[1] - sorted_points[i, 1]
        
        if width > 0 and height > 0:
            hypervolume += width * height
    
    return hypervolume

def _is_point_dominated(sample, points):
    """Check if a sample point is dominated by any point in the front."""
    for point in points:
        if np.all(point <= sample) and np.any(point < sample):
            return True
    return False

def _calculate_monte_carlo_hypervolume(filtered_points, filtered_reference):
    """Calculate hypervolume using Monte Carlo sampling."""
    n_samples = 10000
    
    # Define bounds for sampling
    lower_bounds = np.min(filtered_points, axis=0)
    upper_bounds = filtered_reference
    
    # Generate random points within the reference volume
    rng = np.random.default_rng(seed=42)  # Create a Generator instance with a fixed seed
    samples = rng.uniform(
        low=lower_bounds,
        high=upper_bounds,
        size=(n_samples, len(filtered_reference))
    )
    
    # Count points dominated by the Pareto front
    count_dominated = sum(1 for sample in samples if _is_point_dominated(sample, filtered_points))
    
    # Calculate hypervolume
    dominated_ratio = count_dominated / n_samples
    reference_volume = np.prod(upper_bounds - lower_bounds)
    return dominated_ratio * reference_volume

def calculate_hypervolume(front, reference_point=None):
    """
    Calculate the hypervolume indicator for a Pareto front.
    
    Args:
        front: List of fitness values for solutions in the Pareto front
        reference_point: Reference point for hypervolume calculation (worst possible values)
        
    Returns:
        Hypervolume value
    """
    if not front:
        return 0.0
    
    # Use provided reference point or update the global one
    if reference_point is None:
        reference_point = REFERENCE_POINT
    
    # Convert to numpy array for easier manipulation
    points = np.array(front)
    
    # Check which dimensions have variation
    dimension_ranges = np.ptp(points, axis=0)
    active_dimensions = dimension_ranges > 1e-10
    
    # If we have less than 2 active dimensions, use a simple approach
    if np.sum(active_dimensions) < 2:
        return _calculate_simple_hypervolume(points, reference_point)
    
    # For 2D fronts, use a simpler calculation
    if points.shape[1] == 2:
        return _calculate_2d_hypervolume(points, reference_point)
    
    # For higher dimensions, use a custom calculation approach
    try:
        # Only keep active dimensions to avoid numerical errors
        active_dim_indices = np.nonzero(active_dimensions)[0]
        
        if len(active_dim_indices) < 2:  # Need at least 2 dimensions
            return _calculate_simple_hypervolume(points, reference_point)
        
        # Filter points to only include active dimensions
        filtered_points = points[:, active_dim_indices]
        filtered_reference = np.array(reference_point)[active_dim_indices]
        
        return _calculate_monte_carlo_hypervolume(filtered_points, filtered_reference)
        
    except Exception as e:
        print(f"Error calculating hypervolume: {e}")
        return _calculate_simple_hypervolume(points, reference_point)

def calculate_spacing(front):
    """
    Calculate the spacing metric for a Pareto front.
    
    The spacing metric measures how evenly the solutions are distributed along the front.
    Lower values indicate more uniform spacing.
    
    Args:
        front: List of fitness values for solutions in the Pareto front
        
    Returns:
        Spacing metric value
    """
    if not front or len(front) < 2:
        return 0.0
    
    # Convert to numpy array for easier manipulation
    points = np.array(front)
    n_points = len(points)
    
    # Calculate distances between neighboring points
    distances = []
    
    # For each point, find its closest neighbor
    for i in range(n_points):
        min_distance = float('inf')
        for j in range(n_points):
            if i != j:
                # Calculate Euclidean distance
                distance = np.sqrt(np.sum((points[i] - points[j]) ** 2))
                min_distance = min(min_distance, distance)
        
        if min_distance < float('inf'):
            distances.append(min_distance)
    
    if not distances:
        return 0.0
    
    # Calculate the mean distance
    mean_distance = np.mean(distances)
    
    # Calculate the standard deviation of distances
    variance = np.sum((np.array(distances) - mean_distance) ** 2) / len(distances)
    spacing = np.sqrt(variance)
    
    return spacing

def calculate_igd(front, reference_front):
    """
    Calculate the Inverted Generational Distance (IGD) metric.
    
    IGD measures how far the approximated Pareto front is from the true Pareto front.
    Lower values indicate better convergence to the true front.
    
    Args:
        front: List of fitness values for solutions in the approximated Pareto front
        reference_front: List of fitness values for solutions in the true/reference Pareto front
        
    Returns:
        IGD value
    """
    if not front or not reference_front:
        return float('inf')
    
    # Convert to numpy arrays for easier manipulation
    points = np.array(front)
    reference_points = np.array(reference_front)
    
    # Calculate the minimum distance from each reference point to any point in the front
    sum_distance = 0.0
    for ref_point in reference_points:
        min_distance = float('inf')
        for point in points:
            # Calculate Euclidean distance
            distance = np.sqrt(np.sum((ref_point - point) ** 2))
            min_distance = min(min_distance, distance)
        
        if min_distance < float('inf'):
            sum_distance += min_distance
    
    # Calculate the average distance
    igd = sum_distance / len(reference_points)
    
    return igd

def extract_pareto_front(fitness_values):
    """
    Extract the Pareto front from a set of fitness values.
    
    Args:
        fitness_values: List of fitness values
        
    Returns:
        List of indices forming the Pareto front
    """
    pareto_front = []
    dominated = [False] * len(fitness_values)
    
    for i in range(len(fitness_values)):
        if dominated[i]:
            continue
            
        pareto_front.append(i)
        
        for j in range(i+1, len(fitness_values)):
            if dominated[j]:
                continue
                
            if dominates(fitness_values[i], fitness_values[j]):
                dominated[j] = True
            elif dominates(fitness_values[j], fitness_values[i]):
                dominated[i] = True
                pareto_front.pop()
                break
    
    return pareto_front

def dominates(fitness1, fitness2):
    """
    Check if fitness1 dominates fitness2 (minimization).
    
    Args:
        fitness1: First fitness value tuple
        fitness2: Second fitness value tuple
        
    Returns:
        True if fitness1 dominates fitness2
    """
    return (all(f1 <= f2 for f1, f2 in zip(fitness1, fitness2)) and 
            any(f1 < f2 for f1, f2 in zip(fitness1, fitness2)))

def analyze_constraint_violations(population, activities_dict, groups_dict, spaces_dict):
    """
    Analyze constraint violations across the population.
    
    Args:
        population: List of timetable solutions
        activities_dict: Dictionary of activities
        groups_dict: Dictionary of student groups
        spaces_dict: Dictionary of spaces (rooms)
        
    Returns:
        Dictionary with constraint violation statistics
    """
    # Initialize statistics dictionary
    statistics = {
        'violation_counts': {
            'vacant_rooms': [],
            'lecturer_conflicts': [],
            'student_conflicts': [],
            'capacity_violations': [],
            'unassigned_activities': [],
            'total': []
        },
        'violation_distribution': {
            'vacant_rooms': {},
            'lecturer_conflicts': {},
            'student_conflicts': {},
            'capacity_violations': {},
            'unassigned_activities': {}
        },
        'count_by_severity': {
            'no_violations': 0,
            'minor_violations': 0,  # 1-5 violations
            'moderate_violations': 0,  # 6-20 violations
            'severe_violations': 0   # 21+ violations
        }
    }
    
    # Analyze each solution
    for solution in population:
        # Get constraint violations
        vacant_rooms, lecturer_conflicts, student_conflicts, capacity_violations, unassigned_activities = evaluate_hard_constraints(
            solution, activities_dict, groups_dict, spaces_dict
        )
        
        total_violations = vacant_rooms + lecturer_conflicts + student_conflicts + capacity_violations + unassigned_activities
        
        # Update violation counts
        statistics['violation_counts']['vacant_rooms'].append(vacant_rooms)
        statistics['violation_counts']['lecturer_conflicts'].append(lecturer_conflicts)
        statistics['violation_counts']['student_conflicts'].append(student_conflicts)
        statistics['violation_counts']['capacity_violations'].append(capacity_violations)
        statistics['violation_counts']['unassigned_activities'].append(unassigned_activities)
        statistics['violation_counts']['total'].append(total_violations)
        
        # Update violation distribution
        statistics['violation_distribution']['vacant_rooms'][vacant_rooms] = statistics['violation_distribution']['vacant_rooms'].get(vacant_rooms, 0) + 1
        statistics['violation_distribution']['lecturer_conflicts'][lecturer_conflicts] = statistics['violation_distribution']['lecturer_conflicts'].get(lecturer_conflicts, 0) + 1
        statistics['violation_distribution']['student_conflicts'][student_conflicts] = statistics['violation_distribution']['student_conflicts'].get(student_conflicts, 0) + 1
        statistics['violation_distribution']['capacity_violations'][capacity_violations] = statistics['violation_distribution']['capacity_violations'].get(capacity_violations, 0) + 1
        statistics['violation_distribution']['unassigned_activities'][unassigned_activities] = statistics['violation_distribution']['unassigned_activities'].get(unassigned_activities, 0) + 1
        
        # Update count by severity
        if total_violations == 0:
            statistics['count_by_severity']['no_violations'] += 1
        elif total_violations <= 5:
            statistics['count_by_severity']['minor_violations'] += 1
        elif total_violations <= 20:
            statistics['count_by_severity']['moderate_violations'] += 1
        else:
            statistics['count_by_severity']['severe_violations'] += 1
    
    # Calculate averages and maximums
    statistics['averages'] = {
        'vacant_rooms': np.mean(statistics['violation_counts']['vacant_rooms']),
        'lecturer_conflicts': np.mean(statistics['violation_counts']['lecturer_conflicts']),
        'student_conflicts': np.mean(statistics['violation_counts']['student_conflicts']),
        'capacity_violations': np.mean(statistics['violation_counts']['capacity_violations']),
        'unassigned_activities': np.mean(statistics['violation_counts']['unassigned_activities']),
        'total': np.mean(statistics['violation_counts']['total'])
    }
    
    statistics['maximums'] = {
        'vacant_rooms': np.max(statistics['violation_counts']['vacant_rooms']),
        'lecturer_conflicts': np.max(statistics['violation_counts']['lecturer_conflicts']),
        'student_conflicts': np.max(statistics['violation_counts']['student_conflicts']),
        'capacity_violations': np.max(statistics['violation_counts']['capacity_violations']),
        'unassigned_activities': np.max(statistics['violation_counts']['unassigned_activities']),
        'total': np.max(statistics['violation_counts']['total'])
    }
    
    return statistics
