"""
Metrics Tracker module for optimization algorithms.
Tracks various performance metrics during the optimization process.
"""

import numpy as np
from metrics import calculate_hypervolume, calculate_spacing, calculate_igd, extract_pareto_front

class MetricsTracker:
    """
    Tracks metrics during optimization algorithm runs.
    """
    def __init__(self):
        """Initialize the metrics tracker with empty collections."""
        self.metrics = {
            # Fitness metrics
            'best_hard_violations': [],
            'best_soft_score': [],
            'average_hard_violations': [],
            'average_soft_score': [],
            
            # Constraint violations per generation
            'constraint_violations': [],
            
            # Pareto metrics
            'pareto_front_size': [],
            'hypervolume': [],
            'spacing': [],
            'igd': [],
            
            # Additional metrics
            'execution_time': [],
            'solution_diversity': []
        }
        
        # Reference front for IGD calculation
        self.best_front = []
        
        # Reference point for hypervolume calculation - will be updated dynamically
        self.reference_point = None
    
    def add_generation_metrics(self, population, fitness_values, generation):
        """
        Add metrics for the current generation.
        
        Args:
            population: List of solutions
            fitness_values: List of fitness values corresponding to solutions
            generation: Current generation number
        """
        # Track only if population exists
        if not population or not fitness_values:
            return
        
        # Extract hard constraint violations and soft scores
        hard_violations = [fit[0] for fit in fitness_values]
        soft_scores = [fit[1] for fit in fitness_values]
        
        # Calculate best and average metrics
        best_hard = min(hard_violations)
        average_hard = sum(hard_violations) / len(hard_violations)
        best_soft = min(soft_scores)
        average_soft = sum(soft_scores) / len(soft_scores)
        
        # Store best and average values
        self.metrics['best_hard_violations'].append(best_hard)
        self.metrics['best_soft_score'].append(best_soft)
        self.metrics['average_hard_violations'].append(average_hard)
        self.metrics['average_soft_score'].append(average_soft)
        
        # Extract Pareto front
        try:
            pareto_indices = extract_pareto_front(fitness_values)
            pareto_front = [fitness_values[i] for i in pareto_indices]
            front_size = len(pareto_front)
            
            # Update reference front for IGD calculation (keep best solutions found so far)
            if not self.best_front:
                self.best_front = pareto_front
            else:
                # Combine current front with best front
                combined_front = self.best_front + pareto_front
                # Extract new Pareto front from combined front
                combined_indices = extract_pareto_front(combined_front)
                self.best_front = [combined_front[i] for i in combined_indices]
            
            # Calculate and store metrics
            self.metrics['pareto_front_size'].append(front_size)
            
            # Calculate hypervolume
            if front_size > 0:
                try:
                    # Dynamically determine reference point based on worst values in the current front
                    if self.reference_point is None or generation % 10 == 0:  # Update every 10 generations
                        # Add a margin to the worst values to ensure reference point is worse than all solutions
                        worst_hard = max(hard_violations) * 1.2  # 20% margin
                        worst_soft = max(soft_scores) * 1.2  # 20% margin
                        self.reference_point = [worst_hard, worst_soft]
                        print(f"Updated reference point to: {self.reference_point}")
                    
                    hypervolume = calculate_hypervolume(pareto_front, self.reference_point)
                    self.metrics['hypervolume'].append(hypervolume)
                except Exception as e:
                    print(f"Error calculating hypervolume: {e}")
                    print(f"Pareto front: {pareto_front}")
                    print(f"Reference point: {self.reference_point}")
                    self.metrics['hypervolume'].append(0.0)
                
                # Calculate spacing
                try:
                    spacing = calculate_spacing(pareto_front)
                    self.metrics['spacing'].append(spacing)
                except Exception as e:
                    print(f"Error calculating spacing: {e}")
                    self.metrics['spacing'].append(0.0)
                
                # Calculate IGD
                try:
                    if self.best_front:
                        igd = calculate_igd(pareto_front, self.best_front)
                        self.metrics['igd'].append(igd)
                except Exception as e:
                    print(f"Error calculating IGD: {e}")
                    self.metrics['igd'].append(0.0)
            else:
                # No Pareto front
                self.metrics['hypervolume'].append(0.0)
                self.metrics['spacing'].append(0.0)
                self.metrics['igd'].append(0.0)
                
        except Exception as e:
            print(f"Error extracting Pareto front: {e}")
            # Default values if front extraction fails
            self.metrics['pareto_front_size'].append(0)
            self.metrics['hypervolume'].append(0.0)
            self.metrics['spacing'].append(0.0)
            self.metrics['igd'].append(0.0)
    
    def add_execution_time(self, execution_time):
        """
        Add execution time to the metrics.
        
        Args:
            execution_time: Execution time in seconds
        """
        self.metrics['execution_time'] = execution_time
    
    def set_final_metrics(self, hard_violations=None, soft_score=None, execution_time=None):
        """
        Set final metrics for the optimization process.
        
        Args:
            hard_violations: Number of hard constraint violations in the best solution
            soft_score: Soft constraint score in the best solution
            execution_time: Total execution time
        """
        if hard_violations is not None:
            self.metrics['hard_violations'] = hard_violations
        
        if soft_score is not None:
            self.metrics['soft_score'] = soft_score
            
        if execution_time is not None:
            self.metrics['execution_time'] = execution_time
            
    def add_constraint_violations(self, hard_violations, soft_violations):
        """
        Add detailed constraint violations for the current generation.
        
        Args:
            hard_violations: Number of hard constraint violations
            soft_violations: Number of soft constraint violations
        """
        self.metrics['constraint_violations'].append((hard_violations, soft_violations))
    
    def add_diversity_metric(self, diversity):
        """Add solution diversity metric for the current generation."""
        self.metrics['solution_diversity'].append(diversity)
    
    def get_metrics(self):
        """Return all tracked metrics."""
        return self.metrics
    
    def get_fitness_history(self):
        """Return fitness metrics history."""
        return {
            'best_hard_violations': self.metrics['best_hard_violations'],
            'best_soft_score': self.metrics['best_soft_score'],
            'average_hard_violations': self.metrics['average_hard_violations'],
            'average_soft_score': self.metrics['average_soft_score']
        }
    
    def get_pareto_metrics(self):
        """Return Pareto metrics history."""
        return {
            'pareto_front_size': self.metrics['pareto_front_size'],
            'hypervolume': self.metrics['hypervolume'],
            'spacing': self.metrics['spacing'],
            'igd': self.metrics['igd']
        }
