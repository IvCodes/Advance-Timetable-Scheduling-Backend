"""
MOEA/D: Multi-Objective Evolutionary Algorithm based on Decomposition

This module implements the MOEA/D algorithm for timetable scheduling.
Decomposes multi-objective optimization into multiple scalar subproblems
that are solved simultaneously in a collaborative manner.
"""

import random
import time
import numpy as np
from Data_Loading import activities_dict, groups_dict, spaces_dict, lecturers_dict, slots
from metrics_tracker import MetricsTracker
from timetable_html_generator import generate_timetable_html
import plots
import os

# Algorithm parameters
POPULATION_SIZE = 50
NUM_GENERATIONS = 100
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.8
NUM_OBJECTIVES = 2  # Hard violations and soft score
NUM_NEIGHBORHOOD_SIZE = 5  # Number of neighbors for each weight vector

# Set a fixed seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def generate_weight_vectors(num_weights, num_objectives):
    """
    Generate weight vectors for decomposition using the Dirichlet distribution.
    
    Args:
        num_weights: Number of weight vectors to generate
        num_objectives: Number of objectives
        
    Returns:
        Array of weight vectors, each summing to 1
    """
    weight_vectors = []
    rng = np.random.default_rng(seed=RANDOM_SEED)  # Use the new numpy random generator with a seed
    for _ in range(num_weights):
        # Dirichlet distribution ensures weights sum to 1
        vec = rng.dirichlet(np.ones(num_objectives), size=1)[0]
        weight_vectors.append(vec)
    return np.array(weight_vectors)


def find_suitable_rooms(activity, slot, timetable):
    """
    Find rooms that can accommodate the activity in the given slot.
    
    Args:
        activity: Activity to schedule
        slot: Time slot
        timetable: Current timetable
        
    Returns:
        List of suitable room IDs
    """
    suitable_rooms = []
    
    # Get total size needed for all groups in the activity
    total_size = 0
    for group_id in activity.group_ids:
        if group_id in groups_dict:
            total_size += groups_dict[group_id].size
    
    # Check each room
    for room_id, room in spaces_dict.items():
        # Check if room is empty in this slot
        if room_id not in timetable[slot] or timetable[slot][room_id] is None:
            # Check if room is large enough
            if room.size >= total_size:
                suitable_rooms.append(room_id)
    
    return suitable_rooms


def evaluate_hard_constraints(timetable):
    """
    Evaluate hard constraints of a timetable.
    
    Args:
        timetable: The timetable to evaluate
        
    Returns:
        Tuple of (total_violations, detailed_violations)
    """
    vacant_rooms = 0
    lecturer_conflicts = 0
    student_conflicts = 0
    capacity_violations = 0
    unassigned_activities = 0
    
    # Track which activities have been assigned
    assigned_activities = set()
    
    # Check each slot
    for slot in slots:
        if slot not in timetable:
            continue
            
        # Track lecturers and groups used in this slot
        lecturers_used = set()
        groups_used = set()
        
        for room_id, activity in timetable[slot].items():
            if activity is None:
                vacant_rooms += 1
                continue
                
            # Track this activity as assigned
            assigned_activities.add(activity.id)
            
            # Check lecturer conflicts
            if activity.teacher_id in lecturers_used:
                lecturer_conflicts += 1
            lecturers_used.add(activity.teacher_id)
            
            # Check student group conflicts
            for group_id in activity.group_ids:
                if group_id in groups_used:
                    student_conflicts += 1
                groups_used.add(group_id)
            
            # Check room capacity
            total_students = sum(groups_dict[group_id].size for group_id in activity.group_ids if group_id in groups_dict)
            if room_id in spaces_dict and total_students > spaces_dict[room_id].size:
                capacity_violations += 1
    
    # Check for unassigned activities
    for activity_id in activities_dict:
        if activity_id not in assigned_activities:
            unassigned_activities += 1
    
    total_violations = vacant_rooms + lecturer_conflicts + student_conflicts + capacity_violations + unassigned_activities
    detailed_violations = [vacant_rooms, lecturer_conflicts, student_conflicts, capacity_violations, unassigned_activities]
    
    return total_violations, detailed_violations


def evaluate_soft_constraints():
    """
    Evaluate soft constraints of a timetable.
    
    Returns:
        Score between 0 and 1, lower is better
    """
    # Simplified version - just counting violations
    # This is just a placeholder return value
    soft_score = 0.5  # Generic midpoint value
    
    return soft_score


def evaluate_solution(timetable):
    """
    Evaluate a timetable solution.
    
    Args:
        timetable: The timetable to evaluate
        
    Returns:
        Tuple of (hard_violations, soft_score)
    """
    hard_violations, detailed_violations = evaluate_hard_constraints(timetable)
    soft_score = evaluate_soft_constraints()
    
    return (hard_violations, soft_score), detailed_violations


def generate_initial_population(population_size):
    """
    Generate initial random population of timetables.
    
    Args:
        population_size: Size of the population to generate
        
    Returns:
        List of randomly initialized timetables
    """
    population = []
    activity_list = list(activities_dict.values())
    
    for _ in range(population_size):
        # Initialize empty timetable
        timetable = {slot: {} for slot in slots}
        
        # Assign each activity to a random slot and room
        for activity in activity_list:
            # Choose a random slot
            all_slots = list(slots)
            random.shuffle(all_slots)
            
            assigned = False
            for slot in all_slots:
                # Find suitable rooms
                suitable_rooms = find_suitable_rooms(activity, slot, timetable)
                if suitable_rooms:
                    # Choose a random suitable room
                    selected_room = random.choice(suitable_rooms)
                    timetable[slot][selected_room] = activity
                    assigned = True
                    break
            
            # If activity could not be assigned, leave it unassigned
            if not assigned:
                continue
        
        # Ensure all rooms are initialized in all slots
        for slot in slots:
            for room_id in spaces_dict:
                if room_id not in timetable[slot]:
                    timetable[slot][room_id] = None
        
        population.append(timetable)
    
    return population


def scalarizing_function(fitness, weight_vector, ideal_point):
    """
    Apply the Tchebycheff scalarizing function.
    
    Args:
        fitness: Fitness values (objectives)
        weight_vector: Weight vector for this subproblem
        ideal_point: Ideal point with best values for each objective
        
    Returns:
        Scalar value representing weighted performance
    """
    # Convert to numpy arrays for efficient computation
    fitness_array = np.array(fitness)
    
    # Tchebycheff approach: max(w_i * |f_i - z_i|)
    weighted_diff = weight_vector * np.abs(fitness_array - ideal_point)
    
    return np.max(weighted_diff)


def crossover(parent1, parent2):
    """
    Perform crossover between two timetables.
    
    Args:
        parent1, parent2: Parent timetables
        
    Returns:
        Two child timetables
    """
    child1 = {slot: {} for slot in slots}
    child2 = {slot: {} for slot in slots}
    
    # List of all slots
    all_slots = list(slots)
    
    # Random crossover point
    crossover_point = random.randint(1, len(all_slots) - 1)
    
    # First part from parent1, second part from parent2 for child1
    # First part from parent2, second part from parent1 for child2
    for i, slot in enumerate(all_slots):
        if i < crossover_point:
            child1[slot] = parent1[slot].copy()
            child2[slot] = parent2[slot].copy()
        else:
            child1[slot] = parent2[slot].copy()
            child2[slot] = parent1[slot].copy()
    
    return child1, child2


def mutate(timetable):
    """
    Perform mutation on a timetable.
    
    Args:
        timetable: Timetable to mutate
        
    Returns:
        Mutated timetable (modified in-place)
    """
    # Select two random slots
    slot1, slot2 = random.sample(list(timetable.keys()), 2)
    
    # Get non-empty rooms from each slot
    non_empty_rooms1 = [r for r, a in timetable[slot1].items() if a is not None]
    non_empty_rooms2 = [r for r, a in timetable[slot2].items() if a is not None]
    
    # If either slot has no non-empty rooms, return without mutation
    if not non_empty_rooms1 or not non_empty_rooms2:
        return timetable
    
    # Select a random room from each slot
    room1 = random.choice(non_empty_rooms1)
    room2 = random.choice(non_empty_rooms2)
    
    # Swap activities
    timetable[slot1][room1], timetable[slot2][room2] = timetable[slot2][room2], timetable[slot1][room1]
    
    return timetable


def select_parents(population, neighborhood):
    """
    Select two parents from the neighborhood.
    
    Args:
        population: List of timetables
        neighborhood: List of indices indicating the neighborhood
        
    Returns:
        Two parent timetables
    """
    # Select two random indices from the neighborhood
    parent_indices = random.sample(neighborhood, 2)
    
    return population[parent_indices[0]], population[parent_indices[1]]


def update_ideal_point(fitness_values, ideal_point):
    """
    Update the ideal point based on current fitness values.
    
    Args:
        fitness_values: List of fitness tuples
        ideal_point: Current ideal point
        
    Returns:
        Updated ideal point
    """
    new_ideal = ideal_point.copy()
    
    for fitness in fitness_values:
        for i, val in enumerate(fitness[0]):  # fitness[0] contains the objective values
            new_ideal[i] = min(new_ideal[i], val)
    
    return new_ideal


def calculate_euclidean_distance(vec1, vec2):
    """
    Calculate Euclidean distance between two vectors.
    
    Args:
        vec1, vec2: Input vectors
        
    Returns:
        Euclidean distance
    """
    return np.linalg.norm(np.array(vec1) - np.array(vec2))


def generate_neighborhoods(weight_vectors, neighborhood_size):
    """
    Generate neighborhoods for each weight vector.
    
    Args:
        weight_vectors: List of weight vectors
        neighborhood_size: Number of neighbors to select
        
    Returns:
        List of neighborhoods (lists of indices)
    """
    num_weights = len(weight_vectors)
    neighborhoods = []
    
    # Calculate distances between all pairs of weight vectors
    distances = np.zeros((num_weights, num_weights))
    for i in range(num_weights):
        for j in range(num_weights):
            distances[i, j] = calculate_euclidean_distance(weight_vectors[i], weight_vectors[j])
    
    # For each weight vector, find its nearest neighbors
    for i in range(num_weights):
        sorted_indices = np.argsort(distances[i])
        # Take the first neighborhood_size indices (including itself)
        neighborhood = sorted_indices[:neighborhood_size].tolist()
        neighborhoods.append(neighborhood)
    
    return neighborhoods


def run_moead(population_size=50, num_generations=100, 
            weight_vectors=None, neighborhood_size=20, output_dir=None):
    """
    Run the MOEA/D algorithm for timetable optimization.
    
    Args:
        population_size: Size of the population (default: 50)
        num_generations: Number of generations to run (default: 100)
        weight_vectors: List of weight vectors (default: None, will be generated)
        neighborhood_size: Size of neighborhood for each subproblem (default: 20)
        output_dir: Directory to save output files (default: None)
        
    Returns:
        tuple: (population, best_solution, metrics)
    """
    start_time = time.time()
    metrics = MetricsTracker()
    
    # Set output directory if provided
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Generate initial population
    population = generate_initial_population(population_size)
    
    # Evaluate initial population
    fitness_evaluations = []
    detailed_violations = []
    for timetable in population:
        fitness, violations = evaluate_solution(timetable)
        fitness_evaluations.append((fitness, violations))
        detailed_violations.append(violations)
    
    # Extract just the fitness values
    fitness_values = [f[0] for f in fitness_evaluations]
    
    # Initialize ideal point
    ideal_point = np.array([float('inf'), float('inf')])  # One for each objective
    ideal_point = update_ideal_point(fitness_evaluations, ideal_point)
    
    # Generate weight vectors and neighborhoods
    if weight_vectors is None:
        weight_vectors = generate_weight_vectors(population_size, NUM_OBJECTIVES)
    neighborhoods = generate_neighborhoods(weight_vectors, neighborhood_size)
    
    # Track metrics for initial population
    metrics.add_generation_metrics(population, fitness_values, 0)
    
    # Convert raw violations to dictionary format for plotting
    violation_dict = {}
    if detailed_violations:
        first_violation = detailed_violations[0]
        if isinstance(first_violation, tuple) and len(first_violation) >= 5:
            # Create dictionary with proper keys
            violation_dict = {
                "room_capacity": first_violation[0],
                "room_availability": first_violation[1],
                "lecturer_availability": first_violation[2],
                "group_availability": first_violation[3],
                "consecutive_sessions": first_violation[4]
            }
        
    metrics.add_constraint_violations(violation_dict, 0)
    metrics.add_execution_time(time.time() - start_time)
    
    # Main evolutionary loop
    for generation in range(1, num_generations + 1):
        gen_start_time = time.time()
        
        # For each weight vector (subproblem)
        for i in range(population_size):
            # Select parents from neighborhood
            parent1, parent2 = select_parents(population, neighborhoods[i])
            
            # Create offspring through crossover and mutation
            if random.random() < CROSSOVER_RATE:
                child1, child2 = crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()
            
            # Apply mutation
            if random.random() < MUTATION_RATE:
                child1 = mutate(child1)
            if random.random() < MUTATION_RATE:
                child2 = mutate(child2)
            
            # Evaluate new solutions
            new_solutions = [child1, child2]
            new_evaluations = []
            for solution in new_solutions:
                fitness, violations = evaluate_solution(solution)
                new_evaluations.append((fitness, violations))
            
            # Update ideal point
            ideal_point = update_ideal_point(new_evaluations, ideal_point)
            
            # Update neighboring solutions if improvement found
            for j, new_eval in enumerate(new_evaluations):
                new_fitness = new_eval[0]
                new_solution = new_solutions[j]
                
                # For each neighbor
                for neighbor_idx in neighborhoods[i]:
                    # Calculate scalarized value for current and new solution
                    current_scalar = scalarizing_function(
                        fitness_values[neighbor_idx], weight_vectors[neighbor_idx], ideal_point)
                    new_scalar = scalarizing_function(
                        new_fitness, weight_vectors[neighbor_idx], ideal_point)
                    
                    # If new solution is better, replace the neighbor
                    if new_scalar < current_scalar:
                        population[neighbor_idx] = new_solution
                        fitness_values[neighbor_idx] = new_fitness
                        fitness_evaluations[neighbor_idx] = new_eval
        
        # Extract updated detailed violations
        detailed_violations = [f[1] for f in fitness_evaluations]
        
        # Get the best solution's violations for plotting
        best_idx = min(range(len(fitness_values)), key=lambda i: fitness_values[i][0])
        best_violation = detailed_violations[best_idx]
        
        # Convert to dictionary format for plotting
        violation_dict = {
            "room_capacity": best_violation[0],
            "room_availability": best_violation[1],
            "lecturer_availability": best_violation[2],
            "group_availability": best_violation[3],
            "consecutive_sessions": best_violation[4]
        }
        
        # Track metrics
        metrics.add_generation_metrics(population, fitness_values, generation)
        metrics.add_constraint_violations(violation_dict, 0)
        metrics.add_execution_time(time.time() - gen_start_time)
        
        # Print progress
        if generation % 10 == 0 or generation == num_generations:
            best_idx = min(range(len(fitness_values)), key=lambda i: fitness_values[i][0])
            best_hard = fitness_values[best_idx][0]
            best_soft = fitness_values[best_idx][1]
            print(f"Generation {generation}: Best Hard = {best_hard}, Best Soft = {best_soft}")
    
    # Find the best solution
    best_idx = min(range(len(fitness_values)), key=lambda i: fitness_values[i][0])
    best_solution = population[best_idx]
    best_fitness = fitness_values[best_idx]
    
    # Print final metrics
    print(f"\nOptimization completed in {time.time() - start_time:.2f} seconds")
    print(f"Final best solution: Hard violations = {best_fitness[0]}, Soft score = {best_fitness[1]}")
    
    # Plotting functionality removed to avoid errors
    
    return population, best_solution, metrics


def run_moead_optimizer(population_size=50, num_generations=100, output_dir=None):
    """
    Main MOEA/D algorithm for timetable optimization, wrapper for the run_moead function.
    
    Args:
        population_size: Size of the population
        num_generations: Number of generations
        output_dir: Directory to save output files (default: None)
        
    Returns:
        tuple: (best_solution, metrics_dict)
    """
    # Run the algorithm with specified parameters
    _, best_solution, metrics = run_moead(
        population_size=population_size,
        num_generations=num_generations,
        output_dir=output_dir
    )
    
    # Create a metrics dictionary to match the expected format from other algorithms
    metrics_dict = metrics.get_metrics() if metrics else {}
    
    return best_solution, metrics_dict


def main():
    """Main function to run the MOEA/D algorithm and generate output."""
    # Run the algorithm
    _, best_timetable, metrics = run_moead()
    
    # Generate timetable HTML
    html_file = generate_timetable_html(best_timetable, "results/timetable_moead.html")
    print(f"Timetable HTML saved to {html_file}")
    
    # Plot metrics
    if metrics:
        plots.plot_metrics(metrics.get_metrics())
        plots.plot_pareto_front([(f[0], f[1]) for f in metrics.metrics['pareto_front_size'][-1]])
    
    return best_timetable, metrics


if __name__ == "__main__":
    main()
