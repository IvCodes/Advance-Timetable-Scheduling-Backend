"""
Hybrid NSGA-II + SARSA Algorithm for STA83 Exam Timetabling
Combines NSGA-II population-based search with SARSA-based solution refinement
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

# SARSA imports (with fallback)
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    from rl.sarsa_environment import ExamTimetablingSARSAEnv
    from rl.sarsa_agent import SARSAAgent
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    print("Warning: PyTorch not available. SARSA refinement will be disabled.")

class SARSARefinementAgent:
    """
    Specialized SARSA agent for refining NSGA-II solutions
    """
    
    def __init__(self, data_loader: STA83DataLoader, max_timeslots: int = 25):
        """
        Initialize SARSA refinement agent
        
        Args:
            data_loader: STA83 data loader
            max_timeslots: Maximum timeslots for environment
        """
        self.data_loader = data_loader
        self.max_timeslots = max_timeslots
        self.agent = None
        self.env = None
        
        if PYTORCH_AVAILABLE:
            self._setup_sarsa_components()
    
    def _setup_sarsa_components(self):
        """Setup SARSA environment and agent"""
        try:
            # Create environment
            self.env = ExamTimetablingSARSAEnv(max_timeslots=self.max_timeslots)
            
            # Create agent with refinement-specific parameters
            state_size = self.env.observation_space.shape[0]
            action_size = self.env.action_space.n
            
            self.agent = SARSAAgent(
                state_size=state_size,
                action_size=action_size,
                learning_rate=0.0001,  # Lower learning rate for refinement
                gamma=0.95,
                epsilon_start=0.05,    # Very low exploration for refinement
                epsilon_end=0.01,
                epsilon_decay=0.99
            )
            
        except Exception as e:
            print(f"Warning: Failed to setup SARSA components: {e}")
            self.agent = None
            self.env = None
    
    def load_pretrained_model(self, model_path: str) -> bool:
        """
        Load a pre-trained SARSA model
        
        Args:
            model_path: Path to the trained model
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if not PYTORCH_AVAILABLE or self.agent is None:
            return False
        
        try:
            # Fix PyTorch loading issue
            import torch
            checkpoint = torch.load(model_path, map_location=self.agent.device, weights_only=False)
            self.agent.q_network.load_state_dict(checkpoint['q_network_state_dict'])
            self.agent.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.agent.epsilon = 0.01  # Set to evaluation mode (minimal exploration)
            print(f"✅ Successfully loaded SARSA model: {model_path}")
            return True
        except Exception as e:
            print(f"Warning: Failed to load SARSA model from {model_path}: {e}")
            return False
    
    def refine_solution(self, permutation: np.ndarray, max_refinements: int = 5) -> Tuple[np.ndarray, Dict]:
        """
        Refine a solution using SARSA-based local search
        
        Args:
            permutation: Original permutation from NSGA-II (0-indexed)
            max_refinements: Maximum number of refinement attempts
            
        Returns:
            Tuple of (refined_permutation, refinement_info)
        """
        if not PYTORCH_AVAILABLE or self.agent is None or self.env is None:
            return permutation, {'refined': False, 'reason': 'SARSA not available'}
        
        try:
            # Convert permutation to exam schedule for evaluation
            problem = STA83Problem(self.data_loader)
            original_schedule = problem.get_exam_schedule(permutation)
            original_objectives = [original_schedule['timeslots_used'], 
                                 original_schedule['avg_penalty_per_student']]
            
            # Convert NSGA-II solution to timetable format
            original_timetable = self._permutation_to_timetable(permutation)
            best_timetable = original_timetable.copy()
            best_objectives = original_objectives.copy()
            improvements_made = 0
            
            # Perform multiple refinement attempts
            for refinement in range(max_refinements):
                refined_timetable, improvement_info = self._refine_timetable_with_sarsa(
                    best_timetable, max_moves=3
                )
                
                if improvement_info['improved']:
                    # Evaluate refined solution
                    refined_permutation = self._timetable_to_permutation(refined_timetable)
                    refined_schedule = problem.get_exam_schedule(refined_permutation)
                    refined_objectives = [refined_schedule['timeslots_used'],
                                        refined_schedule['avg_penalty_per_student']]
                    
                    # Check if it's actually better
                    if self._is_solution_better(best_objectives, refined_objectives):
                        best_timetable = refined_timetable
                        best_objectives = refined_objectives
                        improvements_made += 1
            
            # Convert back to permutation
            if improvements_made > 0:
                final_permutation = self._timetable_to_permutation(best_timetable)
                return final_permutation, {
                    'refined': True,
                    'original_objectives': original_objectives,
                    'refined_objectives': best_objectives,
                    'improvement': True,
                    'improvements_made': improvements_made
                }
            else:
                return permutation, {
                    'refined': True,
                    'original_objectives': original_objectives,
                    'refined_objectives': original_objectives,
                    'improvement': False,
                    'improvements_made': 0
                }
            
        except Exception as e:
            print(f"Warning: SARSA refinement failed: {e}")
            return permutation, {'refined': False, 'reason': f'Error: {str(e)}'}
    
    def _refine_timetable_with_sarsa(self, timetable: np.ndarray, max_moves: int = 3) -> Tuple[np.ndarray, Dict]:
        """
        Use SARSA to refine a timetable by suggesting better exam placements
        
        Args:
            timetable: Current timetable (exam_idx -> timeslot)
            max_moves: Maximum number of moves to attempt
            
        Returns:
            Tuple of (refined_timetable, improvement_info)
        """
        refined_timetable = timetable.copy()
        moves_made = 0
        
        for move in range(max_moves):
            # Select a random exam to potentially move
            exam_to_move = np.random.randint(0, len(timetable))
            current_timeslot = timetable[exam_to_move]
            
            # Create SARSA state with this exam "unassigned"
            temp_timetable = refined_timetable.copy()
            temp_timetable[exam_to_move] = -1  # Mark as unassigned
            
            # Convert to SARSA environment state
            sarsa_state = self._create_sarsa_state(temp_timetable, exam_to_move)
            
            # Get valid actions (timeslots without conflicts)
            valid_actions = self._get_valid_actions_for_exam(temp_timetable, exam_to_move)
            
            if len(valid_actions) > 1:  # Only if there are alternatives
                # Get SARSA suggestion
                suggested_timeslot = self.agent.act(sarsa_state, valid_actions)
                
                # Apply move if different from current
                if suggested_timeslot != current_timeslot:
                    refined_timetable[exam_to_move] = suggested_timeslot
                    moves_made += 1
        
        return refined_timetable, {'improved': moves_made > 0, 'moves_made': moves_made}
    
    def _permutation_to_timetable(self, permutation: np.ndarray) -> np.ndarray:
        """Convert NSGA-II permutation to timetable format"""
        # This is a simplified conversion - you may need to adapt based on your exact format
        problem = STA83Problem(self.data_loader)
        schedule = problem.get_exam_schedule(permutation)
        
        # Create timetable array (exam_idx -> timeslot)
        timetable = np.full(self.data_loader.num_exams, -1, dtype=int)
        
        # Use slot_to_exams from the schedule
        for timeslot, exams in schedule['slot_to_exams'].items():
            for exam_id in exams:
                exam_idx = exam_id - 1  # Convert to 0-indexed
                if 0 <= exam_idx < self.data_loader.num_exams:
                    timetable[exam_idx] = timeslot
        
        return timetable
    
    def _timetable_to_permutation(self, timetable: np.ndarray) -> np.ndarray:
        """Convert timetable back to permutation format"""
        # Create a permutation that would result in this timetable
        # This is a simplified approach - you may need to adapt
        
        # Group exams by timeslot
        timeslot_groups = {}
        for exam_idx, timeslot in enumerate(timetable):
            if timeslot >= 0:
                if timeslot not in timeslot_groups:
                    timeslot_groups[timeslot] = []
                timeslot_groups[timeslot].append(exam_idx)
        
        # Create permutation by concatenating timeslot groups
        permutation = []
        for timeslot in sorted(timeslot_groups.keys()):
            permutation.extend(timeslot_groups[timeslot])
        
        # Add any unassigned exams at the end
        for exam_idx in range(len(timetable)):
            if exam_idx not in permutation:
                permutation.append(exam_idx)
        
        return np.array(permutation, dtype=int)
    
    def _create_sarsa_state(self, timetable: np.ndarray, current_exam_idx: int) -> np.ndarray:
        """Create SARSA environment state from timetable"""
        # Calculate timeslot usage
        timeslot_usage = np.zeros(self.max_timeslots, dtype=int)
        for exam_idx, timeslot in enumerate(timetable):
            if timeslot >= 0 and exam_idx != current_exam_idx:
                timeslot_usage[timeslot] += 1
        
        # Create state vector similar to SARSA environment
        state = []
        
        # Current exam index (normalized)
        state.append(current_exam_idx / self.data_loader.num_exams)
        
        # Timetable assignments (normalized)
        normalized_timetable = timetable.astype(float) / self.max_timeslots
        state.extend(normalized_timetable)
        
        # Timeslot usage (normalized)
        normalized_usage = timeslot_usage.astype(float) / self.data_loader.num_exams
        state.extend(normalized_usage)
        
        # Conflict indicators for current exam
        conflict_indicators = self._get_conflict_indicators(timetable, current_exam_idx)
        state.extend(conflict_indicators)
        
        return np.array(state, dtype=np.float32)
    
    def _get_valid_actions_for_exam(self, timetable: np.ndarray, exam_idx: int) -> List[int]:
        """Get valid timeslots for an exam (no conflicts)"""
        valid_actions = []
        
        for timeslot in range(self.max_timeslots):
            has_conflict = False
            
            # Check for conflicts with exams already in this timeslot
            for other_exam_idx, other_timeslot in enumerate(timetable):
                if other_timeslot == timeslot and other_exam_idx != exam_idx:
                    if self.data_loader.conflict_matrix[exam_idx][other_exam_idx] == 1:
                        has_conflict = True
                        break
            
            if not has_conflict:
                valid_actions.append(timeslot)
        
        return valid_actions
    
    def _get_conflict_indicators(self, timetable: np.ndarray, exam_idx: int) -> List[float]:
        """Get conflict indicators for exam with each timeslot"""
        conflict_indicators = []
        
        for timeslot in range(self.max_timeslots):
            has_conflict = False
            
            for other_exam_idx, other_timeslot in enumerate(timetable):
                if other_timeslot == timeslot and other_exam_idx != exam_idx:
                    if self.data_loader.conflict_matrix[exam_idx][other_exam_idx] == 1:
                        has_conflict = True
                        break
            
            conflict_indicators.append(1.0 if has_conflict else 0.0)
        
        return conflict_indicators
    
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

class HybridNSGA2SARSA:
    """
    Hybrid algorithm combining NSGA-II with SARSA-based solution refinement
    """
    
    def __init__(self, data_loader: STA83DataLoader):
        """
        Initialize hybrid algorithm
        
        Args:
            data_loader: STA83 data loader instance
        """
        self.data_loader = data_loader
        self.problem = STA83Problem(data_loader)
        
        # NSGA-II parameters
        self.pop_size = 50
        self.generations = 50
        self.seed = 42
        
        # SARSA refinement parameters
        self.refine_frequency = 10  # Refine every N generations
        self.refine_top_n = 5       # Refine top N solutions
        self.max_refinement_attempts = 3  # Max refinement attempts per solution
        
        # SARSA agent
        self.sarsa_agent = SARSARefinementAgent(data_loader)
        
        # Results storage
        self.nsga2_result = None
        self.refinement_stats = []
        self.final_pareto_front = None
    
    def set_nsga2_params(self, pop_size: int = 50, generations: int = 50, seed: int = 42):
        """Set NSGA-II parameters"""
        self.pop_size = pop_size
        self.generations = generations
        self.seed = seed
    
    def set_refinement_params(self, refine_frequency: int = 10, refine_top_n: int = 5, 
                            max_refinement_attempts: int = 3):
        """Set SARSA refinement parameters"""
        self.refine_frequency = refine_frequency
        self.refine_top_n = refine_top_n
        self.max_refinement_attempts = max_refinement_attempts
    
    def load_pretrained_sarsa(self, model_path: str) -> bool:
        """Load pre-trained SARSA model"""
        return self.sarsa_agent.load_pretrained_model(model_path)
    
    def run_hybrid_optimization(self, verbose: bool = True) -> Dict:
        """
        Run the hybrid NSGA-II + SARSA optimization
        
        Args:
            verbose: Whether to print progress information
            
        Returns:
            Dictionary containing optimization results
        """
        if verbose:
            print(f"\n🚀 Starting Hybrid NSGA-II + SARSA Optimization")
            print(f"   📊 Population: {self.pop_size}, Generations: {self.generations}")
            print(f"   🧠 SARSA refinement every {self.refine_frequency} generations")
            print(f"   🎯 Refining top {self.refine_top_n} solutions")
        
        start_time = time.time()
        
        # Phase 1: Run NSGA-II with periodic SARSA refinement
        self.nsga2_result = self._run_nsga2_with_sarsa_refinement(verbose)
        
        # Phase 2: Final SARSA refinement of Pareto front
        if self.nsga2_result is not None:
            self.final_pareto_front = self._run_final_refinement_phase(verbose)
        
        total_time = time.time() - start_time
        
        if verbose:
            self._print_final_results()
        
        return {
            'nsga2_result': self.nsga2_result,
            'final_pareto_front': self.final_pareto_front,
            'refinement_stats': self.refinement_stats,
            'total_time': total_time,
            'success': self.final_pareto_front is not None
        }
    
    def _run_nsga2_with_sarsa_refinement(self, verbose: bool = True) -> Any:
        """Run NSGA-II with periodic SARSA refinement"""
        try:
            # Setup NSGA-II algorithm
            algorithm = NSGA2(
                pop_size=self.pop_size,
                sampling=STA83GeneticOperators.get_sampling(),
                crossover=STA83GeneticOperators.get_crossover(),
                mutation=STA83GeneticOperators.get_mutation(),
                eliminate_duplicates=True
            )
            
            if verbose:
                print(f"\n📈 Phase 1: NSGA-II Evolution with SARSA Refinement")
            
            # Run optimization with custom callback for refinement
            result = minimize(
                self.problem,
                algorithm,
                ('n_gen', self.generations),
                seed=self.seed,
                verbose=verbose,
                callback=self._sarsa_refinement_callback if PYTORCH_AVAILABLE else None
            )
            
            return result
            
        except Exception as e:
            print(f"❌ Error in NSGA-II phase: {e}")
            return None
    
    def _sarsa_refinement_callback(self, algorithm):
        """Callback function for periodic SARSA refinement during NSGA-II"""
        generation = algorithm.n_gen
        
        # Refine every N generations
        if generation % self.refine_frequency == 0 and generation > 0:
            if hasattr(algorithm, 'pop') and algorithm.pop is not None:
                self._refine_population_with_sarsa(algorithm.pop, generation)
    
    def _refine_population_with_sarsa(self, population, generation: int):
        """Refine top solutions in population using SARSA"""
        try:
            # Get top solutions based on crowding distance or rank
            top_indices = self._get_top_solution_indices(population)
            
            refined_count = 0
            improved_count = 0
            
            for idx in top_indices[:self.refine_top_n]:
                individual = population[idx]
                original_permutation = individual.X
                
                # Refine with SARSA
                refined_permutation, refinement_info = self.sarsa_agent.refine_solution(
                    original_permutation, max_refinements=self.max_refinement_attempts
                )
                
                refined_count += 1
                
                if refinement_info.get('improvement', False):
                    # Update individual with refined solution
                    individual.X = refined_permutation
                    # Re-evaluate objectives
                    eval_out = {}
                    self.problem._evaluate_single(refined_permutation, eval_out)
                    individual.F = eval_out['F']
                    improved_count += 1
                
                # Store refinement statistics
                self.refinement_stats.append({
                    'generation': generation,
                    'individual_idx': idx,
                    'improvement': refinement_info.get('improvement', False),
                    'original_objectives': refinement_info.get('original_objectives', []),
                    'refined_objectives': refinement_info.get('refined_objectives', [])
                })
            
            print(f"   🧠 Gen {generation}: SARSA refined {refined_count} solutions, improved {improved_count}")
            
        except Exception as e:
            print(f"   ⚠️ SARSA refinement error at generation {generation}: {e}")
    
    def _get_top_solution_indices(self, population) -> List[int]:
        """Get indices of top solutions in population"""
        # Simple approach: sort by first objective (timeslots)
        objectives = np.array([ind.F for ind in population])
        sorted_indices = np.argsort(objectives[:, 0])  # Sort by timeslots
        return sorted_indices.tolist()
    
    def _run_final_refinement_phase(self, verbose: bool = True) -> Optional[np.ndarray]:
        """Final SARSA refinement of the Pareto front"""
        if self.nsga2_result is None or self.nsga2_result.F is None:
            return None
        
        try:
            if verbose:
                print(f"\n🎯 Phase 2: Final SARSA Refinement of Pareto Front")
            
            pareto_front = self.nsga2_result.F.copy()
            pareto_solutions = self.nsga2_result.X.copy()
            
            final_improved = 0
            
            # Refine each solution in the Pareto front
            for i in range(len(pareto_solutions)):
                refined_permutation, refinement_info = self.sarsa_agent.refine_solution(
                    pareto_solutions[i], max_refinements=self.max_refinement_attempts
                )
                
                if refinement_info.get('improvement', False):
                    # Update solution and re-evaluate
                    pareto_solutions[i] = refined_permutation
                    eval_out = {}
                    self.problem._evaluate_single(refined_permutation, eval_out)
                    pareto_front[i] = eval_out['F']
                    final_improved += 1
            
            if verbose:
                print(f"   ✅ Final refinement improved {final_improved}/{len(pareto_solutions)} solutions")
            
            return pareto_front
            
        except Exception as e:
            print(f"❌ Error in final refinement phase: {e}")
            return self.nsga2_result.F if self.nsga2_result else None
    
    def _print_final_results(self):
        """Print final optimization results"""
        print(f"\n📊 Hybrid NSGA-II + SARSA Results:")
        
        if self.final_pareto_front is not None:
            best_timeslots = np.min(self.final_pareto_front[:, 0])
            best_penalty = np.min(self.final_pareto_front[:, 1])
            pareto_size = len(self.final_pareto_front)
            
            print(f"   🏆 Pareto front size: {pareto_size}")
            print(f"   ⏰ Best timeslots: {best_timeslots:.0f}")
            print(f"   📍 Best penalty: {best_penalty:.4f}")
        
        if self.refinement_stats:
            total_refinements = len(self.refinement_stats)
            improvements = sum(1 for stat in self.refinement_stats if stat['improvement'])
            improvement_rate = improvements / total_refinements if total_refinements > 0 else 0
            
            print(f"   🧠 SARSA refinements: {total_refinements}")
            print(f"   📈 Improvement rate: {improvement_rate:.1%}")

class HybridNSGA2SARSARunner:
    """
    Runner class for Hybrid NSGA-II + SARSA algorithm
    """
    
    def __init__(self, data_loader: STA83DataLoader):
        """Initialize the runner"""
        self.data_loader = data_loader
    
    def run_hybrid(self, pop_size: int = 50, generations: int = 50, 
                   sarsa_model_path: Optional[str] = None, seed: int = 42) -> Dict:
        """
        Run the hybrid NSGA-II + SARSA algorithm
        
        Args:
            pop_size: Population size for NSGA-II
            generations: Number of generations for NSGA-II
            sarsa_model_path: Path to pre-trained SARSA model (optional)
            seed: Random seed
            
        Returns:
            Dictionary containing results
        """
        # Create hybrid algorithm
        hybrid = HybridNSGA2SARSA(self.data_loader)
        
        # Set parameters
        hybrid.set_nsga2_params(pop_size, generations, seed)
        
        # Load pre-trained SARSA model if provided
        if sarsa_model_path and os.path.exists(sarsa_model_path):
            if hybrid.load_pretrained_sarsa(sarsa_model_path):
                print(f"✅ Loaded pre-trained SARSA model: {sarsa_model_path}")
            else:
                print(f"⚠️ Failed to load SARSA model, using untrained agent")
        else:
            print(f"ℹ️ No SARSA model provided, using untrained agent")
        
        # Run optimization
        return hybrid.run_hybrid_optimization(verbose=True)

def test_hybrid_sarsa_algorithm():
    """Test the hybrid NSGA-II + SARSA algorithm"""
    print("🧪 Testing Hybrid NSGA-II + SARSA Algorithm")
    print("="*60)
    
    try:
        # Load data
        data_loader = STA83DataLoader()
        if not data_loader.load_data():
            print("❌ Failed to load STA83 data")
            return
        
        print(f"✅ Data loaded: {data_loader.num_exams} exams, {data_loader.num_students} students")
        
        # Create and run hybrid algorithm
        runner = HybridNSGA2SARSARunner(data_loader)
        
        # Quick test with small parameters
        result = runner.run_hybrid(
            pop_size=20,
            generations=10,
            seed=42
        )
        
        if result['success']:
            print(f"\n✅ Hybrid NSGA-II + SARSA test completed successfully!")
            if result['final_pareto_front'] is not None:
                best_timeslots = np.min(result['final_pareto_front'][:, 0])
                best_penalty = np.min(result['final_pareto_front'][:, 1])
                print(f"   Best solution: {best_timeslots:.0f} timeslots, {best_penalty:.4f} penalty")
        else:
            print(f"❌ Hybrid algorithm failed")
        
    except Exception as e:
        print(f"❌ Error testing hybrid algorithm: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hybrid_sarsa_algorithm() 