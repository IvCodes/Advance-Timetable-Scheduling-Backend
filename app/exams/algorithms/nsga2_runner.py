"""
NSGA-II Runner for STA83 Exam Timetabling Problem
Provides a consistent interface for running NSGA-II optimization
"""
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from core.sta83_data_loader import STA83DataLoader
from core.sta83_problem_fixed import STA83Problem
from core.genetic_operators import STA83GeneticOperators

class NSGA2Runner:
    """Runner class for NSGA-II algorithm"""
    
    def __init__(self, data_loader: STA83DataLoader):
        self.data_loader = data_loader
        self.problem = STA83Problem(data_loader)
        
    def run_nsga2(self, pop_size=50, generations=100, seed=42):
        """Run NSGA-II optimization"""
        # Set random seed
        np.random.seed(seed)
        
        # Create NSGA-II algorithm
        algorithm = NSGA2(
            pop_size=pop_size,
            sampling=STA83GeneticOperators.get_sampling(),
            crossover=STA83GeneticOperators.get_crossover(),
            mutation=STA83GeneticOperators.get_mutation(),
            eliminate_duplicates=True
        )
        
        # Run optimization
        result = minimize(
            self.problem,
            algorithm,
            ('n_gen', generations),
            seed=seed,
            verbose=True
        )
        
        return result
    
    def run_multiple_seeds(self, num_runs=10, pop_size=50, generations=100, base_seed=42):
        """Run NSGA-II with multiple seeds for statistical analysis"""
        results = []
        
        print(f"Running NSGA-II with {num_runs} different seeds")
        print("=" * 50)
        
        for run_id in range(num_runs):
            seed = base_seed + run_id
            print(f"\nRun {run_id + 1}/{num_runs} (seed: {seed})")
            
            result = self.run_nsga2(pop_size, generations, seed)
            results.append({
                'run_id': run_id,
                'seed': seed,
                'result': result,
                'objectives': result.F,
                'solutions': result.X,
                'n_solutions': len(result.F) if result.F is not None else 0,
                'best_timeslots': np.min(result.F[:, 0]) if result.F is not None else np.inf,
                'best_penalty': np.min(result.F[:, 1]) if result.F is not None else np.inf
            })
            
            if result.F is not None:
                print(f"   Found {len(result.F)} solutions")
                print(f"   Best: {np.min(result.F[:, 0]):.0f} timeslots, {np.min(result.F[:, 1]):.2f} penalty")
            else:
                print(f"   No solutions found")
        
        return results

def test_nsga2():
    """Test NSGA-II implementation"""
    print("Testing NSGA-II Implementation")
    print("=" * 40)
    
    # Load data
    data_loader = STA83DataLoader()
    if not data_loader.load_data():
        print("Failed to load STA83 data")
        return
    
    # Create runner and test
    runner = NSGA2Runner(data_loader)
    
    # Run single optimization
    result = runner.run_nsga2(pop_size=30, generations=20, seed=42)
    
    if result.F is not None:
        print(f"\nNSGA-II test successful!")
        print(f"Found {len(result.F)} solutions")
        print(f"Best timeslots: {np.min(result.F[:, 0]):.0f}")
        print(f"Best penalty: {np.min(result.F[:, 1]):.2f}")
    else:
        print("NSGA-II test failed - no solutions found")
    
    return result

if __name__ == "__main__":
    test_nsga2() 