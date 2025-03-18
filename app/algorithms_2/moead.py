import random
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Any, Set
import copy
import time

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

# Algorithm parameters
POPULATION_SIZE = 50
NUM_GENERATIONS = 100
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.8
T = 5  # Size of the neighborhood
NUM_OBJECTIVES = 5  # Number of objectives

# Function to generate weight vectors for decomposition
def generate_weight_vectors(num_weights, num_objectives):
    """
    Generates weight vectors using the Dirichlet distribution, ensuring they sum to 1.
    
    Args:
        num_weights: Number of weight vectors to generate
        num_objectives: Number of objectives (dimensions of each weight vector)
        
    Returns:
        np.ndarray: Array of weight vectors
    """
    weight_vectors = []
    # Use numpy's newer random Generator for better randomness
    rng = np.random.default_rng(42)
    for _ in range(num_weights):
        vec = rng.dirichlet(np.ones(num_objectives), size=1)[0]
        weight_vectors.append(vec)
    return np.array(weight_vectors)

# Tchebycheff scalarizing function
def scalarizing_function(fitness, weight_vector, ideal_point):
    """
    Apply the Tchebycheff approach for decomposition.
    
    Args:
        fitness: Fitness values for an individual
        weight_vector: Weight vector for the subproblem
        ideal_point: Current ideal point
    
    Returns:
        float: Scalarized fitness value
    """
    return np.max(weight_vector * np.abs(np.array(fitness) - np.array(ideal_point)))

# Function to update the ideal point
def update_ideal_point(fitness_values, ideal_point):
    """
    Update the ideal point based on the best objective values found.
    
    Args:
        fitness_values: List of fitness tuples
        ideal_point: Current ideal point
        
    Returns:
        np.ndarray: Updated ideal point
    """
    for fitness in fitness_values:
        ideal_point = np.minimum(ideal_point, np.array(fitness))
    return ideal_point

# Function to select parents from a neighborhood
def select_parents_from_neighborhood(population, neighborhood):
    """
    Select two parents from a given neighborhood for crossover.
    
    Args:
        population: Current population
        neighborhood: Indices of neighbors
        
    Returns:
        tuple: Two selected parents
    """
    parent_indices = random.sample(neighborhood, 2)
    return population[parent_indices[0]], population[parent_indices[1]]

# Crossover function
def crossover(parent1, parent2):
    """
    Perform crossover by swapping time slots between two parents.
    
    Args:
        parent1: First parent timetable
        parent2: Second parent timetable
        
    Returns:
        tuple: Two new offspring timetables
    """
    child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)
    slots = list(parent1.keys())
    split = random.randint(0, len(slots) - 1)
    for i in range(split, len(slots)):
        child1[slots[i]], child2[slots[i]] = parent2[slots[i]], parent1[slots[i]]
    return child1, child2

# Mutation function
def mutate(individual):
    """
    Perform mutation by randomly swapping activities in the timetable.
    
    Args:
        individual: Timetable to mutate
        
    Returns:
        dict: Mutated timetable
    """
    slots = list(individual.keys())
    if len(slots) < 2:
        return individual
    
    slot1, slot2 = random.sample(slots, 2)
    
    # Ensure there are rooms in both slots
    room_keys1 = list(individual[slot1].keys())
    room_keys2 = list(individual[slot2].keys())
    
    if not room_keys1 or not room_keys2:
        return individual
    
    room1 = random.choice(room_keys1)
    room2 = random.choice(room_keys2)
    
    # Swap activities
    individual[slot1][room1], individual[slot2][room2] = individual[slot2][room2], individual[slot1][room1]
    
    return individual

# Generate initial population
def generate_initial_population(slots, spaces_dict, activities_dict, groups_dict, population_size):
    """
    Generate an initial population with random timetables.
    
    Args:
        slots: List of time slots
        spaces_dict: Dictionary of spaces
        activities_dict: Dictionary of activities
        groups_dict: Dictionary of groups
        population_size: Size of the population
        
    Returns:
        list: Initial population of timetables
    """
    population = []
    
    for _ in range(population_size):
        # Initialize empty timetable
        timetable = {}
        activity_slots = {activity_id: [] for activity_id in activities_dict.keys()}
        
        # Make a copy of activities that need to be scheduled
        activities_to_schedule = [activity.id for activity in activities_dict.values() 
                                for _ in range(activity.duration)]
        
        # Initialize empty timetable
        for slot in slots:
            timetable[slot] = {}
            for space_id in spaces_dict.keys():
                timetable[slot][space_id] = None  # Start with all empty
        
        # Try to schedule activities
        for activity_id in activities_to_schedule:
            activity = activities_dict[activity_id]
            activity_size = get_classsize(activity, groups_dict)
            
            # Find suitable slots and rooms
            available_slots = [s for s in slots if s not in activity_slots[activity_id]]
            if not available_slots:
                continue  # Skip if no slots available
                
            chosen_slot = random.choice(available_slots)
            
            # Find suitable rooms in that slot
            suitable_rooms = [
                room_id for room_id, room in spaces_dict.items()
                if room.size >= activity_size and timetable[chosen_slot][room_id] is None
            ]
            
            if not suitable_rooms:
                continue  # Skip if no rooms available
                
            chosen_room = random.choice(suitable_rooms)
            
            # Assign the activity
            timetable[chosen_slot][chosen_room] = activity
            activity_slots[activity_id].append(chosen_slot)
        
        population.append(timetable)
    
    return population

# Helper function to get class size
def get_classsize(activity, groups_dict):
    """
    Calculate the total size of all groups in an activity.
    
    Args:
        activity: Activity object
        groups_dict: Dictionary of groups
        
    Returns:
        int: Total class size
    """
    classsize = 0
    for group_id in activity.group_ids:
        classsize += groups_dict[group_id].size
    return classsize

# Main MOEA/D function
def run_moead_optimizer(activities_dict, groups_dict, spaces_dict, slots, population_size=None, generations=None):
    """
    Main MOEA/D algorithm for timetable optimization.
    
    Args:
        activities_dict: Dictionary of activities
        groups_dict: Dictionary of groups
        spaces_dict: Dictionary of spaces
        slots: List of time slots
        population_size: Size of the population (optional)
        generations: Number of generations (optional)
        
    Returns:
        tuple: Best solution and metrics dictionary
    """
    # Use provided parameters or defaults
    pop_size = population_size if population_size is not None else POPULATION_SIZE
    num_generations = generations if generations is not None else NUM_GENERATIONS
    
    # Initialize metrics tracking to match the format expected by plots.py
    metrics = {
        'generations': list(range(num_generations)),
        'best_hard_violations': [],        # Best hard constraint violations
        'average_hard_violations': [],     # Average hard constraint violations
        'best_soft_score': [],             # Best soft constraint score
        'average_soft_score': [],          # Average soft constraint score
        'best_fitness': [],                # Best overall fitness
        'avg_fitness': [],                 # Average overall fitness
        'hypervolume': [],                 # Hypervolume indicator
        'constraint_violations': [],       # Detailed constraint violations
        'pareto_front_size': [],           # Size of Pareto front
        'execution_time': [],              # Execution time per generation
        'spacing': [],                     # Spacing metric
        'igd': []                          # Inverse Generational Distance
    }
    
    start_time_total = time.time()
    
    # Generate initial population
    print("Generating initial population...")
    population = generate_initial_population(slots, spaces_dict, activities_dict, groups_dict, pop_size)
    
    # Evaluate initial population
    print("Evaluating initial population...")
    fitness_values = [evaluator(timetable, activities_dict, groups_dict, spaces_dict) for timetable in population]
    
    # Initialize ideal point with worst possible values
    ideal_point = np.full(NUM_OBJECTIVES, float('inf'))
    ideal_point = update_ideal_point(fitness_values, ideal_point)
    
    # Generate weight vectors
    print("Generating weight vectors...")
    weight_vectors = generate_weight_vectors(pop_size, NUM_OBJECTIVES)
    
    # Create neighborhoods based on weight vector distances
    print("Creating neighborhoods...")
    distances = np.zeros((pop_size, pop_size))
    for i in range(pop_size):
        for j in range(pop_size):
            distances[i, j] = np.linalg.norm(weight_vectors[i] - weight_vectors[j])
    
    neighborhoods = [list(np.argsort(distances[i])[:T]) for i in range(pop_size)]
    
    # Main algorithm loop
    for generation in range(num_generations):
        start_time_gen = time.time()
        print(f"Generation {generation}: Population size {len(population)}")
        
        new_population = copy.deepcopy(population)
        
        for i in range(pop_size):
            # Select parents from neighborhood
            parent1, parent2 = select_parents_from_neighborhood(population, neighborhoods[i])
            
            # Apply crossover
            if random.random() < CROSSOVER_RATE:
                child1, child2 = crossover(parent1, parent2)
            else:
                child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)
            
            # Apply mutation
            if random.random() < MUTATION_RATE:
                child1 = mutate(child1)
            if random.random() < MUTATION_RATE:
                child2 = mutate(child2)
            
            # Evaluate children
            child1_fitness = evaluator(child1, activities_dict, groups_dict, spaces_dict)
            child2_fitness = evaluator(child2, activities_dict, groups_dict, spaces_dict)
            
            # Update ideal point
            ideal_point = update_ideal_point([child1_fitness, child2_fitness], ideal_point)
            
            # Update subproblems in the neighborhood
            for j in neighborhoods[i]:
                current_scalarized = scalarizing_function(fitness_values[j], weight_vectors[j], ideal_point)
                
                child1_scalarized = scalarizing_function(child1_fitness, weight_vectors[j], ideal_point)
                if child1_scalarized < current_scalarized:
                    new_population[j] = child1
                    fitness_values[j] = child1_fitness
                
                child2_scalarized = scalarizing_function(child2_fitness, weight_vectors[j], ideal_point)
                if child2_scalarized < current_scalarized:
                    new_population[j] = child2
                    fitness_values[j] = child2_fitness
        
        # Update population
        population = new_population
        
        # Calculate metrics for this generation
        hard_violations = [sum(fitness[:3]) for fitness in fitness_values]  # First 3 objectives are hard constraints
        soft_scores = [sum(fitness[3:]) for fitness in fitness_values]      # Last 2 objectives are soft constraints
        
        best_hard_idx = np.argmin(hard_violations)
        best_soft_idx = np.argmin(soft_scores)
        best_overall_idx = np.argmin([sum(fitness) for fitness in fitness_values])
        
        # Store metrics
        metrics['best_hard_violations'].append(hard_violations[best_hard_idx])
        metrics['average_hard_violations'].append(np.mean(hard_violations))
        metrics['best_soft_score'].append(soft_scores[best_soft_idx])
        metrics['average_soft_score'].append(np.mean(soft_scores))
        metrics['best_fitness'].append(sum(fitness_values[best_overall_idx]))
        metrics['avg_fitness'].append(np.mean([sum(fit) for fit in fitness_values]))
        
        # Calculate constraint violations by type
        best_solution = population[best_overall_idx]
        violation_details = detailed_constraint_violations(best_solution, activities_dict, groups_dict, spaces_dict)
        metrics['constraint_violations'].append(violation_details)
        
        # Calculate Pareto front
        non_dominated = find_non_dominated_solutions(fitness_values)
        metrics['pareto_front_size'].append(len(non_dominated))
        
        # Calculate hypervolume
        try:
            hypervolume = calculate_hypervolume([fitness_values[i] for i in non_dominated], 
                                               reference_point=[1000, 1000, 1000, 1000, 1000])
            metrics['hypervolume'].append(hypervolume)
        except Exception as e:
            print(f"Warning: Could not calculate hypervolume: {str(e)}")
            metrics['hypervolume'].append(0)
        
        # Calculate spacing metric (optional)
        try:
            spacing = calculate_spacing([fitness_values[i] for i in non_dominated])
            metrics['spacing'].append(spacing)
        except ValueError as e:
            print(f"Warning: Could not calculate spacing: {str(e)}")
            metrics['spacing'].append(0)
        
        # Calculate IGD (optional - would need reference set)
        metrics['igd'].append(0)  # Placeholder
        
        # Execution time
        generation_time = time.time() - start_time_gen
        metrics['execution_time'].append(generation_time)
    
    # Calculate total execution time
    total_time = time.time() - start_time_total
    
    # Find the best solution
    best_solution = None
    best_fitness_sum = float('inf')
    for i, fitness in enumerate(fitness_values):
        fitness_sum = sum(fitness)
        if fitness_sum < best_fitness_sum:
            best_fitness_sum = fitness_sum
            best_solution = population[i]
    
    print(f"Optimization completed in {total_time:.2f} seconds")
    
    return best_solution, metrics

# Function to find non-dominated solutions (for Pareto front)
def find_non_dominated_solutions(fitness_values):
    """
    Find indices of non-dominated solutions in the population.
    
    Args:
        fitness_values: List of fitness tuples
        
    Returns:
        list: Indices of non-dominated solutions
    """
    non_dominated = []
    for i, fitness_i in enumerate(fitness_values):
        dominated = False
        for j, fitness_j in enumerate(fitness_values):
            if i != j and dominates(fitness_j, fitness_i):
                dominated = True
                break
        if not dominated:
            non_dominated.append(i)
    return non_dominated

# Function to check if one solution dominates another
def dominates(fitness1, fitness2):
    """
    Check if fitness1 dominates fitness2 (Pareto dominance).
    
    Args:
        fitness1: First fitness tuple
        fitness2: Second fitness tuple
        
    Returns:
        bool: True if fitness1 dominates fitness2
    """
    return all(f1 <= f2 for f1, f2 in zip(fitness1, fitness2)) and any(f1 < f2 for f1, f2 in zip(fitness1, fitness2))

# Function for detailed constraint violations
def detailed_constraint_violations(timetable, activities_dict, groups_dict, spaces_dict):
    """
    Get detailed breakdown of constraint violations.
    
    Args:
        timetable: Timetable to evaluate
        activities_dict: Dictionary of activities
        groups_dict: Dictionary of groups
        spaces_dict: Dictionary of spaces
        
    Returns:
        dict: Detailed constraint violations
    """
    vacant_room, prof_conflicts, room_size_conflicts, sub_group_conflicts, unassigned_activities = evaluator(
        timetable, activities_dict, groups_dict, spaces_dict)
    
    return {
        'vacant_rooms': vacant_room,
        'professor_conflicts': prof_conflicts,
        'room_size_conflicts': room_size_conflicts,
        'subgroup_conflicts': sub_group_conflicts,
        'unassigned_activities': unassigned_activities,
        'total': vacant_room + prof_conflicts + room_size_conflicts + sub_group_conflicts + unassigned_activities
    }

# Function to calculate spacing metric
def calculate_spacing(front):
    """
    Calculate spacing metric for the Pareto front.
    
    Args:
        front: List of points in the Pareto front
        
    Returns:
        float: Spacing metric value
    """
    if len(front) < 2:
        return 0
    
    # Calculate distances between consecutive points
    distances = []
    for i in range(len(front) - 1):
        dist = np.linalg.norm(np.array(front[i]) - np.array(front[i+1]))
        distances.append(dist)
    
    # Calculate standard deviation of distances
    return np.std(distances)

# Evaluator function
def evaluator(timetable, activities_dict, groups_dict, spaces_dict):
    """
    Evaluates the timetable based on various constraints.
    
    Args:
        timetable: Timetable to evaluate
        activities_dict: Dictionary of activities
        groups_dict: Dictionary of groups
        spaces_dict: Dictionary of spaces
        
    Returns:
        tuple: Fitness values (vacant_room, prof_conflicts, room_size_conflicts, sub_group_conflicts, unassigned_activities)
    """
    vacant_room = 0
    prof_conflicts = 0
    room_size_conflicts = 0
    sub_group_conflicts = 0
    unassigned_activities = len(activities_dict)
    activities_set = set()

    for slot in timetable:
        prof_set = set()
        sub_group_set = set()
        for room in timetable[slot]:
            activity = timetable[slot][room]

            if not activity:  # If no activity assigned
                vacant_room += 1
            
            elif hasattr(activity, 'id'):  # If it's an activity object
                activities_set.add(activity.id)
                
                if activity.teacher_id in prof_set:
                    prof_conflicts += 1

                # Check for subgroup conflicts
                current_groups = set(activity.group_ids)
                conflicts = len(current_groups.intersection(sub_group_set))
                sub_group_conflicts += conflicts

                # Check room size conflicts
                group_size = sum(groups_dict[group_id].size for group_id in activity.group_ids)
                if group_size > spaces_dict[room].size:
                    room_size_conflicts += 1
                
                # Update sets
                prof_set.add(activity.teacher_id)
                sub_group_set.update(activity.group_ids)

    unassigned_activities -= len(activities_set)
    
    return (vacant_room, prof_conflicts, room_size_conflicts, sub_group_conflicts, unassigned_activities)

# Function to calculate hypervolume
def calculate_hypervolume(front, reference_point=None):
    """
    Calculate the hypervolume indicator for a Pareto front.
    
    Args:
        front: List of points in the Pareto front
        reference_point: Reference point for hypervolume calculation
        
    Returns:
        float: Hypervolume value
    """
    if reference_point is None:
        # Set default reference point if none provided
        reference_point = [1000] * len(front[0])
    
    # Sort points by first objective
    sorted_front = sorted(front, key=lambda x: x[0])
    
    # Simple hypervolume calculation for 2D
    if len(front[0]) == 2:
        hypervolume = 0
        prev_x = reference_point[0]
        for point in sorted_front:
            hypervolume += (prev_x - point[0]) * (reference_point[1] - point[1])
            prev_x = point[0]
        return hypervolume
    
    # For higher dimensions, we would need a more complex algorithm
    # This is a simplified placeholder
    return sum(sum(abs(r - p) for r, p in zip(reference_point, point)) for point in front)

# If this script is run directly
if __name__ == "__main__":
    print("MOEA/D algorithm implementation for timetable scheduling")
    print("This file should be imported and used by run_optimization.py")
