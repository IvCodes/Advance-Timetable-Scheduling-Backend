import random
import numpy as np
from Data_Loading import Activity, spaces_dict, groups_dict, activities_dict, slots, lecturers_dict
from evaluate import evaluate_hard_constraints, evaluate_soft_constraints, evaluate_timetable

# NSGA-II Configuration Parameters
POPULATION_SIZE = 50
NUM_GENERATIONS = 100
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.8

# Global tracking variables
vacant_rooms = []


def evaluator(timetable):
    """
    Evaluate a timetable solution based on hard and soft constraints.
    
    Parameters:
        timetable (dict): The timetable solution to evaluate
        
    Returns:
        tuple: A tuple containing (hard_constraints_score, soft_constraints_score)
    """
    # Evaluate hard constraints
    hard_violations = evaluate_hard_constraints(timetable, activities_dict, groups_dict, spaces_dict)
    hard_score = sum(hard_violations)
    
    # Evaluate soft constraints
    _, soft_score = evaluate_soft_constraints(timetable, groups_dict, lecturers_dict, slots)
    
    # Return both scores as a tuple for multi-objective optimization
    return (hard_score, 1.0 - soft_score)


def get_classsize(activity: Activity) -> int:
    classsize = 0
    for id in activity.group_ids:
        classsize += groups_dict[id].size
    return classsize


def evaluate_population(population):
    """Evaluate each individual using the provided evaluator function."""
    fitness_values = []
    for timetable in population:
        fitness_values.append(evaluator(timetable))
    return fitness_values


def mutate(individual):
    """Perform mutation by randomly swapping activities in the timetable."""
    slots = list(individual.keys())
    slot1, slot2 = random.sample(slots, 2)
    room1, room2 = random.choice(
        list(individual[slot1])), random.choice(list(individual[slot2]))

    individual[slot1][room1], individual[slot2][room2] = individual[slot2][room2], individual[slot1][room1]


def crossover(parent1, parent2):
    """Perform crossover by swapping time slots between two parents."""
    child1, child2 = parent1.copy(), parent2.copy()
    slots = list(parent1.keys())
    split = random.randint(0, len(slots) - 1)

    for i in range(split, len(slots)):
        child1[slots[i]], child2[slots[i]
                                 ] = parent2[slots[i]], parent1[slots[i]]

    return child1, child2


def fast_nondominated_sort(fitness_values):
    """Perform non-dominated sorting based on the multi-objective fitness values."""
    fronts = [[]]
    S = [[] for _ in range(len(fitness_values))]
    n = [0] * len(fitness_values)
    rank = [0] * len(fitness_values)

    for p in range(len(fitness_values)):
        for q in range(len(fitness_values)):
            if dominates(fitness_values[p], fitness_values[q]):
                S[p].append(q)
            elif dominates(fitness_values[q], fitness_values[p]):
                n[p] += 1
        if n[p] == 0:
            rank[p] = 0
            fronts[0].append(p)

    i = 0
    while fronts[i]:
        next_front = []
        for p in fronts[i]:
            for q in S[p]:
                n[q] -= 1
                if n[q] == 0:
                    rank[q] = i + 1
                    next_front.append(q)
        i += 1
        fronts.append(next_front)

    return fronts[:-1]


def dominates(fitness1, fitness2):
    """Return True if fitness1 dominates fitness2."""
    return all(f1 <= f2 for f1, f2 in zip(fitness1, fitness2)) and any(f1 < f2 for f1, f2 in zip(fitness1, fitness2))


def calculate_crowding_distance(front, fitness_values):
    """Calculate crowding distance for a front."""
    distances = [0] * len(front)
    num_objectives = len(fitness_values[0])

    for m in range(num_objectives):
        front.sort(key=lambda x: fitness_values[x][m])
        distances[0] = distances[-1] = float('inf')

        min_value = fitness_values[front[0]][m]
        max_value = fitness_values[front[-1]][m]
        if max_value == min_value:
            continue

        for i in range(1, len(front) - 1):
            distances[i] += (fitness_values[front[i + 1]][m] -
                             fitness_values[front[i - 1]][m]) / (max_value - min_value)

    return distances


def _selection_process(population, new_population, fitness_values):
    """
    Helper function to handle the selection process in NSGA-II.
    
    Parameters:
        population (list): Current population
        new_population (list): New population after crossover and mutation
        fitness_values (list): Fitness values for the new population
        
    Returns:
        list: Selected population for next generation
    """
    # Combine parent and offspring populations
    combined_population = population + new_population
    combined_fitness = evaluate_population(combined_population)
    
    # Perform non-dominated sorting
    fronts = fast_nondominated_sort(combined_fitness)
    
    # Select individuals for next generation
    next_generation = []
    front_idx = 0
    
    # Add complete fronts until we reach the population size
    while len(next_generation) + len(fronts[front_idx]) <= POPULATION_SIZE:
        # Calculate crowding distance for current front
        calculate_crowding_distance(fronts[front_idx], combined_fitness)
        # Add all individuals from the current front
        next_generation.extend([combined_population[i] for i in fronts[front_idx]])
        front_idx += 1
        
        # If we've used all fronts, break
        if front_idx >= len(fronts):
            break
    
    # If we need more individuals, sort the next front by crowding distance
    if len(next_generation) < POPULATION_SIZE and front_idx < len(fronts):
        # Calculate crowding distance for the last front
        calculate_crowding_distance(fronts[front_idx], combined_fitness)
        # Sort the front by crowding distance (descending)
        sorted_front = sorted(fronts[front_idx], 
                              key=lambda i: combined_fitness[i][2] if len(combined_fitness[i]) > 2 else 0,
                              reverse=True)
        # Add individuals from the sorted front until we reach the population size
        remaining = POPULATION_SIZE - len(next_generation)
        next_generation.extend([combined_population[i] for i in sorted_front[:remaining]])
    
    return next_generation


def run_nsga2_optimizer():
    """
    Run the NSGA-II optimizer and return the best solution.
    
    Returns:
        dict: The best timetable solution found
    """
    print("Starting NSGA-II optimization...")
    
    # Generate initial population
    population = generate_initial_population()
    
    # Evolution over generations
    for generation in range(NUM_GENERATIONS):
        # Print progress periodically
        if generation % 10 == 0:
            print("Generation " + str(generation) + "/" + str(NUM_GENERATIONS) + "...")
        
        # Evaluate current population
        fitness_values = evaluate_population(population)
        
        # Create offspring through crossover and mutation
        offspring = _create_offspring(population)
        
        # Select next generation
        population = _selection_process(population, offspring, fitness_values)
    
    # Find the best solution in the final population
    best_solution = _find_best_solution(population)
    
    print("Optimization complete. Best solution found.")
    return best_solution


def _create_offspring(population):
    """
    Create offspring through crossover and mutation.
    
    Parameters:
        population (list): Current population
        
    Returns:
        list: Offspring population
    """
    offspring = []
    
    # Generate offspring until we have enough
    while len(offspring) < POPULATION_SIZE:
        # Select parents
        parent1, parent2 = random.sample(population, 2)
        
        # Apply crossover with probability CROSSOVER_RATE
        if random.random() < CROSSOVER_RATE:
            child1, child2 = crossover(parent1, parent2)
        else:
            child1, child2 = parent1.copy(), parent2.copy()
        
        # Apply mutation with probability MUTATION_RATE
        if random.random() < MUTATION_RATE:
            mutate(child1)
        if random.random() < MUTATION_RATE:
            mutate(child2)
        
        # Add children to offspring
        offspring.extend([child1, child2])
    
    # Trim offspring if needed
    if len(offspring) > POPULATION_SIZE:
        offspring = offspring[:POPULATION_SIZE]
    
    return offspring


def _find_best_solution(population):
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
        # Calculate total constraint violations
        violations = sum(evaluator(solution))
        
        # Update best solution if this one is better
        if violations < minimum_violations:
            minimum_violations = violations
            best_solution = solution
    
    print("Best solution has " + str(minimum_violations) + " total violations.")
    return best_solution


def nsga2():
    """
    Main NSGA-II algorithm loop.
    
    Returns:
        list: The final population of solutions after all generations
    """
    # Generate initial population
    population = generate_initial_population()
    
    # Evolution over generations
    for generation in range(NUM_GENERATIONS):
        # Evaluate current population
        fitness_values = evaluate_population(population)
        
        # Create offspring through crossover and mutation
        offspring = _create_offspring(population)
        
        # Select next generation
        population = _selection_process(population, offspring, fitness_values)
        
        # Optional: Print progress
        if generation % 10 == 0:
            print("Generation " + str(generation) + " completed")

    return population


def generate_initial_population():
    """
    Generate an initial population with random timetables.
    
    Returns:
        list: A list of timetable solutions (population)
    """
    population = []

    for _ in range(POPULATION_SIZE):
        timetable = {}
        activity_slots = {activity.id: [] for activity in activities_dict.values()}
        activities_remain = [activity.id for activity in activities_dict.values()
                            for _ in range(activity.duration)]
        
        # Initialize each slot with empty rooms
        for slot in slots:
            timetable[slot] = {}
            
            # Assign activities to rooms in each time slot
            for space_id in spaces_dict.keys():
                space = spaces_dict[space_id]
                
                # Find activities that fit in this room
                eligible_activities = [
                    activity for activity in activities_remain 
                    if get_classsize(activities_dict[activity]) <= space.size
                ]
                
                # Filter out activities already scheduled in this slot
                eligible_activities = [
                    activity for activity in eligible_activities 
                    if slot not in activity_slots[activity]
                ]
                
                # If there are eligible activities, select one randomly
                if eligible_activities:
                    activity = random.choice(eligible_activities)
                    timetable[slot][space_id] = activities_dict[activity]
                    activity_slots[activity].append(slot)
                    activities_remain.remove(activity)
                else:
                    # If no eligible activities, leave the room empty
                    timetable[slot][space_id] = None

        population.append(timetable)
    return population


# When this module is run directly, execute the optimizer
if __name__ == "__main__":
    best_schedule = run_nsga2_optimizer()
    
    # You can add code here to output or visualize the best schedule