"""
Enhanced Algorithm Runner for Backend with Student ID Mapping
Individual testing and running of all available algorithms with enhanced HTML generation
Supports Quick, Standard, and Full runs with automatic HTML timetable generation
"""
import os
import time
import sys
import importlib
from datetime import datetime
from typing import Dict, Tuple, Any, Optional
from runner import run_optimization_algorithm
from enhanced_html_generator import generate_enhanced_timetable_html
from enhanced_data_loader import enhanced_data_loader

class EnhancedAlgorithmRunner:
    """Enhanced algorithm runner with HTML generation and multiple run modes"""
    
    def __init__(self):
        self.run_modes = {
            'quick': {
                'description': 'Fast test run with minimal parameters',
                'nsga2': {'population': 20, 'generations': 10},
                'spea2': {'population': 20, 'generations': 10},
                'moead': {'population': 20, 'generations': 10},
                'dqn': {'episodes': 50, 'learning_rate': 0.001, 'epsilon': 0.1},
                'sarsa': {'episodes': 50, 'learning_rate': 0.001, 'epsilon': 0.1},
                'implicit_q': {'episodes': 50, 'epsilon': 0.1}
            },
            'standard': {
                'description': 'Balanced run with moderate parameters',
                'nsga2': {'population': 50, 'generations': 25},
                'spea2': {'population': 50, 'generations': 25},
                'moead': {'population': 50, 'generations': 25},
                'dqn': {'episodes': 100, 'learning_rate': 0.001, 'epsilon': 0.1},
                'sarsa': {'episodes': 100, 'learning_rate': 0.001, 'epsilon': 0.1},
                'implicit_q': {'episodes': 100, 'epsilon': 0.1}
            },
            'full': {
                'description': 'Comprehensive run with full parameters',
                'nsga2': {'population': 100, 'generations': 50},
                'spea2': {'population': 100, 'generations': 50},
                'moead': {'population': 100, 'generations': 50},
                'dqn': {'episodes': 200, 'learning_rate': 0.001, 'epsilon': 0.1},
                'sarsa': {'episodes': 200, 'learning_rate': 0.001, 'epsilon': 0.1},
                'implicit_q': {'episodes': 200, 'epsilon': 0.1}
            }
        }
        
        self.available_algorithms = {
            'nsga2': 'NSGA-II - Multi-objective evolutionary algorithm',
            'spea2': 'SPEA2 - Strength Pareto Evolutionary Algorithm',
            'moead': 'MOEA/D - Decomposition-based multi-objective algorithm',
            'dqn': 'DQN - Deep Q-Network reinforcement learning',
            'sarsa': 'SARSA - On-policy reinforcement learning',
            'implicit_q': 'Implicit Q-Learning - Model-free reinforcement learning'
        }
        
        # Output directory for results
        self.output_dir = "app/algorithms_2/output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def run_single_algorithm(self, algorithm: str, mode: str = 'standard', 
                           generate_html: bool = True) -> Tuple[bool, str, Optional[str]]:
        """
        Run a single algorithm with specified mode parameters
        
        Args:
            algorithm: Algorithm name
            mode: Run mode ('quick', 'standard', 'full')
            generate_html: Whether to generate enhanced HTML
            
        Returns:
            Tuple of (success, message, html_path)
        """
        if algorithm not in self.available_algorithms:
            return False, f"Unknown algorithm: {algorithm}", None
        
        if mode not in self.run_modes:
            return False, f"Unknown mode: {mode}", None
        
        params = self.run_modes[mode][algorithm]
        print(f"🚀 Running {algorithm.upper()} ({mode} mode: {params})...")
        
        try:
            start_time = time.time()
            
            # Run the optimization algorithm
            result = run_optimization_algorithm(
                algorithm=algorithm,
                **params,
                enable_plotting=False  # Disable plotting for faster execution
            )
            
            runtime = time.time() - start_time
            
            # Check if we got a valid result
            if not result or 'timetable' not in result:
                return False, f"No valid solution found ({runtime:.1f}s)", None
            
            # Extract metrics
            metrics = result.get('metrics', {})
            hard_violations = metrics.get('hardConstraintViolations', 'Unknown')
            soft_score = metrics.get('softConstraintScore', 'Unknown')
            unassigned = metrics.get('unassignedActivities', 'Unknown')
            
            # Generate enhanced HTML if requested
            html_path = None
            if generate_html:
                try:
                    # Create timestamped filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    html_filename = f"enhanced_timetable_{algorithm}_{mode}_{timestamp}.html"
                    html_path = os.path.join(self.output_dir, html_filename)
                    
                    # Generate enhanced HTML
                    timetable = result['timetable']
                    html_path = generate_enhanced_timetable_html(timetable, html_path)
                    
                    print(f" Enhanced HTML generated: {html_path}")
                    
                except Exception as e:
                    print(f" Warning: Could not generate enhanced HTML: {e}")
                    html_path = None
            
            # Create success message
            message = (f" Success: {hard_violations} hard violations, "
                      f"soft score: {soft_score:.3f}, "
                      f"unassigned: {unassigned} ({runtime:.1f}s)")
            
            return True, message, html_path
            
        except Exception as e:
            return False, f" Error: {str(e)}", None
    
    def run_all_algorithms(self, mode: str = 'standard', 
                          generate_html: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Run all algorithms with specified mode
        
        Args:
            mode: Run mode ('quick', 'standard', 'full')
            generate_html: Whether to generate enhanced HTML
            
        Returns:
            Dictionary with results for each algorithm
        """
        results = {}
        
        print(f"\n Running All Algorithms ({mode.upper()} mode)")
        print("=" * 60)
        
        for algorithm, description in self.available_algorithms.items():
            print(f"\n {algorithm.upper()}: {description}")
            
            success, message, html_path = self.run_single_algorithm(
                algorithm, mode, generate_html
            )
            
            results[algorithm] = {
                'success': success,
                'message': message,
                'html_path': html_path,
                'description': description
            }
            
            print(f"   {message}")
            if html_path:
                print(f"   📄 HTML: {html_path}")
        
        return results
    
    def display_run_modes(self):
        """Display available run modes with their parameters"""
        print("\n⚡ Available Run Modes:")
        print("=" * 50)
        
        for mode, config in self.run_modes.items():
            print(f"\n{mode.upper()}: {config['description']}")
            
            for algorithm in self.available_algorithms.keys():
                params = config[algorithm]
                param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                print(f"  {algorithm.upper()}: {param_str}")
    
    def display_available_algorithms(self):
        """Display available algorithms with descriptions"""
        print("\n🧮 Available Algorithms:")
        print("=" * 50)
        
        for i, (algorithm, description) in enumerate(self.available_algorithms.items(), 1):
            print(f"{i}. {algorithm.upper()}: {description}")
    
    def get_algorithm_statistics(self) -> Dict[str, Any]:
        """Get statistics about the enhanced data loader"""
        mappings = enhanced_data_loader.export_student_mappings()
        
        return {
            'total_students': mappings['total_students'],
            'total_activities': mappings['total_activities'],
            'total_groups': mappings['total_groups'],
            'total_lecturers': len(enhanced_data_loader.lecturers_dict),
            'total_rooms': len(enhanced_data_loader.spaces_dict),
            'total_slots': len(enhanced_data_loader.slots)
        }
    
    def generate_summary_report(self, results: Dict[str, Dict[str, Any]], 
                               mode: str) -> str:
        """Generate a summary report of all algorithm runs"""
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        # Count successes and failures
        successful = [alg for alg, result in results.items() if result['success']]
        failed = [alg for alg, result in results.items() if not result['success']]
        
        # Get statistics
        stats = self.get_algorithm_statistics()
        
        report = f"""
 ENHANCED ALGORITHM RUNNER SUMMARY REPORT
{'=' * 60}
Generated on: {timestamp}
Run Mode: {mode.upper()}

 DATASET STATISTICS:
  • Students: {stats['total_students']}
  • Activities: {stats['total_activities']}
  • Groups: {stats['total_groups']}
  • Lecturers: {stats['total_lecturers']}
  • Rooms: {stats['total_rooms']}
  • Time Slots: {stats['total_slots']}

 ALGORITHM RESULTS:
  • Total Algorithms: {len(results)}
  • Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)
  • Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)

✅ SUCCESSFUL ALGORITHMS:
"""
        
        for alg in successful:
            result = results[alg]
            report += f"  • {alg.upper()}: {result['message']}\n"
            if result['html_path']:
                report += f"    📄 HTML: {result['html_path']}\n"
        
        if failed:
            report += f"\n FAILED ALGORITHMS:\n"
            for alg in failed:
                result = results[alg]
                report += f"  • {alg.upper()}: {result['message']}\n"
        
        report += f"\n Output Directory: {self.output_dir}\n"
        report += "=" * 60
        
        return report


def run_enhanced_algorithm_interface():
    """Interactive interface for running algorithms with enhanced HTML generation"""
    runner = EnhancedAlgorithmRunner()
    
    print("🎓 ENHANCED SLIIT COMPUTING TIMETABLE ALGORITHM RUNNER")
    print("=" * 70)
    print("Individual testing with automatic enhanced HTML generation")
    
    # Display dataset statistics
    stats = runner.get_algorithm_statistics()
    print(f"\n Dataset Overview:")
    print(f"  • {stats['total_students']} students with unique IDs")
    print(f"  • {stats['total_activities']} activities")
    print(f"  • {stats['total_groups']} groups")
    print(f"  • {stats['total_lecturers']} lecturers")
    print(f"  • {stats['total_rooms']} rooms")
    print(f"  • {stats['total_slots']} time slots")
    
    while True:
        print("\n MAIN MENU")
        print("=" * 30)
        print("1. Run Single Algorithm")
        print("2. Run All Algorithms")
        print("3. Show Available Algorithms")
        print("4. Show Run Mode Details")
        print("5. Generate Test HTML (No Algorithm)")
        print("0. Exit")
        
        try:
            choice = input("\nEnter choice (0-5): ").strip()
            
            if choice == '0':
                print(" Exiting Enhanced Algorithm Runner...")
                break
            
            elif choice == '1':
                # Single algorithm menu
                runner.display_available_algorithms()
                
                alg_input = input(f"\nEnter algorithm name or number (1-{len(runner.available_algorithms)}): ").strip()
                
                # Handle numeric input
                if alg_input.isdigit():
                    alg_num = int(alg_input)
                    if 1 <= alg_num <= len(runner.available_algorithms):
                        algorithm = list(runner.available_algorithms.keys())[alg_num - 1]
                    else:
                        print(" Invalid algorithm number!")
                        continue
                else:
                    algorithm = alg_input.lower()
                    if algorithm not in runner.available_algorithms:
                        print(" Invalid algorithm name!")
                        continue
                
                # Mode selection
                print(f"\n⚡ Select Run Mode for {algorithm.upper()}:")
                print("1. Quick   - Fast test run")
                print("2. Standard - Balanced run")
                print("3. Full    - Comprehensive run")
                
                mode_input = input("\nEnter mode choice (1-3): ").strip()
                mode_map = {'1': 'quick', '2': 'standard', '3': 'full'}
                
                if mode_input not in mode_map:
                    print(" Invalid mode choice!")
                    continue
                
                mode = mode_map[mode_input]
                
                # HTML generation option
                html_choice = input("\nGenerate enhanced HTML? (y/n, default: y): ").strip().lower()
                generate_html = html_choice != 'n'
                
                print(f"\n Running {algorithm.upper()} ({mode.upper()} mode)")
                print("=" * 50)
                
                success, message, html_path = runner.run_single_algorithm(
                    algorithm, mode, generate_html
                )
                
                print(f"\n📊 Result: {message}")
                if html_path:
                    print(f" Enhanced HTML: {html_path}")
                    print(" Open this file in a web browser to view the enhanced timetable!")
            
            elif choice == '2':
                # Run all algorithms
                print(f"\n⚡ Select Run Mode for All Algorithms:")
                print("1. Quick   - Fast test run")
                print("2. Standard - Balanced run")
                print("3. Full    - Comprehensive run")
                
                mode_input = input("\nEnter mode choice (1-3): ").strip()
                mode_map = {'1': 'quick', '2': 'standard', '3': 'full'}
                
                if mode_input not in mode_map:
                    print(" Invalid mode choice!")
                    continue
                
                mode = mode_map[mode_input]
                
                # HTML generation option
                html_choice = input("\nGenerate enhanced HTML for each? (y/n, default: y): ").strip().lower()
                generate_html = html_choice != 'n'
                
                results = runner.run_all_algorithms(mode, generate_html)
                
                # Generate and display summary report
                report = runner.generate_summary_report(results, mode)
                print(report)
                
                # Save report to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_file = os.path.join(runner.output_dir, f"algorithm_summary_{mode}_{timestamp}.txt")
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"📄 Summary report saved to: {report_file}")
            
            elif choice == '3':
                runner.display_available_algorithms()
            
            elif choice == '4':
                runner.display_run_modes()
            
            elif choice == '5':
                # Generate test HTML without running algorithm
                print("\n🧪 Generating Test Enhanced HTML...")
                
                try:
                    # Create empty timetable for testing
                    from Data_Loading import slots, spaces_dict
                    test_timetable = {slot: {room: None for room in spaces_dict} for slot in slots}
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    html_filename = f"test_enhanced_timetable_{timestamp}.html"
                    html_path = os.path.join(runner.output_dir, html_filename)
                    
                    html_path = generate_enhanced_timetable_html(test_timetable, html_path)
                    
                    print(f" Test HTML generated: {html_path}")
                    print(" This shows the enhanced layout with student ID mappings!")
                    
                except Exception as e:
                    print(f" Error generating test HTML: {e}")
            
            else:
                print(" Invalid choice!")
        
        except (ValueError, KeyboardInterrupt):
            print("\n Exiting...")
            break
        except Exception as e:
            print(f" Error: {e}")


if __name__ == "__main__":
    run_enhanced_algorithm_interface() 