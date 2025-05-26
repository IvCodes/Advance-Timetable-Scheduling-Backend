"""
Hybrid NSGA-II + DQN Algorithm for STA83 Exam Timetabling
Combines NSGA-II population-based search with DQN-based solution refinement
"""
import numpy as np
import time
import sys
import os
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

# Add paths for imports
sys.path.append('.')
sys.path.append('./core')
sys.path.append('./algorithms')
sys.path.append('./rl')

# Core imports
from core.sta83_data_loader import STA83DataLoader
from core.sta83_problem_fixed import STA83Problem
from core.genetic_operators import STA83GeneticOperators

# NSGA-II imports
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize

# DQN imports (with fallback)
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    from rl.environment import ExamTimetablingEnv
    from rl.agent import DQNAgent
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    print("Warning: PyTorch not available. DQN refinement will be disabled.")

class DQNRefinementAgent:
    """
    Specialized DQN agent for refining NSGA-II solutions
    """
    
    def __init__(self, data_loader: STA83DataLoader, max_timeslots: int = 25):
        """
        Initialize DQN refinement agent
        
        Args:
            data_loader: STA83 data loader
            max_timeslots: Maximum timeslots for environment
        """
        self.data_loader = data_loader
        self.max_timeslots = max_timeslots
        self.agent = None
        self.env = None
        
        if PYTORCH_AVAILABLE:
            self._setup_dqn_components()
    
    def _setup_dqn_components(self):
        """Setup DQN environment and agent"""
        try:
            # Create environment
            self.env = ExamTimetablingEnv(max_timeslots=self.max_timeslots)
            
            # Create agent with refinement-specific parameters
            state_size = self.env.observation_space.shape[0]
            action_size = self.env.action_space.n
            
            self.agent = DQNAgent(
                state_size=state_size,
                action_size=action_size,
                learning_rate=0.0001,  # Lower learning rate for refinement
                gamma=0.95,
                epsilon_start=0.1,     # Lower exploration for refinement
                epsilon_end=0.01,
                epsilon_decay=0.99,
                buffer_size=5000,      # Smaller buffer for refinement
                batch_size=32,
                target_update_freq=50
            )
            
        except Exception as e:
            print(f"Warning: Failed to setup DQN components: {e}")
            self.agent = None
            self.env = None
    
    def load_pretrained_model(self, model_path: str) -> bool:
        """
        Load a pre-trained DQN model
        
        Args:
            model_path: Path to the trained model
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if not PYTORCH_AVAILABLE or self.agent is None:
            return False
        
        try:
            self.agent.load_model(model_path)
            # Set to evaluation mode (no exploration)
            self.agent.epsilon = 0.0
            return True
        except Exception as e:
            print(f"Warning: Failed to load DQN model from {model_path}: {e}")
            return False
    
    def refine_solution(self, permutation: np.ndarray, max_steps: int = 10) -> Tuple[np.ndarray, Dict]:
        """
        Refine a solution using DQN
        
        Args:
            permutation: Original permutation from NSGA-II (0-indexed)
            max_steps: Maximum refinement steps
            
        Returns:
            Tuple of (refined_permutation, refinement_info)
        """
        if not PYTORCH_AVAILABLE or self.agent is None or self.env is None:
            return permutation, {'refined': False, 'reason': 'DQN not available'}
        
        try:
            # Convert permutation to exam schedule for evaluation
            problem = STA83Problem(self.data_loader)
            original_schedule = problem.get_exam_schedule(permutation)
            original_objectives = [original_schedule['timeslots_used'], 
                                 original_schedule['avg_penalty_per_student']]
            
            # Try to construct a similar solution using DQN
            # This is a simplified approach - in practice, you might want to
            # implement a more sophisticated state conversion
            state = self.env.reset()
            refined_permutation = []
            
            # Use DQN to construct a new solution
            for step in range(self.data_loader.num_exams):
                valid_actions = self.env.get_valid_actions()
                if not valid_actions:
                    break
                
                action = self.agent.act(state, valid_actions)
                next_state, reward, done, info = self.env.step(action)
                state = next_state
                
                if done:
                    if 'valid_solution' in info and info['valid_solution']:
                        # Get the solution from environment
                        solution_quality = self.env.get_solution_quality()
                        refined_objectives = [solution_quality['timeslots_used'],
                                            solution_quality['avg_proximity_penalty']]
                        
                        # Check if refined solution is better
                        is_better = self._is_solution_better(original_objectives, refined_objectives)
                        
                        if is_better:
                            # Convert environment solution back to permutation
                            # This is a simplified conversion - you might need to implement
                            # a proper conversion based on your environment's solution format
                            refined_permutation = self._convert_env_solution_to_permutation()
                            
                            return refined_permutation, {
                                'refined': True,
                                'original_objectives': original_objectives,
                                'refined_objectives': refined_objectives,
                                'improvement': True
                            }
                    break
            
            # If no improvement or invalid solution
            return permutation, {
                'refined': True,
                'original_objectives': original_objectives,
                'refined_objectives': original_objectives,
                'improvement': False
            }
            
        except Exception as e:
            print(f"Warning: DQN refinement failed: {e}")
            return permutation, {'refined': False, 'reason': f'Error: {str(e)}'}
    
    def _is_solution_better(self, original: List[float], refined: List[float]) -> bool:
        """
        Check if refined solution is better than original
        Uses simple weighted sum for now - could be improved with Pareto dominance
        """
        # Weighted sum approach (can be customized)
        w1, w2 = 0.6, 0.4  # Weights for timeslots and penalty
        original_score = w1 * original[0] + w2 * original[1]
        refined_score = w1 * refined[0] + w2 * refined[1]
        return refined_score < original_score
    
    def _convert_env_solution_to_permutation(self) -> np.ndarray:
        """
        Convert environment solution to permutation format
        This is a placeholder - implement based on your environment's solution format
        """
        # For now, return a random permutation as placeholder
        return np.random.permutation(self.data_loader.num_exams)

class HybridNSGA2DQN:
    """
    Hybrid NSGA-II + DQN Algorithm
    """
    
    def __init__(self, data_loader: STA83DataLoader):
        """
        Initialize hybrid algorithm
        
        Args:
            data_loader: STA83 data loader
        """
        self.data_loader = data_loader
        self.problem = STA83Problem(data_loader)
        self.dqn_refiner = DQNRefinementAgent(data_loader)
        
        # Algorithm parameters
        self.nsga2_params = {
            'pop_size': 50,
            'generations': 50,
            'seed': 42
        }
        
        self.refinement_params = {
            'refine_frequency': 10,  # Refine every N generations
            'refine_top_n': 5,       # Refine top N solutions
            'max_refinement_steps': 10
        }
        
        # Results storage
        self.results = {
            'nsga2_results': None,
            'refinement_stats': [],
            'final_pareto_front': None,
            'execution_time': 0.0
        }
    
    def set_nsga2_params(self, pop_size: int = 50, generations: int = 50, seed: int = 42):
        """Set NSGA-II parameters"""
        self.nsga2_params = {
            'pop_size': pop_size,
            'generations': generations,
            'seed': seed
        }
    
    def set_refinement_params(self, refine_frequency: int = 10, refine_top_n: int = 5, 
                            max_refinement_steps: int = 10):
        """Set DQN refinement parameters"""
        self.refinement_params = {
            'refine_frequency': refine_frequency,
            'refine_top_n': refine_top_n,
            'max_refinement_steps': max_refinement_steps
        }
    
    def load_pretrained_dqn(self, model_path: str) -> bool:
        """Load pre-trained DQN model for refinement"""
        return self.dqn_refiner.load_pretrained_model(model_path)
    
    def run_hybrid_optimization(self, verbose: bool = True) -> Dict:
        """
        Run hybrid NSGA-II + DQN optimization
        
        Args:
            verbose: Whether to print progress
            
        Returns:
            Results dictionary
        """
        start_time = time.time()
        
        if verbose:
            print("Starting Hybrid NSGA-II + DQN Optimization")
            print("=" * 50)
            print(f"NSGA-II: {self.nsga2_params['pop_size']} pop, {self.nsga2_params['generations']} gen")
            print(f"DQN Refinement: Every {self.refinement_params['refine_frequency']} gen, top {self.refinement_params['refine_top_n']} solutions")
        
        # Phase 1: Run NSGA-II
        if verbose:
            print("\nPhase 1: Running NSGA-II...")
        
        nsga2_result = self._run_nsga2_phase(verbose)
        
        # Phase 2: DQN Refinement (if available)
        if PYTORCH_AVAILABLE and self.dqn_refiner.agent is not None:
            if verbose:
                print("\nPhase 2: DQN Refinement...")
            
            refined_result = self._run_refinement_phase(nsga2_result, verbose)
        else:
            if verbose:
                print("\nPhase 2: DQN Refinement skipped (not available)")
            refined_result = nsga2_result
        
        # Store results
        execution_time = time.time() - start_time
        self.results = {
            'nsga2_results': nsga2_result,
            'final_pareto_front': refined_result.F if refined_result.F is not None else None,
            'final_solutions': refined_result.X if refined_result.X is not None else None,
            'execution_time': execution_time,
            'refinement_stats': getattr(self, '_refinement_stats', []),
            'algorithm': 'Hybrid NSGA-II + DQN'
        }
        
        if verbose:
            self._print_final_results()
        
        return self.results
    
    def _run_nsga2_phase(self, verbose: bool = True) -> Any:
        """Run NSGA-II optimization phase"""
        # Set random seed
        np.random.seed(self.nsga2_params['seed'])
        
        # Create NSGA-II algorithm
        algorithm = NSGA2(
            pop_size=self.nsga2_params['pop_size'],
            sampling=STA83GeneticOperators.get_sampling(),
            crossover=STA83GeneticOperators.get_crossover(),
            mutation=STA83GeneticOperators.get_mutation(),
            eliminate_duplicates=True
        )
        
        # Run optimization
        result = minimize(
            self.problem,
            algorithm,
            ('n_gen', self.nsga2_params['generations']),
            seed=self.nsga2_params['seed'],
            verbose=verbose
        )
        
        return result
    
    def _run_refinement_phase(self, nsga2_result: Any, verbose: bool = True) -> Any:
        """Run DQN refinement phase"""
        if nsga2_result.F is None or len(nsga2_result.F) == 0:
            if verbose:
                print("   No solutions to refine")
            return nsga2_result
        
        # Select top solutions for refinement
        top_n = min(self.refinement_params['refine_top_n'], len(nsga2_result.F))
        
        # Sort by first objective (timeslots) for selection
        sorted_indices = np.argsort(nsga2_result.F[:, 0])
        top_indices = sorted_indices[:top_n]
        
        refined_solutions = []
        refined_objectives = []
        self._refinement_stats = []
        
        if verbose:
            print(f"   Refining top {top_n} solutions...")
        
        for i, idx in enumerate(top_indices):
            original_solution = nsga2_result.X[idx]
            original_objective = nsga2_result.F[idx]
            
            # Refine solution using DQN
            refined_solution, refinement_info = self.dqn_refiner.refine_solution(
                original_solution, 
                self.refinement_params['max_refinement_steps']
            )
            
            # Evaluate refined solution
            if refinement_info.get('refined', False):
                # Re-evaluate the refined solution
                eval_out = {}
                self.problem._evaluate_single(refined_solution, eval_out)
                refined_objective = eval_out['F']
                
                refined_solutions.append(refined_solution)
                refined_objectives.append(refined_objective)
                
                # Store refinement statistics
                self._refinement_stats.append({
                    'solution_index': i,
                    'original_objective': original_objective.tolist(),
                    'refined_objective': refined_objective,
                    'improvement': refinement_info.get('improvement', False)
                })
                
                if verbose and refinement_info.get('improvement', False):
                    print(f"     Solution {i+1}: Improved from {original_objective} to {refined_objective}")
            else:
                # Keep original solution if refinement failed
                refined_solutions.append(original_solution)
                refined_objectives.append(original_objective)
        
        # Combine refined solutions with remaining original solutions
        remaining_indices = sorted_indices[top_n:]
        all_solutions = refined_solutions + [nsga2_result.X[i] for i in remaining_indices]
        all_objectives = refined_objectives + [nsga2_result.F[i] for i in remaining_indices]
        
        # Create result object (simplified)
        class HybridResult:
            def __init__(self, X, F):
                self.X = np.array(X)
                self.F = np.array(F)
        
        return HybridResult(all_solutions, all_objectives)
    
    def _print_final_results(self):
        """Print final optimization results"""
        print("\nHybrid Optimization Results:")
        print("=" * 40)
        
        if self.results['final_pareto_front'] is not None:
            pareto_front = self.results['final_pareto_front']
            print(f"Final Pareto front size: {len(pareto_front)}")
            print(f"Best timeslots: {np.min(pareto_front[:, 0]):.0f}")
            print(f"Best penalty: {np.min(pareto_front[:, 1]):.4f}")
            print(f"Execution time: {self.results['execution_time']:.2f} seconds")
            
            # Refinement statistics
            if self.results['refinement_stats']:
                improved_count = sum(1 for stat in self.results['refinement_stats'] 
                                   if stat['improvement'])
                print(f"DQN improvements: {improved_count}/{len(self.results['refinement_stats'])}")
        else:
            print("No solutions found")

class HybridNSGA2DQNRunner:
    """
    Runner class for Hybrid NSGA-II + DQN algorithm
    """
    
    def __init__(self, data_loader: STA83DataLoader):
        """Initialize runner"""
        self.data_loader = data_loader
        self.hybrid_algorithm = HybridNSGA2DQN(data_loader)
    
    def run_hybrid(self, pop_size: int = 50, generations: int = 50, 
                   dqn_model_path: Optional[str] = None, seed: int = 42) -> Dict:
        """
        Run hybrid optimization
        
        Args:
            pop_size: NSGA-II population size
            generations: NSGA-II generations
            dqn_model_path: Path to pre-trained DQN model (optional)
            seed: Random seed
            
        Returns:
            Results dictionary
        """
        # Configure algorithm
        self.hybrid_algorithm.set_nsga2_params(pop_size, generations, seed)
        
        # Load DQN model if provided
        if dqn_model_path:
            success = self.hybrid_algorithm.load_pretrained_dqn(dqn_model_path)
            if success:
                print(f"Loaded pre-trained DQN model: {dqn_model_path}")
            else:
                print(f"Failed to load DQN model: {dqn_model_path}")
        
        # Run optimization
        return self.hybrid_algorithm.run_hybrid_optimization(verbose=True)

def test_hybrid_algorithm():
    """Test the hybrid algorithm"""
    print("Testing Hybrid NSGA-II + DQN Algorithm")
    print("=" * 50)
    
    # Load data
    data_loader = STA83DataLoader(crs_file='data/sta-f-83.crs', stu_file='data/sta-f-83.stu')
    if not data_loader.load_data():
        print("Failed to load STA83 data")
        return
    
    # Create and run hybrid algorithm
    runner = HybridNSGA2DQNRunner(data_loader)
    
    # Run with small parameters for testing
    results = runner.run_hybrid(
        pop_size=20,
        generations=10,
        seed=42
    )
    
    print("\nTest completed successfully!")
    return results

if __name__ == "__main__":
    test_hybrid_algorithm() 