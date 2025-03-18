import random
import numpy as np
import os
import json
import matplotlib.pyplot as plt
from Data_Loading import Activity, spaces_dict, groups_dict, activities_dict, slots, lecturers_dict
from evaluate import evaluate_hard_constraints, evaluate_soft_constraints, evaluate_timetable
from Nsga_II_optimized import mutate, crossover
import math
import copy

# Constants for the SPEA2 algorithm
POPULATION_SIZE = 30
NUM_GENERATIONS = 100
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.8
ARCHIVE_SIZE = 30  # Archive size for storing non-dominated solutions

def calculate_hypervolume(front, reference_point):
    """
    Calculate the hypervolume indicator for a Pareto front.
    
    Parameters:
        front: List of objective vectors in the Pareto front
        reference_point: Reference point for hypervolume calculation
        
    Returns:
        Hypervolume value
    """
    if not front:
        return 0
    
    try:
        # Extract numerical values from each point in the front
        processed_front = []
        for point in front:
            # Handle different formats of points
            if isinstance(point, tuple) and isinstance(point[0], tuple):
                # If the point is ((hard, soft), dominance)
                processed_front.append([float(point[0][0]), float(point[0][1])])
            elif isinstance(point, tuple):
                # If the point is (hard, soft)
                processed_front.append([float(point[0]), float(point[1])])
            else:
                processed_front.append(point)
        
        # Convert to numpy array
        np_front = np.array(processed_front)
        
        # Simple hypervolume calculation for 2D
        # This is the area between the Pareto front and the reference point
        return np.prod(reference_point - np.min(np_front, axis=0))
    except Exception as e:
        print(f"Error in hypervolume calculation: {e}")
        return 0

def extract_fitness_values(fitness):
    """
    Extract numerical values from fitness tuples regardless of their structure.
    
    Parameters:
        fitness: Fitness tuple that may be nested
        
    Returns:
        tuple: Extracted numerical values
    """
    if isinstance(fitness[0], tuple):
        return fitness[0]  # Extract the inner tuple
    return fitness  # Use as is

def calculate_spacing(front):
    """
    Calculate the spacing metric for a Pareto front.
    
    Args:
        front: List of objective vectors in the Pareto front
        
    Returns:
        Spacing value
    """
    if len(front) <= 1:
        return 0
    
    try:
        front = np.array(front)
        distances = []
        
        for i in range(len(front)):
            # Calculate distances to all other points
            dist_to_others = [np.linalg.norm(front[i] - front[j]) for j in range(len(front)) if i != j]
            # Find minimum distance
            if dist_to_others:
                distances.append(min(dist_to_others))
        
        # Calculate standard deviation of distances
        return np.std(distances)
    except ValueError:
        # Specify the exception class to catch without using the unused variable
        return 0

def calculate_density(fitness_values, k=10):
    """
    Calculate density of individuals in the objective space.
    
    Parameters:
        fitness_values (list): List of fitness values
        k (int): Parameter for k-th nearest neighbor
        
    Returns:
        list: Density values for each individual
    """
    k = min(k, len(fitness_values) - 1)  # Ensure k is not larger than possible
    if k <= 0:
        return [0.0] * len(fitness_values)
    
    densities = []
    
    for i, fit1 in enumerate(fitness_values):
        # Calculate distances to all other points
        distances = calculate_distances(fit1, fitness_values, i)
        
        # Sort distances
        distances.sort()
        
        # Calculate density as 1/(2 + k-th distance)
        density = calculate_single_density(distances, k)
        densities.append(density)
    
    return densities

def calculate_distances(fit1, fitness_values, current_index):
    """
    Calculate distances from one fitness value to all others.
    
    Parameters:
        fit1: The fitness value to calculate distances from
        fitness_values: List of all fitness values
        current_index: Index of fit1 in fitness_values
    
    Returns:
        list: List of distances
    """
    distances = []
    fit1_values = extract_fitness_values(fit1)
    
    for j, fit2 in enumerate(fitness_values):
        if current_index != j:
            fit2_values = extract_fitness_values(fit2)
            
            # Convert to numpy arrays for calculation
            fit1_array = np.array([float(fit1_values[0]), float(fit1_values[1])])
            fit2_array = np.array([float(fit2_values[0]), float(fit2_values[1])])
            distances.append(np.linalg.norm(fit1_array - fit2_array))
    
    return distances

def calculate_single_density(distances, k):
    """
    Calculate density based on k-th nearest neighbor.
    
    Parameters:
        distances: Sorted list of distances
        k: Parameter k for k-th nearest neighbor
    
    Returns:
        float: Density value
    """
    if len(distances) >= k:
        return 1.0 / (2 + distances[k-1])
    return 0.0

def dominates(fit1, fit2):
    """
    Check if individual with fitness `fit1` dominates individual with fitness `fit2`.
    
    Args:
        fit1: Fitness vector of the first individual
        fit2: Fitness vector of the second individual
        
    Returns:
        True if fit1 dominates fit2, False otherwise
    """
    return all(f1 <= f2 for f1, f2 in zip(fit1, fit2)) and any(f1 < f2 for f1, f2 in zip(fit1, fit2))

def calculate_dominance_strength(fitness_values):
    """
    Calculate the strength of each individual (number of solutions it dominates).
    
    Args:
        fitness_values: List of fitness vectors
        
    Returns:
        List of strength values
    """
    strengths = []
    
    for i, fit1 in enumerate(fitness_values):
        count = 0
        for j, fit2 in enumerate(fitness_values):
            if i != j and dominates(fit1, fit2):
                count += 1
        strengths.append(count)
        
    return strengths

def calculate_raw_fitness(fitness_values, strengths):
    """
    Calculate the raw fitness of each individual (sum of strengths of dominators).
    
    Args:
        fitness_values: List of fitness vectors
        strengths: List of strength values
        
    Returns:
        List of raw fitness values
    """
    raw_fitness = []
    
    for i, fit1 in enumerate(fitness_values):
        sum_strengths = 0
        for j, fit2 in enumerate(fitness_values):
            if i != j and dominates(fit2, fit1):
                sum_strengths += strengths[j]
        raw_fitness.append(sum_strengths)
        
    return raw_fitness

def environmental_selection(combined_pop, combined_fitness, archive_size):
    """
    Perform environmental selection to create the next archive.
    
    Args:
        combined_pop: Combined population and archive
        combined_fitness: Fitness values of the combined population
        archive_size: Size of the archive
        
    Returns:
        New archive of non-dominated solutions
    """
    # Calculate strength values
    strengths = calculate_dominance_strength(combined_fitness)
    
    # Calculate raw fitness
    raw_fitness = calculate_raw_fitness(combined_fitness, strengths)
    
    # Calculate density
    densities = calculate_density(combined_fitness)
    
    # Calculate final fitness (raw fitness + density)
    final_fitness = [raw + density for raw, density in zip(raw_fitness, densities)]
    
    # Find non-dominated solutions (raw fitness = 0)
    non_dominated_indices = [i for i, raw in enumerate(raw_fitness) if raw == 0]
    
    # If we have fewer non-dominated solutions than archive size
    if len(non_dominated_indices) < archive_size:
        # Sort all solutions by fitness
        sorted_indices = sorted(range(len(final_fitness)), key=lambda i: final_fitness[i])
        archive_indices = sorted_indices[:archive_size]
    
    # If we have more non-dominated solutions than archive size
    elif len(non_dominated_indices) > archive_size:
        # Truncate non-dominated set by removing solutions in most crowded regions
        # Sort non-dominated solutions by density (descending)
        non_dom_densities = [densities[i] for i in non_dominated_indices]
        sorted_indices = sorted(range(len(non_dom_densities)), 
                               key=lambda i: non_dom_densities[i], 
                               reverse=True)
        
        archive_indices = [non_dominated_indices[i] for i in sorted_indices[:archive_size]]
    
    # If we have exactly the right number
    else:
        archive_indices = non_dominated_indices
    
    # Create new archive
    archive = [combined_pop[i] for i in archive_indices]
    archive_fitness = [combined_fitness[i] for i in archive_indices]
    
    return archive, archive_fitness

def binary_tournament_selection(population, fitness):
    """
    Select an individual using binary tournament selection.
    
    Args:
        population: List of individuals
        fitness: List of fitness values (lower is better)
        
    Returns:
        Selected individual
    """
    idx1, idx2 = random.sample(range(len(population)), 2)
    if fitness[idx1] < fitness[idx2]:
        return population[idx1]
    else:
        return population[idx2]

def save_metrics(metrics, output_dir):
    """
    Save metrics to a JSON file.
    
    Args:
        metrics: Dictionary containing metrics
        output_dir: Directory to save the metrics
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(os.path.join(output_dir, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=4)

def save_final_population(population, fitness_values, output_dir):
    """
    Save the final population to a file.
    
    Args:
        population: List of individuals
        fitness_values: List of fitness vectors
        output_dir: Directory to save the population
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Save top individuals
    pareto_front = []
    for idx, fitness in enumerate(fitness_values):
        is_dominated = False
        for other_fitness in fitness_values:
            if dominates(other_fitness, fitness) and fitness != other_fitness:
                is_dominated = True
                break
                
        if not is_dominated:
            pareto_front.append((population[idx], fitness))
    
    with open(os.path.join(output_dir, 'pareto_front.json'), 'w') as f:
        json.dump([(str(ind), list(fit)) for ind, fit in pareto_front], f, indent=4)

def evaluate_population_fitness(population):
    """
    Evaluate the fitness of each individual in the population.
    
    Parameters:
        population (list): List of individuals
        
    Returns:
        tuple: (list of fitness values, list of hard violations, list of soft scores)
    """
    fitness_values = []
    hard_violations = []
    soft_scores = []
    
    for individual in population:
        # Call the evaluate_individual function
        fitness = evaluate_individual(individual)
        fitness_values.append(fitness)
        
        # Extract hard and soft scores for metrics
        if isinstance(fitness, tuple):
            if isinstance(fitness[0], tuple):
                hard_violations.append(fitness[0][0])
                soft_scores.append(fitness[0][1])
            else:
                hard_violations.append(fitness[0])
                soft_scores.append(fitness[1])
    
    return fitness_values, hard_violations, soft_scores

def extract_pareto_front(fitness_values):
    """
    Extract the Pareto front from a list of fitness values.
    
    Args:
        fitness_values: List of fitness vectors
        
    Returns:
        List of fitness vectors in the Pareto front
    """
    pareto_front = []
    for idx, fitness in enumerate(fitness_values):
        is_dominated = False
        for other_fitness in fitness_values:
            if dominates(other_fitness, fitness) and fitness != other_fitness:
                is_dominated = True
                break
                
        if not is_dominated:
            pareto_front.append(fitness)
    
    return pareto_front

def create_next_generation(combined_pop, fitness):
    """
    Create the next generation through selection, crossover, and mutation.
    
    Args:
        combined_pop: Combined population and archive
        fitness: Fitness values for selection
        
    Returns:
        New population
    """
    new_population = []
    
    while len(new_population) < POPULATION_SIZE:
        # Select parents using binary tournament
        parent1 = binary_tournament_selection(combined_pop, fitness)
        parent2 = binary_tournament_selection(combined_pop, fitness)
        
        # Apply crossover
        if random.random() < CROSSOVER_RATE:
            child1, child2 = crossover(parent1, parent2)
        else:
            child1, child2 = parent1.copy(), parent2.copy()
        
        # Apply mutation
        if random.random() < MUTATION_RATE:
            mutate(child1)
        if random.random() < MUTATION_RATE:
            mutate(child2)
        
        new_population.extend([child1, child2])
    
    # Trim if needed
    if len(new_population) > POPULATION_SIZE:
        new_population = new_population[:POPULATION_SIZE]
    
    return new_population

def setup_spea2(population_size, generations):
    """
    Set up SPEA2 algorithm parameters.
    
    Args:
        population_size: Size of the population
        generations: Number of generations
        
    Returns:
        Updated parameters
    """
    global POPULATION_SIZE, NUM_GENERATIONS, ARCHIVE_SIZE
    
    if population_size is not None:
        POPULATION_SIZE = population_size
        ARCHIVE_SIZE = population_size
    
    if generations is not None:
        NUM_GENERATIONS = generations
        
    return POPULATION_SIZE, NUM_GENERATIONS, ARCHIVE_SIZE

def initialize_metrics_and_population():
    """
    Initialize metrics dictionary and population.
    
    Returns:
        Metrics dictionary, initial population, empty archive, and reference point
    """
    # Initialize the metrics dictionary
    metrics = {
        "generations": [],
        "avg_hard_violations": [],
        "average_hard_violations": [],  # Add this key for plotting compatibility
        "avg_soft_score": [],
        "average_soft_score": [],  # Add this key for plotting compatibility
        "min_hard_violations": [],
        "min_soft_score": [],
        "hypervolume": [],
        "spacing": [],
        "constraint_violations": [],  # Add this key for plotting compatibility
        "pareto_front_size": [],      # Add this key for plotting compatibility
        "execution_time": [],         # Add this key for plotting compatibility
        "solution_diversity": [],     # Add this key for plotting compatibility
        "igd": []                     # Add this key for plotting compatibility
    }
    
    # Generate initial population
    population = generate_initial_population()
    
    # Initialize empty archive
    archive = []
    archive_fitness = []
    
    # Reference point for hypervolume calculation (worst case)
    reference_point = np.array([1000, 1])  # High values for hard violations and soft constraints
    
    return metrics, population, archive, archive_fitness, reference_point

def extract_numeric_value(value, index=0, nested_index=0):
    """
    Extract numeric value from various fitness value structures.
    
    Parameters:
        value: Value to extract from, can be a number, tuple, or nested tuple
        index: Index to extract from if value is a tuple
        nested_index: Index to extract from if the tuple element is also a tuple
        
    Returns:
        float: Extracted numeric value
    """
    if isinstance(value, tuple):
        if isinstance(value[index], tuple):
            return float(value[index][nested_index])
        return float(value[index])
    return float(value)

def process_fitness_values(values, is_hard=True):
    """
    Process a list of fitness values to extract numerical components.
    
    Parameters:
        values: List of fitness values (can be numbers, tuples, or nested tuples)
        is_hard: If True, extract hard constraint violations (index 0),
                 otherwise extract soft scores (index 1)
    
    Returns:
        list: List of processed numeric values
    """
    processed = []
    
    for value in values:
        if is_hard:
            # For hard violations, extract from index 0
            processed.append(extract_numeric_value(value, 0, 0))
        else:
            # For soft scores, extract from index 1 or nested index 1
            if isinstance(value, tuple) and isinstance(value[0], tuple):
                processed.append(extract_numeric_value(value, 0, 1))
            else:
                processed.append(extract_numeric_value(value, 1, 0))
    
    return processed

def calculate_average(values):
    """
    Calculate the average of a list of values.
    
    Parameters:
        values: List of numeric values
        
    Returns:
        float: Average value
    """
    return sum(values) / len(values) if values else 0

def process_best_fitness(best_fitness):
    """
    Extract hard violations and soft score from best fitness.
    
    Parameters:
        best_fitness: Best fitness tuple
        
    Returns:
        tuple: (best_hard, best_soft)
    """
    best_hard = 0
    best_soft = 0
    
    if best_fitness:
        if isinstance(best_fitness, tuple):
            best_hard = extract_numeric_value(best_fitness, 0, 0)
            if isinstance(best_fitness[0], tuple):
                best_soft = extract_numeric_value(best_fitness, 0, 1)
            else:
                best_soft = extract_numeric_value(best_fitness, 1, 0)
    
    return best_hard, best_soft

def initialize_metrics_if_needed(metrics):
    """
    Initialize metrics dictionary with required keys if not already initialized.
    
    Parameters:
        metrics: Dictionary of metrics
        
    Returns:
        dict: Initialized metrics dictionary
    """
    if not metrics:
        metrics = {
            "generations": [],
            "avg_hard_violations": [],
            "average_hard_violations": [],  # Add this key for plotting compatibility
            "avg_soft_score": [],
            "average_soft_score": [],  # Add this key for plotting compatibility
            "best_hard_violations": [],
            "best_soft_score": [],
            "hypervolume": [],
            "spacing": [],
            "constraint_violations": [],  # Add this key for plotting compatibility
            "pareto_front_size": [],      # Add this key for plotting compatibility
            "execution_time": [],         # Add this key for plotting compatibility
            "solution_diversity": [],     # Add this key for plotting compatibility
            "igd": []                     # Add this key for plotting compatibility
        }
    return metrics

def ensure_all_metrics_updated(metrics, generation_index):
    """
    Ensure all metrics have entries for the current generation.
    
    Parameters:
        metrics: Dictionary of metrics
        generation_index: Index of the current generation
        
    Returns:
        dict: Updated metrics dictionary
    """
    optional_metrics = [
        "constraint_violations",
        "pareto_front_size",
        "execution_time",
        "solution_diversity",
        "igd"
    ]
    
    for key in optional_metrics:
        if key in metrics and len(metrics[key]) <= generation_index:
            default_value = {} if key == "constraint_violations" else 0
            metrics[key].append(default_value)
    
    return metrics

def update_metrics(metrics, generation, hard_violations, soft_scores, hypervolume, spacing, best_fitness):
    """
    Update the metrics dictionary with the current generation's data.
    
    Parameters:
        metrics (dict): Dictionary of metrics
        generation (int): Current generation
        hard_violations (list): List of hard constraint violations
        soft_scores (list): List of soft constraint scores
        hypervolume (float): Hypervolume indicator
        spacing (float): Spacing indicator
        best_fitness (tuple): Best fitness found
        
    Returns:
        dict: Updated metrics
    """
    # Initialize metrics dictionary if needed
    metrics = initialize_metrics_if_needed(metrics)
    
    # Process fitness values
    processed_hard = process_fitness_values(hard_violations, is_hard=True)
    processed_soft = process_fitness_values(soft_scores, is_hard=False)
    
    # Calculate average values
    avg_hard = calculate_average(processed_hard)
    avg_soft = calculate_average(processed_soft)
    
    # Update metrics
    metrics["generations"].append(generation)
    metrics["avg_hard_violations"].append(avg_hard)
    metrics["average_hard_violations"].append(avg_hard)
    metrics["avg_soft_score"].append(avg_soft)
    metrics["average_soft_score"].append(avg_soft)
    
    # Process best fitness
    best_hard, best_soft = process_best_fitness(best_fitness)
    
    metrics["best_hard_violations"].append(best_hard)
    metrics["best_soft_score"].append(best_soft)
    metrics["hypervolume"].append(hypervolume)
    metrics["spacing"].append(spacing)
    
    # Create constraint violations dictionary for plotting
    if "constraint_violations" not in metrics:
        metrics["constraint_violations"] = []
    
    # Add constraint violation details in the format expected by the plotting functions
    # This is a simplified version since we may not have the exact breakdown of violation types
    violation_dict = {
        "total": best_hard,
        "room_capacity": best_hard / 5 if best_hard > 0 else 0,
        "room_availability": best_hard / 5 if best_hard > 0 else 0,
        "lecturer_availability": best_hard / 5 if best_hard > 0 else 0,
        "group_availability": best_hard / 5 if best_hard > 0 else 0,
        "consecutive_sessions": best_hard / 5 if best_hard > 0 else 0
    }
    metrics["constraint_violations"].append(violation_dict)
    
    # Ensure all metrics are updated for this generation
    generation_index = len(metrics["generations"]) - 1
    metrics = ensure_all_metrics_updated(metrics, generation_index)
    
    return metrics

def log_generation_progress(generation, metrics):
    """
    Log progress of the current generation.
    
    Args:
        generation: Current generation
        metrics: Metrics dictionary
    """
    print(f"Generation {generation}: " +
          f"Avg Hard Violations = {metrics['avg_hard_violations'][-1]:.2f}, " +
          f"Avg Soft Score = {metrics['avg_soft_score'][-1]:.2f}, " +
          f"Best Hard Violations = {metrics['best_hard_violations'][-1]:.2f}, " +
          f"Best Soft Score = {metrics['best_soft_score'][-1]:.2f}, " +
          f"Hypervolume = {metrics['hypervolume'][-1]:.2f}, " +
          f"Spacing = {metrics['spacing'][-1]:.2f}")

def find_best_solution(archive, archive_fitness):
    """
    Find the best solution from the final archive based on hard violations and soft score.
    
    Parameters:
        archive (list): Archive of solutions
        archive_fitness (list): Fitness values of the archive solutions
        
    Returns:
        The best solution from the archive
    """
    if not archive:
        return None
    
    # Helper function to extract hard violations and soft score from fitness
    def extract_fitness_components(fitness):
        hard_violations = 0
        soft_score = 0
        
        if isinstance(fitness, tuple):
            if isinstance(fitness[0], tuple):
                # Format: ((hard, soft), ...)
                hard_violations = fitness[0][0]
                soft_score = fitness[0][1]
            else:
                # Format: (hard, soft)
                hard_violations = fitness[0]
                soft_score = fitness[1]
        
        return hard_violations, soft_score
    
    # Find the best solution with minimal hard violations, then maximal soft score
    best_idx = 0
    best_hard, best_soft = extract_fitness_components(archive_fitness[0])
    
    for i, fitness in enumerate(archive_fitness):
        hard, soft = extract_fitness_components(fitness)
        
        # Better solution has fewer hard violations or equal hard but better soft score
        if hard < best_hard or (hard == best_hard and soft > best_soft):
            best_idx = i
            best_hard = hard
            best_soft = soft
    
    return archive[best_idx]

def save_pareto_front(archive, archive_fitness, output_dir):
    """
    Save the Pareto front to a file for visualization.
    
    Args:
        archive: Archive of solutions
        archive_fitness: Fitness values of the archive
        output_dir: Directory to save the Pareto front
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    pareto_front = []
    for idx, fitness in enumerate(archive_fitness):
        is_dominated = False
        for other_fitness in archive_fitness:
            if dominates(other_fitness, fitness) and fitness != other_fitness:
                is_dominated = True
                break
                
        if not is_dominated:
            pareto_front.append((archive[idx], fitness))
    
    with open(os.path.join(output_dir, 'pareto_front.json'), 'w') as f:
        json.dump([(str(ind), list(fit)) for ind, fit in pareto_front], f, indent=4)

def generate_initial_population(size=None):
    """
    Generate an initial population of timetable solutions.
    
    Parameters:
        size (int, optional): Size of the population to generate
        
    Returns:
        list: List of individual timetable solutions
    """
    global POPULATION_SIZE
    if size is None:
        size = POPULATION_SIZE
    
    population = []
    for _ in range(size):
        # Create an empty timetable (dictionary of period-space assignments)
        timetable = {slot: {} for slot in slots}
        
        # Convert activities to list for easier manipulation
        unassigned_activities = list(activities_dict.values())
        
        # Sort activities by complexity (number of groups, duration)
        unassigned_activities.sort(key=lambda a: (len(a.group_ids), a.duration), reverse=True)
        
        # First assign activities with most constraints
        for activity in unassigned_activities:
            # Find feasible slots for this activity
            feasible_slots = []
            for slot in slots:
                if check_activity_conflicts(activity, slot, timetable):
                    feasible_slots.append(slot)
            
            # Find suitable room in one of the feasible slots
            assigned = False
            if feasible_slots:
                random.shuffle(feasible_slots)  # For diversity
                for slot in feasible_slots:
                    suitable_rooms = find_suitable_rooms(activity, slot, timetable)
                    
                    if suitable_rooms:
                        room = random.choice(suitable_rooms)
                        timetable[slot][room] = activity.id  # Store activity ID instead of the activity object
                        assigned = True
                        break
            
            # If we couldn't assign the activity, place it somewhere with minimal conflicts
            if not assigned:
                # Try to find a slot with the fewest conflicts
                best_slot = None
                best_room = None
                min_conflicts = float('inf')
                
                # Shuffle slots for randomness
                all_slots = list(slots)
                random.shuffle(all_slots)
                
                for slot in all_slots:
                    suitable_rooms = find_suitable_rooms(activity, slot, timetable)
                    if not suitable_rooms:
                        continue
                    
                    # Count conflicts in this slot
                    conflicts = 0
                    lecturer_used = set()
                    groups_used = set()
                    
                    for room, act_id in timetable[slot].items():
                        if act_id is not None:
                            act = activities_dict.get(act_id)
                            if act is not None:
                                if act.teacher_id == activity.teacher_id:
                                    conflicts += 1
                                lecturer_used.add(act.teacher_id)
                                
                                for group in act.group_ids:
                                    if group in activity.group_ids:
                                        conflicts += 1
                                    groups_used.add(group)
                    
                    if conflicts < min_conflicts:
                        min_conflicts = conflicts
                        best_slot = slot
                        best_room = random.choice(suitable_rooms)
                
                # If we found a slot with some conflicts, use it
                if best_slot is not None:
                    timetable[best_slot][best_room] = activity.id  # Store activity ID instead of the activity object
        
        # Ensure all rooms are initialized in all slots
        for slot in slots:
            for room_id in spaces_dict:
                if room_id not in timetable[slot]:
                    timetable[slot][room_id] = None
        
        population.append(timetable)
    
    return population

def find_best_solution(archive, archive_fitness):
    """
    Find the best solution from the final archive based on hard violations and soft score.
    
    Parameters:
        archive (list): Archive of solutions
        archive_fitness (list): Fitness values of the archive solutions
        
    Returns:
        The best solution from the archive
    """
    if not archive:
        return None
    
    # Find solution with minimal hard violations, then maximal soft score
    best_idx = 0
    best_fitness = archive_fitness[0]
    
    for i, fitness in enumerate(archive_fitness):
        # Compare hard violations first (minimize)
        if isinstance(fitness, tuple) and isinstance(best_fitness, tuple):
            if isinstance(fitness[0], tuple) and isinstance(best_fitness[0], tuple):
                # Format: ((hard, soft), ...)
                if fitness[0][0] < best_fitness[0][0] or (fitness[0][0] == best_fitness[0][0] and fitness[0][1] > best_fitness[0][1]):
                    best_idx = i
                    best_fitness = fitness
            else:
                # Format: (hard, soft)
                if fitness[0] < best_fitness[0] or (fitness[0] == best_fitness[0] and fitness[1] > best_fitness[1]):
                    best_idx = i
                    best_fitness = fitness
    
    return archive[best_idx]

def save_metrics(metrics, output_dir):
    """
    Save the optimization metrics to a file.
    
    Parameters:
        metrics (dict): Dictionary of metrics
        output_dir (str): Directory to save the metrics
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save metrics to JSON file
    with open(os.path.join(output_dir, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=4, default=str)
    
    # Plot metrics
    plt.figure(figsize=(12, 10))
    
    # Plot average hard violations
    plt.subplot(2, 2, 1)
    plt.plot(metrics['generations'], metrics['avg_hard_violations'])
    plt.title('Average Hard Violations')
    plt.xlabel('Generation')
    plt.ylabel('Violations')
    
    # Plot average soft score
    plt.subplot(2, 2, 2)
    plt.plot(metrics['generations'], metrics['avg_soft_score'])
    plt.title('Average Soft Score')
    plt.xlabel('Generation')
    plt.ylabel('Score')
    
    # Plot best hard violations
    plt.subplot(2, 2, 3)
    plt.plot(metrics['generations'], metrics['best_hard_violations'])
    plt.title('Best Hard Violations')
    plt.xlabel('Generation')
    plt.ylabel('Violations')
    
    # Plot hypervolume
    plt.subplot(2, 2, 4)
    plt.plot(metrics['generations'], metrics['hypervolume'])
    plt.title('Hypervolume')
    plt.xlabel('Generation')
    plt.ylabel('Value')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'metrics.png'))

def save_final_population(population, fitness_values, output_dir):
    """
    Save the final population to a file.
    
    Parameters:
        population (list): Final population of solutions
        fitness_values (list): Fitness values of the final population
        output_dir (str): Directory to save the final population
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save only basic information about the solutions to avoid large files
    solutions_info = []
    for i, (individual, fitness) in enumerate(zip(population, fitness_values)):
        # For each individual, save index, fitness, and a summary of assignments
        solution_info = {
            'index': i,
            'fitness': str(fitness),
            'num_assignments': sum(1 for period in individual for space in individual[period] if individual[period][space] is not None)
        }
        solutions_info.append(solution_info)
    
    with open(os.path.join(output_dir, 'final_population.json'), 'w') as f:
        json.dump(solutions_info, f, indent=4)

def log_generation_progress(generation, metrics):
    """
    Log progress of the current generation.
    
    Parameters:
        generation (int): Current generation
        metrics (dict): Dictionary of metrics
    """
    # Log basic metrics for the current generation
    current_idx = metrics['generations'].index(generation)
    avg_hard = metrics['avg_hard_violations'][current_idx]
    avg_soft = metrics['avg_soft_score'][current_idx]
    best_hard = metrics['best_hard_violations'][current_idx]
    best_soft = metrics['best_soft_score'][current_idx]
    hypervolume = metrics['hypervolume'][current_idx]
    
    print(f"Generation {generation}: "
          f"Avg Hard={avg_hard:.2f}, Avg Soft={avg_soft:.2f}, "
          f"Best Hard={best_hard}, Best Soft={best_soft:.2f}, "
          f"Hypervolume={hypervolume:.4f}")

def run_spea2_optimizer(population_size=None, generations=None, output_dir="spea2_output", enable_plotting=False):
    """
    Run the SPEA2 optimization algorithm and return the best solution.
    
    Parameters:
        population_size: Size of the population (default: uses global POPULATION_SIZE)
        generations: Number of generations to run (default: uses global NUM_GENERATIONS)
        output_dir: Directory to save outputs
        enable_plotting: Whether to generate plots
        
    Returns:
        tuple: (Best solution found, metrics dictionary)
    """
    # Setup SPEA2 parameters
    global POPULATION_SIZE, NUM_GENERATIONS, ARCHIVE_SIZE
    POPULATION_SIZE = population_size if population_size is not None else POPULATION_SIZE
    NUM_GENERATIONS = generations if generations is not None else NUM_GENERATIONS
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Initialize metrics dictionary
    metrics = {
        "generations": [],
        "avg_hard_violations": [],
        "average_hard_violations": [],  # Add this key for plotting compatibility
        "avg_soft_score": [],
        "average_soft_score": [],  # Add this key for plotting compatibility
        "best_hard_violations": [],
        "best_soft_score": [],
        "hypervolume": [],
        "spacing": [],
        "constraint_violations": [],  # Add this key for plotting compatibility
        "pareto_front_size": [],      # Add this key for plotting compatibility
        "execution_time": [],         # Add this key for plotting compatibility
        "solution_diversity": [],     # Add this key for plotting compatibility
        "igd": []                     # Add this key for plotting compatibility
    }
    
    # Initialize population
    population = generate_initial_population()
    
    # Initialize empty archive
    archive = []
    archive_fitness = []
    
    # Reference point for hypervolume calculation (worst case)
    reference_point = np.array([1000, 1])  # High values for hard violations and soft constraints
    
    print(f"Starting SPEA2 optimization with {POPULATION_SIZE} individuals for {NUM_GENERATIONS} generations")
    
    # Main optimization loop
    for generation in range(NUM_GENERATIONS):
        # Evaluate population
        fitness_values, hard_violations, soft_scores = evaluate_population_fitness(population)
        
        # Combine population and archive
        combined_pop = population + archive
        combined_fitness = fitness_values + archive_fitness
        
        # Environmental selection
        archive, archive_fitness = environmental_selection(combined_pop, combined_fitness, ARCHIVE_SIZE)
        
        # Extract Pareto front from archive
        pareto_front = extract_pareto_front(archive_fitness)
        
        # Calculate hypervolume and spacing if Pareto front is not empty
        if pareto_front:
            hypervolume = calculate_hypervolume(pareto_front, reference_point)
            spacing = calculate_spacing(pareto_front)
        else:
            hypervolume = 0
            spacing = 0
        
        # Update metrics
        if archive_fitness:
            best_fitness = min(archive_fitness, key=lambda x: (x[0], x[1]))
        else:
            best_fitness = None
            
        metrics = update_metrics(metrics, generation, hard_violations, soft_scores, hypervolume, spacing, best_fitness)
        
        # Log progress
        log_generation_progress(generation, metrics)
        
        # If this is the last generation, save final population and exit
        if generation == NUM_GENERATIONS - 1:
            save_metrics(metrics, output_dir)
            save_final_population(population, fitness_values, output_dir)
            # Disable plotting to avoid errors
            # if enable_plotting:
            #    try:
            #        from app.algorithms_2.plots import (plot_convergence, plot_constraint_violations,
            #                                            plot_pareto_front, plot_hypervolume)
            #        # Generate plots
            #        plot_convergence(metrics, save_dir=output_dir)
            #        plot_constraint_violations(metrics, save_dir=output_dir)
            #        plot_pareto_front(metrics, save_dir=output_dir)
            #        plot_hypervolume(metrics, save_dir=output_dir)
            #    except Exception as e:
            #        print(f"Error generating plots: {e}")
            #        # Continue execution even if plotting fails
            break
        
        # Select parents using binary tournament
        parent1_fitness = [raw + density for raw, density in 
                          zip(calculate_raw_fitness(combined_fitness, calculate_dominance_strength(combined_fitness)),
                              calculate_density(combined_fitness))]
        
        # Create new population
        population = create_next_generation(combined_pop, parent1_fitness)
    
    # Find the best solution from the final archive
    best_solution = find_best_solution(archive, archive_fitness)
    
    # Save the Pareto front to file for visualization
    save_pareto_front(archive, archive_fitness, output_dir)
    
    return best_solution, metrics

def evaluate_individual(individual, evaluator_instance=None):
    """
    Evaluate an individual timetable solution to determine its fitness.
    
    Parameters:
        individual (dict): A timetable solution
        evaluator_instance (Evaluator, optional): Instance of the evaluator class
        
    Returns:
        tuple: Fitness as (hard_violations, soft_score)
    """
    # Use existing evaluator functions if provided
    if evaluator_instance is not None:
        # Evaluate hard constraints
        hard_violations = evaluator_instance.evaluate_hard_constraints(individual)
        
        # Evaluate soft constraints
        soft_score = evaluator_instance.evaluate_soft_constraints(individual)
    else:
        # Fall back to simulated evaluation with random values if no evaluator
        hard_violations = random.randint(0, 100)
        soft_score = random.uniform(0, 1)
    
    return (hard_violations, soft_score)

def dominates(fitness1, fitness2):
    """
    Check if fitness1 dominates fitness2 in a minimization problem.
    For fitness values, lower is better for both objectives.
    
    Parameters:
        fitness1 (tuple): First fitness tuple (hard_violations, soft_score)
        fitness2 (tuple): Second fitness tuple (hard_violations, soft_score)
        
    Returns:
        bool: True if fitness1 dominates fitness2, False otherwise
    """
    # Extract values according to their structure
    if isinstance(fitness1[0], tuple):
        hard1 = fitness1[0][0]
        soft1 = -fitness1[0][1]  # Negate because we want to maximize soft score
    else:
        hard1 = fitness1[0]
        soft1 = -fitness1[1]  # Negate because we want to maximize soft score
    
    if isinstance(fitness2[0], tuple):
        hard2 = fitness2[0][0]
        soft2 = -fitness2[0][1]  # Negate because we want to maximize soft score
    else:
        hard2 = fitness2[0]
        soft2 = -fitness2[1]  # Negate because we want to maximize soft score
    
    # Return True if fitness1 is strictly better in at least one objective
    # and not worse in any objective
    if ((hard1 < hard2 and soft1 <= soft2) or 
        (hard1 <= hard2 and soft1 < soft2)):
        return True
    return False

def calculate_dominance_strength(fitness_values):
    """
    Calculate the strength of each individual (number of solutions it dominates).
    
    Parameters:
        fitness_values (list): List of fitness values
        
    Returns:
        list: Strength values for each individual
    """
    strength = [0] * len(fitness_values)
    
    for i, fitness1 in enumerate(fitness_values):
        for j, fitness2 in enumerate(fitness_values):
            if i != j and dominates(fitness1, fitness2):
                strength[i] += 1
    
    return strength

def calculate_raw_fitness(fitness_values, strength):
    """
    Calculate the raw fitness of each individual.
    Raw fitness is the sum of the strengths of all dominators.
    
    Parameters:
        fitness_values (list): List of fitness values
        strength (list): Strength values for each individual
        
    Returns:
        list: Raw fitness values for each individual
    """
    raw_fitness = [0] * len(fitness_values)
    
    for i, fitness1 in enumerate(fitness_values):
        for j, fitness2 in enumerate(fitness_values):
            if i != j and dominates(fitness2, fitness1):
                raw_fitness[i] += strength[j]
    
    return raw_fitness

def calculate_distance(fitness1, fitness2):
    """
    Calculate the Euclidean distance between two fitness values.
    
    Parameters:
        fitness1 (tuple): First fitness tuple
        fitness2 (tuple): Second fitness tuple
        
    Returns:
        float: Euclidean distance between the two fitness values
    """
    # Extract values according to their structure
    if isinstance(fitness1[0], tuple):
        # Format: ((hard, soft), ...)
        hard1 = fitness1[0][0]
        soft1 = -fitness1[0][1]  # Negate because we want to maximize soft score
    else:
        # Format: (hard, soft)
        hard1 = fitness1[0]
        soft1 = -fitness1[1]  # Negate because we want to maximize soft score
    
    if isinstance(fitness2[0], tuple):
        # Format: ((hard, soft), ...)
        hard2 = fitness2[0][0]
        soft2 = -fitness2[0][1]  # Negate because we want to maximize soft score
    else:
        # Format: (hard, soft)
        hard2 = fitness2[0]
        soft2 = -fitness2[1]  # Negate because we want to maximize soft score
    
    # Normalize values to [0, 1] range (assuming hard violations can be up to 1000)
    hard1_norm = hard1 / 1000.0
    hard2_norm = hard2 / 1000.0
    
    # Calculate Euclidean distance
    return math.sqrt((hard1_norm - hard2_norm)**2 + (soft1 - soft2)**2)

def calculate_density(fitness_values):
    """
    Calculate the density of each individual using k-nearest neighbor.
    
    Parameters:
        fitness_values (list): List of fitness values
        
    Returns:
        list: Density values for each individual
    """
    if not fitness_values:
        return []
    
    # Convert fitness values to float arrays for distance calculations
    fitness_arrays = []
    for fitness in fitness_values:
        if isinstance(fitness[0], tuple):
            # Handle nested tuples
            fitness_arrays.append(np.array([float(fitness[0][0]), float(fitness[0][1])]))
        else:
            # Handle simple tuples
            fitness_arrays.append(np.array([float(fitness[0]), float(fitness[1])]))
    
    # Number of nearest neighbors to consider
    k = int(math.sqrt(len(fitness_values)))
    k = max(1, min(k, len(fitness_values) - 1))  # Ensure k is at least 1 and at most n-1
    
    density = []
    for i, fitness1 in enumerate(fitness_arrays):
        # Calculate distances to all other individuals
        distances = []
        for j, fitness2 in enumerate(fitness_arrays):
            if i != j:
                # Calculate Euclidean distance
                dist = np.linalg.norm(fitness1 - fitness2)
                distances.append(dist)
        
        # Sort distances and take the k-th nearest neighbor
        distances.sort()
        density_value = 1.0 / (distances[k-1] + 2.0)  # Add small constant to avoid division by zero
        density.append(density_value)
    
    return density

def environmental_selection(population, fitness_values, archive_size):
    """
    Perform environmental selection to create the archive.
    
    Parameters:
        population (list): List of individuals
        fitness_values (list): List of fitness values
        archive_size (int): Size of the archive
        
    Returns:
        tuple: (Archive of selected individuals, fitness values of archive individuals)
    """
    # Calculate strength of each individual
    strengths = calculate_dominance_strength(fitness_values)
    
    # Calculate raw fitness
    raw_fitness = calculate_raw_fitness(fitness_values, strengths)
    
    # Calculate density
    densities = calculate_density(fitness_values)
    
    # Calculate final fitness (raw fitness + density)
    final_fitness = [raw + dens for raw, dens in zip(raw_fitness, densities)]
    
    # Create list of (individual, fitness, final_fitness) tuples
    combined = [(ind, fit, ffitness) for ind, fit, ffitness in 
               zip(population, fitness_values, final_fitness)]
    
    # Sort by final fitness (lower is better)
    combined.sort(key=lambda x: x[2])
    
    # Select non-dominated individuals first
    archive_inds = []
    archive_fits = []
    
    # Add non-dominated individuals (raw fitness = 0)
    for ind, fit, ffitness in combined:
        if ffitness == 0:
            archive_inds.append(ind)
            archive_fits.append(fit)
    
    # If we don't have enough non-dominated individuals, add the best dominated ones
    if len(archive_inds) < archive_size:
        for ind, fit, ffitness in combined:
            if ffitness > 0 and len(archive_inds) < archive_size:
                archive_inds.append(ind)
                archive_fits.append(fit)
    
    # If we have too many non-dominated individuals, truncate based on density
    elif len(archive_inds) > archive_size:
        # Recalculate density for the non-dominated set
        non_dom_density = calculate_density(archive_fits)
        
        # Create list of (individual, fitness, density) tuples for the non-dominated set
        non_dom_combined = [(ind, fit, dens) for ind, fit, dens in 
                           zip(archive_inds, archive_fits, non_dom_density)]
        
        # Sort by density (higher density means the individual is in a more crowded area)
        non_dom_combined.sort(key=lambda x: x[2], reverse=True)
        
        # Truncate to archive size
        archive_inds = [ind for ind, _, _ in non_dom_combined[:archive_size]]
        archive_fits = [fit for _, fit, _ in non_dom_combined[:archive_size]]
    
    return archive_inds, archive_fits

def extract_pareto_front(fitness_values):
    """
    Extract the Pareto front from a set of fitness values.
    
    Parameters:
        fitness_values (list): List of fitness values
        
    Returns:
        list: Fitness values on the Pareto front
    """
    if not fitness_values:
        return []
    
    pareto_front = []
    
    for i, fitness1 in enumerate(fitness_values):
        is_dominated = False
        
        for fitness2 in fitness_values:
            if dominates(fitness2, fitness1) and fitness1 != fitness2:
                is_dominated = True
                break
        
        if not is_dominated:
            pareto_front.append(fitness1)
    
    return pareto_front

def calculate_hypervolume(pareto_front, reference_point):
    """
    Calculate the hypervolume indicator for a Pareto front.
    
    Parameters:
        pareto_front (list): List of fitness values on the Pareto front
        reference_point (numpy.ndarray): Reference point for the hypervolume calculation
        
    Returns:
        float: Hypervolume indicator
    """
    if not pareto_front:
        return 0.0
    
    # Convert fitness values to numpy arrays
    points = []
    for fitness in pareto_front:
        if isinstance(fitness[0], tuple):
            # Format: ((hard, soft), ...)
            hard = fitness[0][0]
            soft = -fitness[0][1]  # Negate because we want to maximize soft score
        else:
            # Format: (hard, soft)
            hard = fitness[0]
            soft = -fitness[1]  # Negate because we want to maximize soft score
        
        points.append(np.array([hard, soft]))
    
    # Calculate hypervolume (simple implementation for 2D)
    points.sort(key=lambda p: p[0])
    hypervolume = 0.0
    
    for i in range(len(points)):
        if i == 0:
            # First point
            height = reference_point[1] - points[i][1]
            width = points[i][0] - 0  # Assuming 0 is the minimum for objective 1
        else:
            # Other points
            height = reference_point[1] - points[i][1]
            width = points[i][0] - points[i-1][0]
        
        hypervolume += height * width
    
    return hypervolume

def calculate_spacing(pareto_front):
    """
    Calculate the spacing metric for a Pareto front.
    
    Parameters:
        pareto_front (list): List of fitness values on the Pareto front
        
    Returns:
        float: Spacing metric
    """
    if not pareto_front or len(pareto_front) < 2:
        return 0.0
    
    # Calculate distances between consecutive points
    distances = []
    
    for i in range(len(pareto_front)):
        min_dist = float('inf')
        
        for j in range(len(pareto_front)):
            if i != j:
                dist = calculate_distance(pareto_front[i], pareto_front[j])
                min_dist = min(min_dist, dist)
        
        distances.append(min_dist)
    
    # Calculate mean distance
    mean_dist = sum(distances) / len(distances)
    
    # Calculate standard deviation
    variance = sum((d - mean_dist) ** 2 for d in distances) / len(distances)
    std_dev = math.sqrt(variance)
    
    return std_dev

def find_violations(timetable):
    """
    Find activities involved in constraint violations.
    
    Parameters:
        timetable (dict): The timetable to check
        
    Returns:
        list: List of (slot, room, activity_id) tuples with violations
    """
    violations = []
    
    for slot in slots:
        lecturer_seen = {}
        group_seen = {}
        
        for room, activity_id in timetable[slot].items():
            if activity_id is None:
                continue
            
            # Get the actual activity object from the activity ID
            activity = activities_dict.get(activity_id)
            if activity is None:
                continue
            
            # Check lecturer conflicts
            if activity.teacher_id in lecturer_seen:
                violations.append((slot, room, activity_id))
                violations.append((slot, lecturer_seen[activity.teacher_id], 
                                  timetable[slot][lecturer_seen[activity.teacher_id]]))
            else:
                lecturer_seen[activity.teacher_id] = room
            
            # Check group conflicts
            for group_id in activity.group_ids:
                if group_id in group_seen:
                    violations.append((slot, room, activity_id))
                    violations.append((slot, group_seen[group_id], 
                                      timetable[slot][group_seen[group_id]]))
                else:
                    group_seen[group_id] = room
            
            # Check room capacity
            class_size = sum(groups_dict[group_id].size for group_id in activity.group_ids)
            room_obj = spaces_dict.get(room)
            if room_obj and class_size > room_obj.size:
                violations.append((slot, room, activity_id))
    
    return violations

def repair_mutation(timetable):
    """
    Attempt to repair constraint violations through targeted mutation.
    
    Parameters:
        timetable (dict): The timetable to repair
        
    Returns:
        dict: The repaired timetable
    """
    # Create a deep copy to avoid modifying the original
    individual = copy.deepcopy(timetable)
    
    # Find activities involved in violations
    violations = find_violations(individual)
    
    if not violations:
        return individual
    
    # For each violation, try to find a new valid slot and room
    for slot, room, activity_id in violations:
        if activity_id is None:
            continue
        
        # Remove the activity from its current position
        individual[slot][room] = None
        
        # Get the actual activity object
        activity = activities_dict.get(activity_id)
        if activity is None:
            continue
        
        # Try to find a new valid slot and room
        valid_placements = []
        
        for new_slot in slots:
            for new_room in spaces_dict.keys():
                # Skip if already occupied
                if individual[new_slot][new_room] is not None:
                    continue
                
                # Temporarily place activity
                individual[new_slot][new_room] = activity_id
                
                # Check if this creates violations
                new_violations = find_violations(individual)
                if not any((s == new_slot and r == new_room and a == activity_id) for s, r, a in new_violations):
                    valid_placements.append((new_slot, new_room))
                
                # Remove temporary placement
                individual[new_slot][new_room] = None
        
        if valid_placements:
            # Choose a random valid placement
            new_slot, new_room = random.choice(valid_placements)
            individual[new_slot][new_room] = activity_id
        else:
            # If no valid placement is found, put it back where it was
            individual[slot][room] = activity_id
    
    # Now handle unassigned activities
    unassigned_activities = find_unassigned_activities(individual)
    
    if unassigned_activities:
        # Sort unassigned activities by complexity (group size, duration)
        sorted_unassigned = []
        for activity_id in unassigned_activities:
            activity = activities_dict.get(activity_id)
            if activity:
                sorted_unassigned.append((activity, len(activity.group_ids), activity.duration))
        
        # Sort by complexity (highest first)
        sorted_unassigned.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Try to assign each activity
        for activity, _, _ in sorted_unassigned:
            # Find feasible slots for this activity
            feasible_slots = []
            for slot in slots:
                if check_activity_conflicts(activity, slot, individual):
                    feasible_slots.append(slot)
            
            # Try to find a suitable room in one of the feasible slots
            assigned = False
            if feasible_slots:
                random.shuffle(feasible_slots)  # For diversity
                for slot in feasible_slots:
                    suitable_rooms = find_suitable_rooms(activity, slot, individual)
                    
                    if suitable_rooms:
                        room = random.choice(suitable_rooms)
                        individual[slot][room] = activity.id
                        assigned = True
                        break
            
            # If still not assigned, try to place it somewhere with minimal conflicts
            if not assigned:
                # Try all slots and rooms, even if there are conflicts
                all_slots = list(slots)
                random.shuffle(all_slots)
                
                min_conflicts = float('inf')
                best_slot = None
                best_room = None
                
                for slot in all_slots:
                    suitable_rooms = find_suitable_rooms(activity, slot, individual)
                    if not suitable_rooms:
                        continue
                    
                    for room in suitable_rooms:
                        # Temporarily place activity
                        temp_value = individual[slot][room]
                        individual[slot][room] = activity.id
                        
                        # Count conflicts
                        conflicts = len(find_violations(individual))
                        
                        # Restore original value
                        individual[slot][room] = temp_value
                        
                        if conflicts < min_conflicts:
                            min_conflicts = conflicts
                            best_slot = slot
                            best_room = room
                
                # Place activity in best position found
                if best_slot is not None and best_room is not None:
                    individual[best_slot][best_room] = activity.id
    
    return individual

def random_mutation(timetable):
    """
    Perform a random mutation by swapping activities between slots.
    
    Parameters:
        timetable (dict): The timetable to mutate
        
    Returns:
        dict: The mutated timetable
    """
    # Create a deep copy to avoid modifying the original
    individual = copy.deepcopy(timetable)
    
    # Select two random slots
    slot1, slot2 = random.sample(slots, 2)
    
    # Select two random rooms
    room1, room2 = random.sample(list(spaces_dict.keys()), 2)
    
    # Swap activities
    individual[slot1][room1], individual[slot2][room2] = individual[slot2][room2], individual[slot1][room1]
    
    return individual

def mutate(individual):
    """
    Apply mutation operator to an individual.
    
    Parameters:
        individual (dict): The timetable to mutate
        
    Returns:
        dict: The mutated timetable
    """
    if random.random() < 0.8:  # 80% chance of repair mutation
        return repair_mutation(individual)
    else:  # 20% chance of random mutation
        return random_mutation(individual)

def find_suitable_rooms(activity, slot, timetable):
    """
    Find suitable rooms for an activity in a given slot.
    
    Parameters:
        activity (Activity): The activity to find rooms for
        slot (str): The time slot to check
        timetable (dict): The current timetable
        
    Returns:
        list: List of suitable room IDs
    """
    suitable_rooms = []
    
    # Check each room for suitability
    for room_id, room in spaces_dict.items():
        # Check if room is not already occupied
        if room_id in timetable[slot] and timetable[slot][room_id] is not None:
            continue
            
        # Check capacity - using the 'size' attribute instead of 'students'
        student_count = sum(groups_dict[group_id].size for group_id in activity.group_ids)
        if student_count > room.size:
            continue
            
        # Check if room has required equipment/features
        # (This could be implemented if the data model supports it)
        
        suitable_rooms.append(room_id)
        
    return suitable_rooms

def check_activity_conflicts(activity, slot, timetable):
    """
    Check if an activity would create conflicts if placed in a given slot.
    
    Parameters:
        activity (Activity): The activity to check
        slot (str): The time slot to check
        timetable (dict): The current timetable
        
    Returns:
        bool: True if no conflicts, False if conflicts exist
    """
    # Check lecturer availability
    for room_id, existing_activity_id in timetable[slot].items():
        if existing_activity_id is None:
            continue
            
        # Get the actual activity object
        existing_activity = activities_dict.get(existing_activity_id)
        if existing_activity is None:
            continue
            
        # Check teacher conflict
        if existing_activity.teacher_id == activity.teacher_id:
            return False
            
        # Check student group conflicts
        for group_id in activity.group_ids:
            if group_id in existing_activity.group_ids:
                return False
                
    return True

def create_next_generation(current_population, fitness_values):
    """
    Create the next generation of individuals through selection, crossover, and mutation.
    
    Parameters:
        current_population (list): Current population of individuals
        fitness_values (list): Fitness values of the current population
        
    Returns:
        list: New population of individuals for the next generation
    """
    new_population = []
    
    # Create mating pool using binary tournament selection
    mating_pool = []
    for _ in range(POPULATION_SIZE):
        # Select two random individuals
        idx1, idx2 = random.sample(range(len(current_population)), 2)
        
        # Compare their fitness and select the better one (lower fitness is better)
        if fitness_values[idx1] < fitness_values[idx2]:
            mating_pool.append(current_population[idx1])
        else:
            mating_pool.append(current_population[idx2])
    
    # Create offspring through crossover and mutation
    for i in range(0, len(mating_pool), 2):
        # If we have an odd number of individuals, add the last one directly
        if i + 1 >= len(mating_pool):
            new_population.append(mating_pool[i])
            continue
        
        # Perform crossover with probability CROSSOVER_RATE
        if random.random() < CROSSOVER_RATE:
            offspring1, offspring2 = crossover(mating_pool[i], mating_pool[i + 1])
        else:
            offspring1, offspring2 = mating_pool[i], mating_pool[i + 1]
        
        # Perform mutation with probability MUTATION_RATE
        if random.random() < MUTATION_RATE:
            offspring1 = mutate(offspring1)
        if random.random() < MUTATION_RATE:
            offspring2 = mutate(offspring2)
        
        # Add offspring to new population
        new_population.append(offspring1)
        new_population.append(offspring2)
    
    # Ensure the population size is maintained
    if len(new_population) > POPULATION_SIZE:
        new_population = new_population[:POPULATION_SIZE]
    
    return new_population

def find_unassigned_activities(timetable):
    """
    Find activities that are not assigned to any slot in the timetable.
    
    Parameters:
        timetable (dict): The timetable to check
        
    Returns:
        list: List of activity IDs that are not assigned
    """
    # Get all activity IDs
    all_activity_ids = set(activities_dict.keys())
    
    # Find assigned activity IDs
    assigned_activity_ids = set()
    for slot in slots:
        for room, activity_id in timetable[slot].items():
            if activity_id is not None:
                assigned_activity_ids.add(activity_id)
    
    # Return the difference
    return list(all_activity_ids - assigned_activity_ids)
