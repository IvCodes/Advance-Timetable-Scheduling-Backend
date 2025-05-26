#!/usr/bin/env python3
"""
Hybrid CP-MOEA Approach: Using CP solutions to seed evolutionary algorithms
"""
import sys
import os
import numpy as np
from typing import List, Dict
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.sta83_data_loader import STA83DataLoader
from core.sta83_problem_fixed import STA83Problem
from constraint_programming.cp_enhanced_solver import EnhancedSTA83CPSolver

try:
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.operators.sampling.rnd import PermutationRandomSampling
    from pymoo.operators.crossover.ox import OrderCrossover
    from pymoo.operators.mutation.inversion import InversionMutation
    from pymoo.optimize import minimize
    from pymoo.core.population import Population
    PYMOO_AVAILABLE = True
except ImportError:
    PYMOO_AVAILABLE = False
    print("WARNING: pymoo not available - hybrid approach will be limited")

class CPSeededSampling:
    """
    Custom sampling that uses CP solutions to seed the initial population
    """
    
    def __init__(self, cp_solutions: List[np.ndarray], fill_random: bool = True):
        """
        Initialize with CP solutions
        
        Args:
            cp_solutions: List of permutation arrays from CP solver
            fill_random: Whether to fill remaining population with random solutions
        """
        self.cp_solutions = cp_solutions
        self.fill_random = fill_random
        print(f"CP Seeding: {len(cp_solutions)} solutions available")
    
    def __call__(self, problem, n_samples, **kwargs):
        """
        Generate initial population with CP seeding
        
        Args:
            problem: The optimization problem
            n_samples: Number of samples to generate
            
        Returns:
            Population with CP-seeded solutions
        """
        X = np.zeros((n_samples, problem.n_var), dtype=int)
        
        # Use CP solutions first
        cp_count = min(len(self.cp_solutions), n_samples)
        for i in range(cp_count):
            X[i] = self.cp_solutions[i]
        
        # Fill remaining with random solutions if requested
        if self.fill_random and cp_count < n_samples:
            for i in range(cp_count, n_samples):
                X[i] = np.random.permutation(problem.n_var)
        
        # Create population
        if PYMOO_AVAILABLE:
            pop = Population.new("X", X)
            return pop
        else:
            return X

class HybridCPMOEA:
    """
    Hybrid approach combining CP-SAT and MOEAs
    """
    
    def __init__(self, data_loader: STA83DataLoader):
        """
        Initialize hybrid solver
        
        Args:
            data_loader: Loaded STA83 dataset
        """
        self.data_loader = data_loader
        self.cp_solver = EnhancedSTA83CPSolver(data_loader)
        self.problem = STA83Problem(data_loader)
        self.cp_solutions = []
        
    def generate_cp_seeds(self, num_seeds: int = 5, timeslots: int = 13) -> List[np.ndarray]:
        """
        Generate multiple CP solutions for seeding
        
        Args:
            num_seeds: Number of seed solutions to generate
            timeslots: Number of timeslots to use
            
        Returns:
            List of permutation arrays
        """
        print(f"\nGenerating {num_seeds} CP seed solutions...")
        
        solutions = self.cp_solver.create_multiple_solutions(timeslots, num_seeds)
        
        cp_permutations = []
        for i, solution in enumerate(solutions):
            if solution['feasible']:
                permutation = self.cp_solver.export_solution_for_moea(solution)
                cp_permutations.append(permutation)
                print(f"   Seed {i+1}: penalty {solution['proximity_penalty']:.2f}")
        
        self.cp_solutions = cp_permutations
        print(f"Generated {len(cp_permutations)} CP seed solutions")
        
        return cp_permutations
    
    def run_seeded_nsga2(self, pop_size: int = 20, generations: int = 50) -> Dict:
        """
        Run NSGA-II with CP-seeded initial population
        
        Args:
            pop_size: Population size
            generations: Number of generations
            
        Returns:
            Results dictionary
        """
        if not PYMOO_AVAILABLE:
            print("ERROR: pymoo not available - cannot run NSGA-II")
            return {'success': False, 'error': 'pymoo not available'}
        
        if not self.cp_solutions:
            print("WARNING: No CP solutions available - generating seeds first...")
            self.generate_cp_seeds()
        
        print(f"\nRunning CP-seeded NSGA-II...")
        print(f"   Population: {pop_size}, Generations: {generations}")
        print(f"   CP seeds: {len(self.cp_solutions)}")
        
        # Create seeded sampling
        seeded_sampling = CPSeededSampling(self.cp_solutions, fill_random=True)
        
        # Create NSGA-II algorithm with seeded population
        algorithm = NSGA2(
            pop_size=pop_size,
            sampling=seeded_sampling,
            crossover=OrderCrossover(prob=0.9),
            mutation=InversionMutation(prob=0.1),
            eliminate_duplicates=False
        )
        
        # Run optimization
        start_time = time.time()
        try:
            result = minimize(
                self.problem,
                algorithm,
                ('n_gen', generations),
                seed=42,
                verbose=False
            )
            solve_time = time.time() - start_time
            
            if result.F is not None and len(result.F) > 0:
                # Analyze results
                best_timeslots = np.min(result.F[:, 0])
                best_penalty = np.min(result.F[:, 1])
                
                # Find solutions with minimum timeslots
                min_timeslot_mask = result.F[:, 0] == best_timeslots
                min_timeslot_penalties = result.F[min_timeslot_mask, 1]
                best_penalty_at_min_timeslots = np.min(min_timeslot_penalties)
                
                return {
                    'success': True,
                    'solve_time': solve_time,
                    'num_solutions': len(result.F),
                    'best_timeslots': best_timeslots,
                    'best_penalty': best_penalty,
                    'best_penalty_at_min_timeslots': best_penalty_at_min_timeslots,
                    'pareto_front': result.F,
                    'solutions': result.X,
                    'cp_seeded': True
                }
            else:
                return {'success': False, 'error': 'No solutions found'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run_comparison_study(self) -> Dict:
        """
        Run comprehensive comparison between CP, standard MOEA, and hybrid approach
        
        Returns:
            Comparison results
        """
        print("\nRunning Hybrid CP-MOEA Comparison Study")
        print("=" * 50)
        
        results = {
            'cp_only': {},
            'standard_nsga2': {},
            'hybrid_nsga2': {}
        }
        
        # 1. CP-only approach
        print("\n1. CP-Only Approach")
        print("-" * 25)
        start_time = time.time()
        cp_result = self.cp_solver.solve_penalty_optimization(fixed_timeslots=13, time_limit_seconds=300)
        cp_time = time.time() - start_time
        
        if cp_result['feasible']:
            results['cp_only'] = {
                'success': True,
                'solve_time': cp_time,
                'timeslots': cp_result['timeslots_used'],
                'penalty': cp_result['proximity_penalty'],
                'optimal': cp_result['optimal']
            }
            print(f"   CP Solution: {cp_result['timeslots_used']} timeslots, penalty {cp_result['proximity_penalty']:.2f}")
        else:
            results['cp_only'] = {'success': False}
            print("   CP failed to find solution")
        
        # 2. Standard NSGA-II
        print("\n2. Standard NSGA-II")
        print("-" * 20)
        if PYMOO_AVAILABLE:
            algorithm = NSGA2(
                pop_size=20,
                crossover=OrderCrossover(prob=0.9),
                mutation=InversionMutation(prob=0.1),
                eliminate_duplicates=False
            )
            
            start_time = time.time()
            try:
                result = minimize(
                    self.problem,
                    algorithm,
                    ('n_gen', 50),
                    seed=42,
                    verbose=False
                )
                nsga2_time = time.time() - start_time
                
                if result.F is not None and len(result.F) > 0:
                    best_timeslots = np.min(result.F[:, 0])
                    best_penalty = np.min(result.F[:, 1])
                    
                    results['standard_nsga2'] = {
                        'success': True,
                        'solve_time': nsga2_time,
                        'num_solutions': len(result.F),
                        'best_timeslots': best_timeslots,
                        'best_penalty': best_penalty,
                        'pareto_front': result.F
                    }
                    print(f"   NSGA-II: {len(result.F)} solutions, best {best_timeslots} timeslots, penalty {best_penalty:.2f}")
                else:
                    results['standard_nsga2'] = {'success': False}
                    print("   NSGA-II failed")
            except Exception as e:
                results['standard_nsga2'] = {'success': False, 'error': str(e)}
                print(f"   NSGA-II error: {e}")
        else:
            results['standard_nsga2'] = {'success': False, 'error': 'pymoo not available'}
        
        # 3. Hybrid CP-seeded NSGA-II
        print("\n3. Hybrid CP-Seeded NSGA-II")
        print("-" * 30)
        
        # Generate CP seeds
        self.generate_cp_seeds(num_seeds=3, timeslots=13)
        
        # Run seeded NSGA-II
        hybrid_result = self.run_seeded_nsga2(pop_size=20, generations=50)
        results['hybrid_nsga2'] = hybrid_result
        
        if hybrid_result['success']:
            print(f"   Hybrid: {hybrid_result['num_solutions']} solutions, best {hybrid_result['best_timeslots']} timeslots, penalty {hybrid_result['best_penalty']:.2f}")
        else:
            print(f"   Hybrid failed: {hybrid_result.get('error', 'Unknown error')}")
        
        # Summary comparison
        print("\n" + "=" * 50)
        print("COMPARISON SUMMARY")
        print("=" * 50)
        
        for approach, result in results.items():
            if result.get('success', False):
                if approach == 'cp_only':
                    print(f"{approach:20}: {result['timeslots']} timeslots, penalty {result['penalty']:.2f}, time {result['solve_time']:.1f}s")
                else:
                    print(f"{approach:20}: {result['best_timeslots']} timeslots, penalty {result['best_penalty']:.2f}, time {result['solve_time']:.1f}s")
            else:
                print(f"{approach:20}: FAILED")
        
        return results

def test_hybrid_approach():
    """Test the hybrid CP-MOEA approach"""
    print("Testing Hybrid CP-MOEA Approach")
    print("=" * 40)
    
    # Load data
    data_loader = STA83DataLoader()
    if not data_loader.load_data():
        print("Failed to load data")
        return
    
    print(f"Loaded {data_loader.num_exams} exams, {data_loader.num_students} students")
    
    # Create hybrid solver
    hybrid = HybridCPMOEA(data_loader)
    
    # Run comparison study
    results = hybrid.run_comparison_study()
    
    print("\nTest completed!")
    return results

if __name__ == "__main__":
    test_hybrid_approach() 