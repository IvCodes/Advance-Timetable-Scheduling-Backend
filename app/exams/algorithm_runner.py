"""
STA83 Algorithm Runner
Individual testing and running of all available algorithms with different run modes
Supports Quick, Standard, and Full runs for comprehensive testing
"""
import numpy as np
import time
import sys
import os
from datetime import datetime
from typing import Dict, Tuple, Any, Optional, List
import glob

# Add paths for imports
sys.path.append('.')
sys.path.append('./core')
sys.path.append('./algorithms')
sys.path.append('./constraint_programming')
sys.path.append('./rl')

# Base directory for the exams module, where algorithm_runner.py resides
BASE_EXAMS_DIR = os.path.dirname(os.path.abspath(__file__))

class AlgorithmRunner:
    """Enhanced algorithm runner with multiple run modes"""
    
    def __init__(self):
        self.run_modes = {
            'quick': {
                'description': 'Fast test run with minimal parameters',
                'nsga2': {'pop_size': 20, 'generations': 10},
                'moead': {'pop_size': 20, 'generations': 10},
                'cp': {'time_limit': 30, 'timeslots': 13},
                'dqn': {'episodes': 3},
                'sarsa': {'episodes': 10},
                'hybrid': {'pop_size': 20, 'generations': 10},
                'hybrid_sarsa': {'pop_size': 20, 'generations': 10}
            },
            'standard': {
                'description': 'Balanced run with moderate parameters',
                'nsga2': {'pop_size': 50, 'generations': 25},
                'moead': {'pop_size': 50, 'generations': 25},
                'cp': {'time_limit': 120, 'timeslots': 13},
                'dqn': {'episodes': 10},
                'sarsa': {'episodes': 50},
                'hybrid': {'pop_size': 50, 'generations': 25},
                'hybrid_sarsa': {'pop_size': 50, 'generations': 25}
            },
            'full': {
                'description': 'Comprehensive run with full parameters',
                'nsga2': {'pop_size': 100, 'generations': 50},
                'moead': {'pop_size': 100, 'generations': 50},
                'cp': {'time_limit': 300, 'timeslots': 13},
                'dqn': {'episodes': 20},
                'sarsa': {'episodes': 100},
                'hybrid': {'pop_size': 100, 'generations': 50},
                'hybrid_sarsa': {'pop_size': 100, 'generations': 50}
            }
        }
    
    def run_nsga2(self, mode: str = 'standard') -> Tuple[bool, str, Optional[Dict], Optional[float]]:
        """Run NSGA-II with specified mode parameters"""
        params = self.run_modes[mode]['nsga2']
        print(f"Running NSGA-II ({mode} mode: {params['pop_size']} pop, {params['generations']} gen)...")
        runtime = None
        try:
            from .core.sta83_data_loader import STA83DataLoader
            from .algorithms.nsga2_runner import NSGA2Runner
            
            crs_file_path = os.path.join(BASE_EXAMS_DIR, 'data', 'sta-f-83.crs')
            stu_file_path = os.path.join(BASE_EXAMS_DIR, 'data', 'sta-f-83.stu')

            data_loader = STA83DataLoader(crs_file=crs_file_path, stu_file=stu_file_path)
            if not data_loader.load_data():
                return False, "Failed to load data", None, runtime
            
            runner = NSGA2Runner(data_loader)
            problem = runner.problem
            start_time = time.time()
            result = runner.run_nsga2(
                pop_size=params['pop_size'], 
                generations=params['generations'], 
                seed=42
            )
            runtime = time.time() - start_time
            
            if result.X is not None and len(result.X) > 0:
                objectives = result.F
                solutions = result.X
                sorted_indices = np.lexsort((objectives[:, 1], objectives[:, 0]))
                best_solution_idx = sorted_indices[0]
                best_permutation = solutions[best_solution_idx]
                decoded_schedule = problem.get_exam_schedule(best_permutation)
                message = f"{len(result.F)} solutions, best: {decoded_schedule['timeslots_used']:.0f} ts, {decoded_schedule['avg_penalty_per_student']:.2f} penalty ({runtime:.1f}s)"
                return True, message, decoded_schedule, runtime
            else:
                return False, f"No solutions found ({runtime:.1f}s)", None, runtime
        except ImportError as e:
            return False, f"ImportError: {str(e)}", None, runtime
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            return False, f"Error in run_nsga2: {str(e)}\nTraceback: {tb_str}", None, runtime

    def run_moead(self, mode: str = 'standard') -> Tuple[bool, str, Optional[Dict], Optional[float]]:
        """Run MOEA/D with specified mode parameters"""
        params = self.run_modes[mode]['moead']
        print(f"Running MOEA/D ({mode} mode: {params['pop_size']} pop, {params['generations']} gen)...")
        runtime = None
        try:
            from .core.sta83_data_loader import STA83DataLoader
            from .algorithms.moead import MOEADRunner
            
            crs_file_path = os.path.join(BASE_EXAMS_DIR, 'data', 'sta-f-83.crs')
            stu_file_path = os.path.join(BASE_EXAMS_DIR, 'data', 'sta-f-83.stu')
            data_loader = STA83DataLoader(crs_file=crs_file_path, stu_file=stu_file_path)

            if not data_loader.load_data():
                return False, "Failed to load data", None, runtime
            
            runner = MOEADRunner(data_loader)
            problem = runner.problem
            start_time = time.time()
            result = runner.run_moead(
                pop_size=params['pop_size'], 
                generations=params['generations'], 
                seed=42
            )
            runtime = time.time() - start_time
            
            if result.X is not None and len(result.X) > 0:
                objectives = result.F
                solutions = result.X
                sorted_indices = np.lexsort((objectives[:, 1], objectives[:, 0]))
                best_solution_idx = sorted_indices[0]
                best_permutation = solutions[best_solution_idx]
                decoded_schedule = problem.get_exam_schedule(best_permutation)
                message = f"{len(result.F)} solutions, best: {decoded_schedule['timeslots_used']:.0f} ts, {decoded_schedule['avg_penalty_per_student']:.2f} penalty ({runtime:.1f}s)"
                return True, message, decoded_schedule, runtime
            else:
                return False, f"No solutions found ({runtime:.1f}s)", None, runtime
                
        except ImportError as e:
            return False, f"ImportError in run_moead: {str(e)}", None, runtime
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            return False, f"Error in run_moead: {str(e)}\nTraceback: {tb_str}", None, runtime

    def run_cp(self, mode: str = 'standard') -> Tuple[bool, str, Optional[Dict], Optional[float]]:
        """Run Constraint Programming with specified mode parameters"""
        params = self.run_modes[mode]['cp']
        print(f"Running CP ({mode} mode: {params['time_limit']}s limit, {params['timeslots']} timeslots)...")
        runtime = None
        try:
            from .constraint_programming.cp_sta83_solver import STA83CPSolver
            from .core.sta83_data_loader import STA83DataLoader
            
            crs_file_path = os.path.join(BASE_EXAMS_DIR, 'data', 'sta-f-83.crs')
            stu_file_path = os.path.join(BASE_EXAMS_DIR, 'data', 'sta-f-83.stu')
            data_loader = STA83DataLoader(crs_file=crs_file_path, stu_file=stu_file_path)

            if not data_loader.load_data():
                return False, "Failed to load data", None, runtime
            
            solver = STA83CPSolver(data_loader)
            start_time = time.time()
            schedule_result = solver.solve_with_fixed_timeslots(
                params['timeslots'], 
                time_limit_seconds=params['time_limit']
            )
            runtime = time.time() - start_time
            
            if schedule_result is not None and schedule_result.get('feasible', False):
                timeslots_used = schedule_result.get('timeslots_used', 0)
                penalty = schedule_result.get('proximity_penalty', 0.0)
                status_msg = 'OPTIMAL' if schedule_result.get('optimal', False) else 'FEASIBLE'
                message = f"Solution found: {timeslots_used} timeslots, penalty: {penalty:.2f}, status: {status_msg} ({runtime:.1f}s)"
                return True, message, schedule_result, runtime
            else:
                status = schedule_result.get('status', 'UNKNOWN') if schedule_result else 'NO_RESULT'
                return False, f"No solution found, status: {status} ({runtime:.1f}s)", None, runtime
                
        except ImportError as e:
            return False, f"ImportError in run_cp: {str(e)}", None, runtime
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            return False, f"Error in run_cp: {str(e)}\nTraceback: {tb_str}", None, runtime

    def run_dqn(self, mode: str = 'standard') -> Tuple[bool, str, Optional[Dict], Optional[float]]:
        """Run DQN with specified mode parameters"""
        params = self.run_modes[mode]['dqn']
        print(f"Running DQN ({mode} mode: {params['episodes']} episodes)...")
        runtime = None
        schedule_data = None
        try:
            from .rl.environment import ExamTimetablingEnv
            from .rl.agent import DQNAgent
            import glob
            
            start_time = time.time()
            
            # Create environment with same config as trained model
            env = ExamTimetablingEnv(max_timeslots=18)
            
            # Create agent
            state_size = env.observation_space.shape[0]
            action_size = env.action_space.n
            
            agent = DQNAgent(
                state_size=state_size,
                action_size=action_size,
                epsilon_start=0.0  # No exploration for inference
            )
            
            # Try to load trained model - check multiple possible locations
            model_patterns = [
                'results/dqn_final_results/trained_dqn_model.pth',
                'results/dqn_sta83_results_*/trained_dqn_model.pth',
                'results/*/trained_dqn_model.pth',
                'results/**/trained_dqn_model.pth',
                '*.pth'
            ]
            
            print(f"   Searching for trained models...")
            model_to_load = self._find_model_path(model_patterns)
            
            if model_to_load:
                agent.load_model(model_to_load)
                print(f"   ✅ Successfully loaded trained model: {os.path.basename(model_to_load)}")
                
                # Run evaluation with trained model
                eval_stats = agent.evaluate(env, num_episodes=params['episodes'])
                runtime = time.time() - start_time
                
                if eval_stats.get('solutions'):
                    return True, f"Success rate: {eval_stats['success_rate']:.3f}, avg: {eval_stats['avg_timeslots']:.1f} timeslots, penalty: {eval_stats['avg_proximity_penalty']:.2f} ({runtime:.1f}s)", schedule_data, runtime
                else:
                    return True, f"Success rate: {eval_stats['success_rate']:.3f}, avg reward: {eval_stats['avg_reward']:.2f} ({runtime:.1f}s)", schedule_data, runtime
            else:
                print(f"   ❌ No trained models found in any search pattern")
                return False, "No trained models found. Run training first.", schedule_data, runtime
                
        except ImportError:
            return False, "DQN implementation not available (PyTorch required)", None, runtime
        except Exception as e:
            return False, f"Error: {str(e)}", None, runtime

    def run_sarsa(self, mode: str = 'standard') -> Tuple[bool, str, Optional[Dict], Optional[float]]:
        """Run SARSA with specified mode parameters"""
        params = self.run_modes[mode]['sarsa']
        print(f"Running SARSA ({mode} mode: {params['episodes']} episodes)...")
        runtime = None
        schedule_data = None
        try:
            from .rl.sarsa_environment import ExamTimetablingSARSAEnv
            from .rl.sarsa_agent import SARSAAgent
            import glob
            import os
            
            start_time = time.time()
            
            # Create environment
            env = ExamTimetablingSARSAEnv(max_timeslots=18)
            
            # Create agent
            state_size = env.observation_space.shape[0]
            action_size = env.action_space.n
            
            agent = SARSAAgent(
                state_size=state_size,
                action_size=action_size,
                epsilon_start=0.8,  # High exploration initially
                epsilon_decay=0.995,
                learning_rate=0.001
            )
            
            # Try to load trained model - check multiple possible locations
            model_patterns = [
                'results/sarsa_final_results/trained_sarsa_model.pth',
                'results/sarsa_sta83_results_*/trained_sarsa_model.pth',
                'results/*/trained_sarsa_model.pth',
                'results/**/trained_sarsa_model.pth',
                '*.pth'
            ]
            
            print(f"   Searching for trained SARSA models...")
            model_to_load = self._find_model_path(model_patterns)
            
            if model_to_load:
                agent.load_model(model_to_load)
                print(f"   ✅ Successfully loaded trained model: {os.path.basename(model_to_load)}")
                
                # Run evaluation with trained model
                eval_stats = agent.evaluate(env, num_episodes=params['episodes'])
                runtime = time.time() - start_time
                
                success_rate = eval_stats.get('success_rate', 0)
                avg_timeslots = eval_stats.get('avg_timeslots', 0)
                avg_reward = eval_stats.get('avg_reward', 0)
                
                if avg_timeslots:
                    return True, f"Success rate: {success_rate:.1%}, avg: {avg_timeslots:.1f} timeslots, reward: {avg_reward:.1f} ({runtime:.1f}s)", schedule_data, runtime
                else:
                    return True, f"Success rate: {success_rate:.1%}, avg reward: {avg_reward:.1f} ({runtime:.1f}s)", schedule_data, runtime
            else:
                print(f"   ❌ No trained models found")
                print(f"   🏃‍♂️ Training new SARSA model instead...")
                
                # Train new model
                training_stats = agent.train(env, num_episodes=params['episodes'], verbose=True)
                runtime = time.time() - start_time
                
                success_rate = training_stats.get('success_rate', 0)
                avg_timeslots = training_stats.get('avg_timeslots', 0)
                avg_reward = training_stats.get('avg_reward', 0)
                
                if avg_timeslots:
                    return True, f"Training complete - Success rate: {success_rate:.1%}, avg: {avg_timeslots:.1f} timeslots, reward: {avg_reward:.1f} ({runtime:.1f}s)", schedule_data, runtime
                else:
                    return True, f"Training complete - Success rate: {success_rate:.1%}, avg reward: {avg_reward:.1f} ({runtime:.1f}s)", schedule_data, runtime
        except ImportError:
            return False, "SARSA implementation not available (PyTorch required)", None, runtime
        except Exception as e:
            return False, f"Error: {str(e)}", None, runtime

    def run_hybrid(self, mode: str = 'standard') -> Tuple[bool, str, Optional[Dict], Optional[float]]:
        """Run Hybrid NSGA-II + DQN with specified mode parameters"""
        params = self.run_modes[mode]['hybrid']
        print(f"Running Hybrid NSGA-II + DQN ({mode} mode: {params['pop_size']} pop, {params['generations']} gen)...")
        runtime = None
        try:
            from .core.sta83_data_loader import STA83DataLoader
            from .algorithms.hybrid_nsga2_dqn import HybridNSGA2DQNRunner
            import glob
            
            crs_file_path = os.path.join(BASE_EXAMS_DIR, 'data', 'sta-f-83.crs')
            stu_file_path = os.path.join(BASE_EXAMS_DIR, 'data', 'sta-f-83.stu')
            data_loader = STA83DataLoader(crs_file=crs_file_path, stu_file=stu_file_path)
            if not data_loader.load_data():
                return False, "Failed to load data", None, runtime
            
            runner = HybridNSGA2DQNRunner(data_loader)
            start_time = time.time()
            
            # Try to find a trained DQN model
            model_patterns = [
                'results/dqn_final_results/trained_dqn_model.pth',
                'results/dqn_sta83_results_*/trained_dqn_model.pth',
                'results/*/trained_dqn_model.pth',
                'results/**/trained_dqn_model.pth'
            ]
            
            dqn_model_to_load = self._find_model_path(model_patterns)
            
            # Run hybrid optimization
            result = runner.run_hybrid(
                pop_size=params['pop_size'], 
                generations=params['generations'], 
                dqn_model_path=dqn_model_to_load,
                seed=42
            )
            runtime = time.time() - start_time
            
            if result.get('final_pareto_front') is not None and len(result['final_pareto_front']) > 0:
                pareto_front = result['final_pareto_front']
                best_timeslots = np.min(pareto_front[:, 0])
                best_penalty = np.min(pareto_front[:, 1])
                
                # Check for DQN improvements
                refinement_stats = result.get('refinement_stats', [])
                improvements = sum(1 for stat in refinement_stats if stat.get('improvement', False))
                
                dqn_status = f", DQN improved {improvements}/{len(refinement_stats)} solutions" if refinement_stats else ", DQN: no model"
                
                return True, f"{len(pareto_front)} solutions, best: {best_timeslots:.0f} timeslots, {best_penalty:.2f} penalty{dqn_status} ({runtime:.1f}s)", None, runtime
            else:
                return False, f"No solutions found ({runtime:.1f}s)", None, runtime
                
        except ImportError as e:
            return False, f"Hybrid implementation not available: {str(e)}", None, runtime
        except Exception as e:
            return False, f"Error: {str(e)}", None, runtime

    def run_hybrid_sarsa(self, mode: str = 'standard') -> Tuple[bool, str, Optional[Dict], Optional[float]]:
        """Run Hybrid NSGA-II + SARSA with specified mode parameters"""
        params = self.run_modes[mode]['hybrid_sarsa']
        print(f"Running Hybrid NSGA-II + SARSA ({mode} mode: {params['pop_size']} pop, {params['generations']} gen)...")
        runtime = None
        try:
            from .core.sta83_data_loader import STA83DataLoader
            from .algorithms.hybrid_nsga2_sarsa import HybridNSGA2SARSARunner
            import glob
            
            crs_file_path = os.path.join(BASE_EXAMS_DIR, 'data', 'sta-f-83.crs')
            stu_file_path = os.path.join(BASE_EXAMS_DIR, 'data', 'sta-f-83.stu')
            data_loader = STA83DataLoader(crs_file=crs_file_path, stu_file=stu_file_path)
            if not data_loader.load_data():
                return False, "Failed to load data", None, runtime
            
            runner = HybridNSGA2SARSARunner(data_loader)
            start_time = time.time()
            
            # Try to find a trained SARSA model
            model_patterns = [
                'results/sarsa_final_results/trained_sarsa_model.pth',
                'results/sarsa_sta83_results_*/trained_sarsa_model.pth',
                'results/*/trained_sarsa_model.pth',
                'results/**/trained_sarsa_model.pth'
            ]
            
            sarsa_model_to_load = self._find_model_path(model_patterns)
            
            # Run hybrid optimization
            result = runner.run_hybrid(
                pop_size=params['pop_size'], 
                generations=params['generations'], 
                sarsa_model_path=sarsa_model_to_load,
                seed=42
            )
            runtime = time.time() - start_time
            
            if result.get('final_pareto_front') is not None and len(result['final_pareto_front']) > 0:
                pareto_front = result['final_pareto_front']
                best_timeslots = np.min(pareto_front[:, 0])
                best_penalty = np.min(pareto_front[:, 1])
                
                # Check for SARSA improvements
                refinement_stats = result.get('refinement_stats', [])
                improvements = sum(1 for stat in refinement_stats if stat.get('improvement', False))
                
                sarsa_status = f", SARSA improved {improvements}/{len(refinement_stats)} solutions" if refinement_stats else ", SARSA: no model"
                
                return True, f"{len(pareto_front)} solutions, best: {best_timeslots:.0f} timeslots, {best_penalty:.2f} penalty{sarsa_status} ({runtime:.1f}s)", None, runtime
            else:
                return False, f"No solutions found ({runtime:.1f}s)", None, runtime
                
        except ImportError as e:
            return False, f"Hybrid SARSA implementation not available: {str(e)}", None, runtime
        except Exception as e:
            return False, f"Error: {str(e)}", None, runtime

    def display_run_modes(self):
        """Display available run modes with their parameters"""
        print("\nAvailable Run Modes:")
        print("=" * 50)
        for mode, config in self.run_modes.items():
            print(f"{mode.upper()}: {config['description']}")
            print(f"  NSGA-II: {config['nsga2']['pop_size']} pop, {config['nsga2']['generations']} gen")
            print(f"  MOEA/D:  {config['moead']['pop_size']} pop, {config['moead']['generations']} gen")
            print(f"  CP:      {config['cp']['time_limit']}s limit, {config['cp']['timeslots']} timeslots")
            print(f"  DQN:     {config['dqn']['episodes']} episodes")
            print(f"  SARSA:   {config['sarsa']['episodes']} episodes")
            print(f"  Hybrid:  {config['hybrid']['pop_size']} pop, {config['hybrid']['generations']} gen (NSGA-II + DQN)")
            print()

    def run_single_algorithm(self, algorithm: str, mode: str) -> Tuple[bool, str, Optional[Dict], Optional[float]]:
        """Run a single algorithm with specified mode"""
        algorithm_map = {
            'nsga2': self.run_nsga2,
            'moead': self.run_moead,
            'cp': self.run_cp,
            'dqn': self.run_dqn,
            'sarsa': self.run_sarsa,
            'hybrid': self.run_hybrid,
            'hybrid_sarsa': self.run_hybrid_sarsa
        }
        
        if algorithm in algorithm_map:
            return algorithm_map[algorithm](mode)
        else:
            return False, f"Unknown algorithm: {algorithm}", None, None

    def run_all_algorithms(self, mode: str) -> Dict[str, Dict[str, Any]]:
        """Run all algorithms with specified mode"""
        algorithms = ['nsga2', 'moead', 'cp', 'dqn', 'sarsa', 'hybrid', 'hybrid_sarsa']
        algorithm_names = ['NSGA-II', 'MOEA/D', 'CP', 'DQN', 'SARSA', 'Hybrid NSGA-II+DQN', 'Hybrid NSGA-II+SARSA']
        results = {}
        
        print(f"\nRunning All Algorithms ({mode.upper()} mode)")
        print("=" * 50)
        
        for alg, name in zip(algorithms, algorithm_names):
            print(f"\n{name}:")
            success, message, schedule_data, runtime = self.run_single_algorithm(alg, mode)
            results[name] = {
                'success': success,
                'message': message,
                'schedule_data': schedule_data,
                'runtime_seconds': runtime
            }
            print(f"   {message}")
            if schedule_data:
                print(f"  Schedule: {schedule_data.get('timeslots_used')} timeslots, {len(schedule_data.get('exam_to_slot_map', {}))} exams scheduled.")
        
        return results

    # Helper for model path resolution
    def _find_model_path(self, patterns: List[str]) -> Optional[str]:
        for pattern in patterns:
            # Construct path relative to BASE_EXAMS_DIR for glob
            full_pattern = os.path.join(BASE_EXAMS_DIR, pattern)
            found_files = glob.glob(full_pattern)
            if found_files:
                return found_files[0] # Return the first match
        return None

def main():
    """Enhanced STA83 Algorithm Runner with multiple run modes"""
    runner = AlgorithmRunner()
    
    print("🔬 STA83 ALGORITHM RUNNER")
    print("=" * 60)
    print("Individual testing and running of all available algorithms")
    
    # Available algorithms
    algorithms = [
        ("NSGA-II", "nsga2", "Multi-objective evolutionary algorithm"),
        ("MOEA/D", "moead", "Decomposition-based multi-objective algorithm"),
        ("CP", "cp", "Constraint programming solver"),
        ("DQN", "dqn", "Deep Q-Network (uses trained models)"),
        ("SARSA", "sarsa", "SARSA on-policy reinforcement learning"),
        ("Hybrid NSGA-II+DQN", "hybrid", "NSGA-II with DQN-based solution refinement"),
        ("Hybrid NSGA-II+SARSA", "hybrid_sarsa", "NSGA-II with SARSA-based solution refinement")
    ]
    
    while True:
        print("\n📋 MAIN MENU")
        print("=" * 30)
        print("1. Run Single Algorithm")
        print("2. Run All Algorithms")
        print("3. Show Run Mode Details")
        print("0. Exit")
        
        try:
            main_choice = input("\nEnter choice (0-3): ")
            main_choice = int(main_choice)
            
            if main_choice == 0:
                print("Exiting...")
                break
                
            elif main_choice == 1:
                # Single algorithm menu
                print("\n🎯 SELECT ALGORITHM:")
                for i, (name, _, description) in enumerate(algorithms, 1):
                    print(f"  {i}. {name} - {description}")
                
                alg_choice = input(f"\nEnter algorithm choice (1-{len(algorithms)}): ")
                alg_choice = int(alg_choice)
                
                if 1 <= alg_choice <= len(algorithms):
                    name, alg_key, description = algorithms[alg_choice-1]
                    
                    # Mode selection
                    print(f"\n⚡ SELECT RUN MODE for {name}:")
                    print("  1. Quick   - Fast test run")
                    print("  2. Standard - Balanced run")
                    print("  3. Full    - Comprehensive run")
                    
                    mode_choice = input("\nEnter mode choice (1-3): ")
                    mode_choice = int(mode_choice)
                    
                    mode_map = {1: 'quick', 2: 'standard', 3: 'full'}
                    if mode_choice in mode_map:
                        mode = mode_map[mode_choice]
                        
                        print(f"\n🚀 Running {name} ({mode.upper()} mode)")
                        print("=" * 50)
                        print(f"Description: {description}")
                        
                        success, message, schedule_data, runtime = runner.run_single_algorithm(alg_key, mode)
                        print(f"Result: {message}")
                        
                        if success:
                            print("✅ Algorithm completed successfully!")
                        else:
                            print("❌ Algorithm failed or found no solution")
                    else:
                        print("Invalid mode choice!")
                else:
                    print("Invalid algorithm choice!")
                    
            elif main_choice == 2:
                # Run all algorithms
                print("\n⚡ SELECT RUN MODE for All Algorithms:")
                print("  1. Quick   - Fast test run")
                print("  2. Standard - Balanced run")
                print("  3. Full    - Comprehensive run")
                
                mode_choice = input("\nEnter mode choice (1-3): ")
                mode_choice = int(mode_choice)
                
                mode_map = {1: 'quick', 2: 'standard', 3: 'full'}
                if mode_choice in mode_map:
                    mode = mode_map[mode_choice]
                    
                    results = runner.run_all_algorithms(mode)
                    
                    # Summary
                    print(f"\n📊 SUMMARY ({mode.upper()} mode):")
                    print("=" * 40)
                    successful = [name for name, result in results.items() if result['success']]
                    failed = [name for name, result in results.items() if not result['success']]
                    
                    print(f"✅ Successful: {successful}")
                    if failed:
                        print(f"❌ Failed: {failed}")
                    
                    print(f"\nSuccess Rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
                else:
                    print("Invalid mode choice!")
                    
            elif main_choice == 3:
                # Show run mode details
                runner.display_run_modes()
                
            else:
                print("Invalid choice!")
                
        except (ValueError, KeyboardInterrupt):
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main() 