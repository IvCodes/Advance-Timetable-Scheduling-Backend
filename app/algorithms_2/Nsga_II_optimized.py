import random
import copy
import numpy as np
import time
import os
from Data_Loading import Activity, spaces_dict, groups_dict, activities_dict, slots, lecturers_dict
from evaluate import evaluate_hard_constraints, evaluate_soft_constraints, evaluate_timetable
from metrics_tracker import MetricsTracker
from metrics import extract_pareto_front
from plots import plot_metrics_dashboard, plot_convergence, plot_constraint_violations
from timetable_html_generator import generate_timetable_html

# Enhanced NSGA-II Configuration Parameters
POPULATION_SIZE = 50 # Increased from 50
NUM_GENERATIONS = 50  # Increased from 100
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.8
LOCAL_SEARCH_ITERATIONS = 50  # Number of local search iterations

# Output directory for plots
OUTPUT_DIR = 'results'

# Global tracking variables
vacant_rooms = []
metrics_tracker = MetricsTracker()

def get_classsize(activity: Activity) -> int:
    """
    Calculate the total class size for an activity based on assigned groups.
    
    Parameters:
        activity (Activity): The activity to calculate size for
        
    Returns:
        int: The total class size
    """
    classsize = 0
    for id in activity.group_ids:
        if id in groups_dict:
            classsize += groups_dict[id].size
    return classsize


def evaluator(timetable):
    """
    Evaluate a timetable solution with weighted hard constraints and soft constraints.
    
    Parameters:
        timetable (dict): The timetable solution to evaluate
        
    Returns:
        tuple: A tuple containing (weighted_hard_constraints_score, soft_constraints_score)
    """
    # Hard constraint violations with weights
    hard_violations = evaluate_hard_constraints(timetable, activities_dict, groups_dict, spaces_dict)
    
    # Heavily weight the hard constraints to prioritize their resolution
    weighted_hard_score = (
        hard_violations[0] * 1 +        # Vacant rooms (lower priority)
        hard_violations[1] * 100 +      # Lecturer conflicts (high priority)
        hard_violations[2] * 100 +      # Student group conflicts (high priority)
        hard_violations[3] * 50 +       # Room capacity (medium priority)
        hard_violations[4] * 200        # Unassigned activities (highest priority)
    )
    
    # Soft constraint score (inverted since we're minimizing)
    _, soft_score = evaluate_soft_constraints(timetable, groups_dict, lecturers_dict, slots)
    
    # Return as a tuple for multi-objective optimization
    return (weighted_hard_score, 1.0 - soft_score)


def evaluate_population(population):
    """
    Evaluate the fitness of each individual in the population.
    
    Parameters:
        population (list): List of timetable solutions
        
    Returns:
        list: List of fitness values for each solution
    """
    fitness_values = []
    for timetable in population:
        fitness_values.append(evaluator(timetable))
    return fitness_values


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
    lecturer_available = activity.teacher_id not in [
        timetable[slot][room].teacher_id 
        for room in timetable[slot] 
        if room in timetable[slot] and timetable[slot][room] is not None
    ]
    
    # Check group availability
    current_groups = set()
    for room in timetable[slot]:
        if room in timetable[slot] and timetable[slot][room] is not None:
            current_groups.update(timetable[slot][room].group_ids)
    
    groups_available = all(group_id not in current_groups for group_id in activity.group_ids)
    
    return lecturer_available and groups_available


def find_suitable_rooms(activity, slot, timetable):
    """
    Find suitable rooms for an activity in a given slot.
    
    Parameters:
        activity (Activity): The activity to place
        slot (str): The time slot
        timetable (dict): The current timetable
        
    Returns:
        list: List of suitable room IDs
    """
    activity_size = get_classsize(activity)
    
    # Find rooms with sufficient capacity that aren't already occupied
    suitable_rooms = [
        room_id for room_id, room in spaces_dict.items() 
        if room.size >= activity_size and (
            room_id not in timetable[slot] or 
            timetable[slot][room_id] is None
        )
    ]
    
    return suitable_rooms


def generate_initial_population():
    """
    Generate an initial population using a constraint-based approach.
    
    Returns:
        list: A list of timetable solutions (population)
    """
    population = []
    
    for _ in range(POPULATION_SIZE):
        # Start with an empty timetable
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
                        timetable[slot][room] = activity
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
                    
                    for room, act in timetable[slot].items():
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
                    timetable[best_slot][best_room] = activity
        
        # Ensure all rooms are initialized in all slots
        for slot in slots:
            for room_id in spaces_dict:
                if room_id not in timetable[slot]:
                    timetable[slot][room_id] = None
        
        population.append(timetable)
    
    return population


def find_violations(timetable):
    """
    Find activities involved in constraint violations.
    
    Parameters:
        timetable (dict): The timetable to check
        
    Returns:
        list: List of (slot, room, activity) tuples with violations
    """
    violations = []
    
    # Check for lecturer and student group conflicts
    for slot in timetable:
        lecturer_seen = {}
        group_seen = {}
        
        for room, activity in timetable[slot].items():
            if activity is None:
                continue
            
            # Check lecturer conflicts
            if activity.teacher_id in lecturer_seen:
                violations.append((slot, room, activity))
                violations.append((slot, lecturer_seen[activity.teacher_id], 
                                  timetable[slot][lecturer_seen[activity.teacher_id]]))
            else:
                lecturer_seen[activity.teacher_id] = room
            
            # Check group conflicts
            for group_id in activity.group_ids:
                if group_id in group_seen:
                    violations.append((slot, room, activity))
                    violations.append((slot, group_seen[group_id], 
                                      timetable[slot][group_seen[group_id]]))
                else:
                    group_seen[group_id] = room
            
            # Check room capacity
            if get_classsize(activity) > spaces_dict[room].size:
                violations.append((slot, room, activity))
    
    # Remove duplicates
    unique_violations = []
    seen = set()
    for v in violations:
        if (v[0], v[1]) not in seen:
            unique_violations.append(v)
            seen.add((v[0], v[1]))
    
    return unique_violations


def repair_mutation(individual):
    """
    Attempt to repair constraint violations through targeted mutation.
    
    Parameters:
        individual (dict): The timetable to repair
        
    Returns:
        dict: The repaired timetable
    """
    # Make a copy to avoid modifying the original during repair attempts
    timetable = copy.deepcopy(individual)
    
    # Find activities involved in violations
    violations = find_violations(timetable)
    
    if not violations:
        # If no violations, perform random mutation
        return random_mutation(timetable)
    
    # Select a random violation to fix
    slot, room, activity = random.choice(violations)
    
    # Try to find a better slot for this activity
    target_slots = [s for s in slots if s != slot]
    random.shuffle(target_slots)
    
    # Try to move the activity to a new slot with no conflicts
    for target_slot in target_slots:
        if check_activity_conflicts(activity, target_slot, timetable):
            # Find available rooms in the target slot
            suitable_rooms = find_suitable_rooms(activity, target_slot, timetable)
            
            if suitable_rooms:
                target_room = random.choice(suitable_rooms)
                # Remove from current slot and place in new slot
                timetable[slot][room] = None
                timetable[target_slot][target_room] = activity
                return timetable
    
    # If no conflict-free slot found, try swapping with another activity
    target_slot = random.choice(target_slots)
    rooms_in_target = [r for r in timetable[target_slot] if timetable[target_slot][r] is not None]
    
    if rooms_in_target:
        target_room = random.choice(rooms_in_target)
        # Swap the activities
        timetable[slot][room], timetable[target_slot][target_room] = (
            timetable[target_slot][target_room], timetable[slot][room]
        )
    
    return timetable


def random_mutation(individual):
    """
    Perform a random mutation by swapping activities.
    
    Parameters:
        individual (dict): The timetable to mutate
        
    Returns:
        dict: The mutated timetable
    """
    timetable = copy.deepcopy(individual)
    
    # Get all slots with at least one activity
    non_empty_slots = [
        slot for slot in timetable 
        if any(timetable[slot].values())
    ]
    
    if len(non_empty_slots) < 2:
        return timetable  # Not enough activities to swap
    
    # Pick two random slots
    slot1, slot2 = random.sample(non_empty_slots, 2)
    
    # Choose rooms from each slot
    room1 = random.choice(list(timetable[slot1].keys()))
    room2 = random.choice(list(timetable[slot2].keys()))
    
    # Swap activities
    timetable[slot1][room1], timetable[slot2][room2] = (
        timetable[slot2][room2], timetable[slot1][room1]
    )
    
    return timetable


def mutate(individual):
    """
    Apply mutation operator based on repair or random mutation.
    
    Parameters:
        individual (dict): The timetable to mutate
        
    Returns:
        dict: The mutated timetable
    """
    # 80% chance to try repair-based mutation, 20% for random mutation
    if random.random() < 0.8:
        return repair_mutation(individual)
    else:
        return random_mutation(individual)


def crossover(parent1, parent2):
    """
    Perform crossover while preserving constraints where possible.
    
    Parameters:
        parent1 (dict): First parent timetable
        parent2 (dict): Second parent timetable
        
    Returns:
        tuple: Two child timetables
    """
    child1 = copy.deepcopy(parent1)
    child2 = copy.deepcopy(parent2)
    
    # Choose a random crossover point
    slot_list = list(parent1.keys())
    crossover_point = random.randint(1, len(slot_list) - 1)
    
    # Swap the second half of the timetables
    for i in range(crossover_point, len(slot_list)):
        slot = slot_list[i]
        child1[slot], child2[slot] = copy.deepcopy(parent2[slot]), copy.deepcopy(parent1[slot])
    
    return child1, child2


def dominates(fitness1, fitness2):
    """
    Check if fitness1 dominates fitness2 in a minimization context.
    
    Parameters:
        fitness1 (tuple): First fitness values
        fitness2 (tuple): Second fitness values
        
    Returns:
        bool: True if fitness1 dominates fitness2
    """
    return (all(f1 <= f2 for f1, f2 in zip(fitness1, fitness2)) and 
            any(f1 < f2 for f1, f2 in zip(fitness1, fitness2)))


def fast_nondominated_sort(fitness_values):
    """
    Perform fast non-dominated sorting to rank solutions.
    
    Parameters:
        fitness_values (list): List of fitness values
        
    Returns:
        list: List of fronts, where each front is a list of indices
    """
    n = len(fitness_values)
    dominated_by = [[] for _ in range(n)]
    domination_count = [0] * n
    fronts = [[]]
    
    # Determine domination relationships
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
                
            if dominates(fitness_values[i], fitness_values[j]):
                dominated_by[i].append(j)
            elif dominates(fitness_values[j], fitness_values[i]):
                domination_count[i] += 1
        
        # If not dominated by anyone, it's in the first front
        if domination_count[i] == 0:
            fronts[0].append(i)
    
    # Generate subsequent fronts
    front_index = 0
    while fronts[front_index]:
        next_front = []
        
        for i in fronts[front_index]:
            for j in dominated_by[i]:
                domination_count[j] -= 1
                if domination_count[j] == 0:
                    next_front.append(j)
        
        front_index += 1
        fronts.append(next_front)
    
    # Remove the empty front at the end
    return fronts[:-1]


def calculate_crowding_distance(front, fitness_values):
    """
    Calculate crowding distance for diversity preservation.
    
    Parameters:
        front (list): List of indices forming a front
        fitness_values (list): List of fitness values
        
    Returns:
        list: Crowding distances for individuals in the front
    """
    if len(front) <= 2:
        return [float('inf')] * len(front)
    
    n = len(front)
    distances = [0.0] * n
    objectives = len(fitness_values[0])
    
    for obj in range(objectives):
        # Sort front by current objective
        sorted_front = sorted(front, key=lambda i: fitness_values[i][obj])
        
        # Set boundary points to infinity
        distances[0] = distances[-1] = float('inf')
        
        if fitness_values[sorted_front[-1]][obj] == fitness_values[sorted_front[0]][obj]:
            continue
        
        # Calculate distance for intermediate points
        norm = fitness_values[sorted_front[-1]][obj] - fitness_values[sorted_front[0]][obj]
        for i in range(1, n-1):
            distances[i] += (
                fitness_values[sorted_front[i+1]][obj] - 
                fitness_values[sorted_front[i-1]][obj]
            ) / norm
    
    return distances


def selection(population, fitness_values):
    """
    Select next generation based on non-dominated sorting and crowding distance.
    
    Parameters:
        population (list): Current population
        fitness_values (list): Fitness values for the population
        
    Returns:
        list: Selected individuals for next generation
    """
    # Get the non-dominated fronts
    fronts = fast_nondominated_sort(fitness_values)
    
    next_generation = []
    front_idx = 0
    
    # Add complete fronts until we reach population size
    while len(next_generation) + len(fronts[front_idx]) <= POPULATION_SIZE:
        next_generation.extend([population[i] for i in fronts[front_idx]])
        front_idx += 1
        
        # If we've used all fronts, break
        if front_idx >= len(fronts):
            break
    
    # If we need more individuals to fill the population
    if len(next_generation) < POPULATION_SIZE and front_idx < len(fronts):
        # Calculate crowding distance for the last front
        distances = calculate_crowding_distance(fronts[front_idx], fitness_values)
        
        # Sort by crowding distance (larger is better)
        last_front_sorted = sorted(
            [(i, dist) for i, dist in zip(fronts[front_idx], distances)],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Add individuals from the last front until we reach population size
        remaining = POPULATION_SIZE - len(next_generation)
        for i, _ in last_front_sorted[:remaining]:
            next_generation.append(population[i])
    
    return next_generation


def find_best_solution(population):
    """
    Find the best solution in the population based on constraint violations.
    
    Parameters:
        population (list): Population to evaluate
        
    Returns:
        dict: Best solution found
    """
    best_solution = None
    minimum_violations = float('inf')
    
    for solution in population:
        # Calculate total violations
        hard_violations = evaluate_hard_constraints(solution, activities_dict, groups_dict, spaces_dict)
        violations = sum(hard_violations)
        
        # If this solution has fewer violations, update best
        if violations < minimum_violations:
            minimum_violations = violations
            best_solution = solution
    
    print("Best solution has " + str(minimum_violations) + " total violations.")
    return best_solution


def run_nsga2_optimizer(
    population_size=50,
    num_generations=50,
    crossover_rate=0.8,
    mutation_rate=0.1,
    output_dir="."
):
    """
    Main function to run the NSGA-II optimizer.
    
    Args:
        population_size: Size of the population
        num_generations: Number of generations to run
        crossover_rate: Probability of crossover
        mutation_rate: Probability of mutation
        output_dir: Directory to save output files
    
    Returns:
        best_solution: Best solution found
        metrics_tracker: Object containing optimization metrics
    """
    global POPULATION_SIZE, NUM_GENERATIONS, OUTPUT_DIR, CROSSOVER_RATE, MUTATION_RATE
    
    # Override global parameters if provided
    if population_size is not None:
        POPULATION_SIZE = population_size
    if num_generations is not None:
        NUM_GENERATIONS = num_generations
    if crossover_rate is not None:
        CROSSOVER_RATE = crossover_rate
    if mutation_rate is not None:
        MUTATION_RATE = mutation_rate
    if output_dir is not None:
        OUTPUT_DIR = output_dir
        # Ensure the directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"Starting NSGA-II optimization with population={POPULATION_SIZE}, generations={NUM_GENERATIONS}...")
    
    # Setup phase
    setup_optimization()
    
    # Main optimization loop
    population = generate_initial_population()
    start_time = time.time()
    
    # Evolution over generations
    for generation in range(NUM_GENERATIONS):
        population = run_single_generation(population, generation)
    
    # Find the best solution in the final population
    best_solution = find_best_solution(population)
    
    # Generate final results
    generate_final_results(best_solution, start_time)
    
    return best_solution, metrics_tracker


def setup_optimization():
    """Set up the optimization environment and metrics tracker."""
    global metrics_tracker
    metrics_tracker = MetricsTracker()
    
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Set reference point for hypervolume calculation
    reference_point = [float('inf'), 1.0]
    metrics_tracker.reference_point = reference_point


def run_single_generation(population, generation):
    """
    Run a single generation of the NSGA-II algorithm.
    
    Args:
        population: Current population
        generation: Current generation number
        
    Returns:
        Updated population
    """
    generation_start_time = time.time()
    
    # Print progress periodically
    if generation % 10 == 0:
        print(f"Generation {generation}/{NUM_GENERATIONS}...")
    
    # Evaluate current population
    fitness_values = evaluate_population(population)
    
    # Track metrics for this generation
    metrics_tracker.add_generation_metrics(population, fitness_values, generation)
    
    # Track constraint violations for the best individual
    best_idx = min(range(len(fitness_values)), key=lambda i, fvals=fitness_values: fvals[i][0])
    best_solution = population[best_idx]
    hard_violations = evaluate_hard_constraints(best_solution, activities_dict, groups_dict, spaces_dict)
    
    # Convert hard_violations tuple to a dictionary for plotting
    violation_dict = {
        "room_capacity": hard_violations[0],
        "room_availability": hard_violations[1],
        "lecturer_availability": hard_violations[2],
        "group_availability": hard_violations[3],
        "consecutive_sessions": hard_violations[4]
    }
    
    metrics_tracker.add_constraint_violations(violation_dict, 0)
    
    # Create and evaluate offspring
    offspring = create_offspring(population)
    offspring_fitness = evaluate_population(offspring)
    
    # Select next generation
    combined_population = population + offspring
    combined_fitness = fitness_values + offspring_fitness
    population = selection(combined_population, combined_fitness)
    
    # Apply local search periodically
    population = apply_periodic_local_search(population, generation)
    
    # Track execution time for this generation
    generation_time = time.time() - generation_start_time
    metrics_tracker.add_execution_time(generation_time)
    
    return population


def apply_periodic_local_search(population, generation):
    """
    Apply local search periodically to improve solutions.
    
    Args:
        population: Current population
        generation: Current generation number
        
    Returns:
        Updated population
    """
    if generation % 20 == 0:
        improved_solutions = apply_local_search(population, evaluate_population(population))
        
        # Replace some random individuals with improved ones
        if improved_solutions:
            for i, solution in enumerate(improved_solutions):
                idx = random.randint(0, len(population) - 1)
                population[idx] = solution
    
    return population


def generate_periodic_visualizations():
    """Generate periodic visualizations during optimization."""
    pass


def generate_final_results(best_solution, start_time):
    """
    Generate final results and visualizations.
    
    Args:
        best_solution: Best solution found
        start_time: Start time of optimization
    """
    # Print optimization statistics
    total_time = time.time() - start_time
    print(f"Optimization complete in {total_time:.2f} seconds.")
    print(f"Best solution found with {sum(evaluate_hard_constraints(best_solution, activities_dict, groups_dict, spaces_dict))} hard violations.")
    
    # Display final constraint violations breakdown
    if metrics_tracker.metrics['constraint_violations']:
        # The constraint_violations contains tuples of (hard_violations, soft_violations)
        hard_violations_dict, _ = metrics_tracker.metrics['constraint_violations'][-1]
        
        print("\nFinal constraint violations:")
        if isinstance(hard_violations_dict, dict):
            for violation_type, count in hard_violations_dict.items():
                print(f"  {violation_type.replace('_', ' ').title()}: {count}")
            total = sum(hard_violations_dict.values())
            print(f"  Total: {total}")
        else:
            # Handle case where hard_violations might be a tuple (from evaluate_hard_constraints)
            if isinstance(hard_violations_dict, tuple):
                violations = hard_violations_dict
                violation_types = ["Room Capacity", "Room Availability", "Lecturer Availability", 
                                  "Group Availability", "Consecutive Sessions"]
                
                for i, violation_type in enumerate(violation_types):
                    if i < len(violations):
                        print(f"  {violation_type}: {violations[i]}")
                
                total = sum(violations)
                print(f"  Total: {total}")
    
    print(f"\nAll performance metrics saved to '{OUTPUT_DIR}' directory.")
    
    # Generate HTML timetable
    try:
        html_file = generate_timetable_html(best_solution, output_file=f"{OUTPUT_DIR}/timetable.html")
        print(f"\nHTML timetable generated and saved to {html_file}")
        print("Open this file in a web browser to view the complete timetable.")
    except Exception as e:
        print(f"\nError generating HTML timetable: {e}")


def create_offspring(population):
    """
    Create offspring through crossover and mutation.
    
    Parameters:
        population (list): Current population
        
    Returns:
        list: Offspring population
    """
    offspring = []
    
    # Create offspring until we have enough
    while len(offspring) < POPULATION_SIZE:
        # Select parents through binary tournament
        parent1, parent2 = random.sample(population, 2), random.sample(population, 2)
        
        # Create children
        if random.random() < CROSSOVER_RATE:
            child1, child2 = crossover(parent1[0], parent2[0])
        else:
            child1, child2 = copy.deepcopy(parent1[0]), copy.deepcopy(parent2[0])
        
        # Apply mutation
        if random.random() < MUTATION_RATE:
            child1 = mutate(child1)
        if random.random() < MUTATION_RATE:
            child2 = mutate(child2)
        
        offspring.extend([child1, child2])
    
    # Trim to exact population size
    return offspring[:POPULATION_SIZE]


def apply_local_search(solutions, fitness_values):
    """
    Apply local search to improve the best solutions.
    
    Parameters:
        solutions (list): Solutions to improve
        fitness_values (list): Fitness values for the solutions
        
    Returns:
        list: Improved solutions
    """
    # Sort solutions by their fitness
    ranked_solutions = sorted(
        [(sol, fit) for sol, fit in zip(solutions, fitness_values)],
        key=lambda x: sum(x[1])
    )
    
    # Take the top 10% for local improvement
    top_solutions = [sol for sol, _ in ranked_solutions[:max(1, POPULATION_SIZE // 10)]]
    improved_solutions = []
    
    for solution in top_solutions:
        # Make a copy to work with
        improved = copy.deepcopy(solution)
        
        # Try small improvements for a number of iterations
        for _ in range(LOCAL_SEARCH_ITERATIONS):
            # Find activities involved in violations
            violations = find_violations(improved)
            
            if not violations:
                break  # No violations to fix
            
            # Take a random violation and try to fix it
            slot, room, activity = random.choice(violations)
            
            # Try to find a better slot
            better_slot_found = False
            for target_slot in random.sample(list(slots), min(len(slots), 10)):
                if target_slot != slot and check_activity_conflicts(activity, target_slot, improved):
                    suitable_rooms = find_suitable_rooms(activity, target_slot, improved)
                    
                    if suitable_rooms:
                        target_room = random.choice(suitable_rooms)
                        # Move the activity
                        improved[slot][room] = None
                        improved[target_slot][target_room] = activity
                        better_slot_found = True
                        break
            
            # If we couldn't find a better slot, try swapping with another activity
            if not better_slot_found:
                target_slot = random.choice(list(slots))
                if target_slot != slot:
                    rooms_in_target = [r for r in improved[target_slot] 
                                      if improved[target_slot][r] is not None]
                    
                    if rooms_in_target:
                        target_room = random.choice(rooms_in_target)
                        # Swap activities
                        improved[slot][room], improved[target_slot][target_room] = (
                            improved[target_slot][target_room], improved[slot][room]
                        )
        
        improved_solutions.append(improved)
    
    return improved_solutions


# When this module is run directly, execute the optimizer
if __name__ == "__main__":
    best_schedule, metrics_tracker = run_nsga2_optimizer()
    print("\nPerformance metrics:")
    metrics = metrics_tracker.get_metrics()
    
    # Print final metrics
    if metrics['hypervolume']:
        print(f"Final hypervolume: {metrics['hypervolume'][-1]:.4f}")
    if metrics['spacing']:
        print(f"Final spacing: {metrics['spacing'][-1]:.4f}")
    if metrics['igd']:
        print(f"Final IGD: {metrics['igd'][-1]:.4f}")
