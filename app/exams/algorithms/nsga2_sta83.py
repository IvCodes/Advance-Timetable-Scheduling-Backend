"""
NSGA-II Implementation for STA83 Exam Timetabling
Multi-objective optimization using pymoo's NSGA-II algorithm
"""
import numpy as np
import matplotlib.pyplot as plt
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from pymoo.visualization.scatter import Scatter
import time
import os
from typing import Dict, List, Tuple, Optional

from core.sta83_data_loader import STA83DataLoader
from core.sta83_problem_fixed import STA83Problem
from core.genetic_operators import STA83GeneticOperators

class NSGA2Runner:
    """
    NSGA-II algorithm runner for STA83 exam timetabling problem
    """
    
    def __init__(self, data_loader: STA83DataLoader, 
                 population_size: int = 50,
                 max_generations: int = 100,
                 output_dir: str = "nsga2_results"):
        """
        Initialize NSGA-II runner
        
        Args:
            data_loader: Loaded STA83 dataset
            population_size: Population size for NSGA-II
            max_generations: Maximum number of generations
            output_dir: Directory to save results
        """
        self.data_loader = data_loader
        self.population_size = population_size
        self.max_generations = max_generations
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize problem
        self.problem = STA83Problem(data_loader)
          # Set up algorithm
        self.algorithm = NSGA2(
            pop_size=population_size,
            sampling=STA83GeneticOperators.get_sampling(),
            crossover=STA83GeneticOperators.get_crossover(prob_crossover=0.9),
            mutation=STA83GeneticOperators.get_mutation(prob_mutation=0.1),
            eliminate_duplicates=True
        )
        
        # Set up termination criteria
        self.termination = get_termination("n_gen", max_generations)
        
        print(f"NSGA-II Runner initialized:")
        print(f"   Dataset: STA83 ({data_loader.num_exams} exams, {data_loader.num_students} students)")
        print(f"   Population size: {population_size}")
        print(f"   Max generations: {max_generations}")
        print(f"   Output directory: {output_dir}")
    
    def run_optimization(self, seed: Optional[int] = None, verbose: bool = True) -> Dict:
        """
        Run NSGA-II optimization
        
        Args:
            seed: Random seed for reproducibility
            verbose: Whether to display optimization progress
            
        Returns:
            Dictionary containing optimization results
        """
        if seed is not None:
            np.random.seed(seed)
        
        print(f"\nStarting NSGA-II optimization...")
        print(f"Objectives: (1) Minimize timeslots, (2) Minimize avg penalty per student")
        
        start_time = time.time()
        
        # Run optimization
        result = minimize(
            self.problem,
            self.algorithm,
            self.termination,
            seed=seed,
            verbose=verbose,
            save_history=True
        )
        
        optimization_time = time.time() - start_time
        
        print(f"Optimization completed in {optimization_time:.2f} seconds")
        print(f"Final population size: {len(result.X)}")
        print(f"Pareto optimal solutions found: {len(result.X)}")
        
        # Process results
        results_dict = self._process_results(result, optimization_time)
        
        # Save results
        self._save_results(results_dict)
        
        return results_dict
    
    def _process_results(self, result, optimization_time: float) -> Dict:
        """Process optimization results"""
        
        # Extract Pareto front solutions
        pareto_front_X = result.X  # Decision variables (permutations)
        pareto_front_F = result.F  # Objective values
        
        # Find extreme solutions
        best_timeslots_idx = np.argmin(pareto_front_F[:, 0])  # Minimize timeslots
        best_penalty_idx = np.argmin(pareto_front_F[:, 1])    # Minimize penalty
        
        best_timeslots_solution = pareto_front_X[best_timeslots_idx]
        best_penalty_solution = pareto_front_X[best_penalty_idx]
        
        # Get detailed schedules for best solutions
        best_timeslots_schedule = self.problem.get_exam_schedule(best_timeslots_solution)
        best_penalty_schedule = self.problem.get_exam_schedule(best_penalty_solution)
        
        # Calculate some statistics
        timeslots_range = (np.min(pareto_front_F[:, 0]), np.max(pareto_front_F[:, 0]))
        penalty_range = (np.min(pareto_front_F[:, 1]), np.max(pareto_front_F[:, 1]))
        
        results_dict = {
            'optimization_time': optimization_time,
            'pareto_front_size': len(pareto_front_F),
            'pareto_front_objectives': pareto_front_F,
            'pareto_front_solutions': pareto_front_X,
            'best_timeslots_solution': {
                'permutation': best_timeslots_solution,
                'objectives': pareto_front_F[best_timeslots_idx],
                'schedule': best_timeslots_schedule
            },
            'best_penalty_solution': {
                'permutation': best_penalty_solution,
                'objectives': pareto_front_F[best_penalty_idx],
                'schedule': best_penalty_schedule
            },
            'objective_ranges': {
                'timeslots': timeslots_range,
                'avg_penalty': penalty_range
            },
            'algorithm_params': {
                'population_size': self.population_size,
                'max_generations': self.max_generations
            },
            'history': result.history if hasattr(result, 'history') else None
        }
        
        return results_dict
    
    def _save_results(self, results: Dict) -> None:
        """Save optimization results to files"""
        
        # Save summary report
        self._save_summary_report(results)
        
        # Save Pareto front data
        self._save_pareto_front(results)
        
        # Generate and save plots
        self._save_plots(results)
        
        print(f"Results saved to: {self.output_dir}")
    
    def _save_summary_report(self, results: Dict) -> None:
        """Save summary report as text file"""
        
        report_path = os.path.join(self.output_dir, "summary_report.txt")
        
        with open(report_path, 'w') as f:
            f.write("STA83 EXAM TIMETABLING - NSGA-II OPTIMIZATION RESULTS\n")
            f.write("=" * 60 + "\n\n")
            
            # Dataset info
            f.write(f"DATASET INFORMATION:\n")
            f.write(f"  Exams: {self.data_loader.num_exams}\n")
            f.write(f"  Students: {self.data_loader.num_students}\n")
            f.write(f"  Conflict density: {np.sum(self.data_loader.conflict_matrix) / (self.data_loader.num_exams * (self.data_loader.num_exams - 1)):.4f}\n\n")
            
            # Algorithm parameters
            f.write(f"ALGORITHM PARAMETERS:\n")
            f.write(f"  Algorithm: NSGA-II\n")
            f.write(f"  Population size: {results['algorithm_params']['population_size']}\n")
            f.write(f"  Max generations: {results['algorithm_params']['max_generations']}\n")
            f.write(f"  Optimization time: {results['optimization_time']:.2f} seconds\n\n")
            
            # Results summary
            f.write(f"OPTIMIZATION RESULTS:\n")
            f.write(f"  Pareto front size: {results['pareto_front_size']} solutions\n")
            f.write(f"  Timeslots range: {results['objective_ranges']['timeslots'][0]:.0f} - {results['objective_ranges']['timeslots'][1]:.0f}\n")
            f.write(f"  Avg penalty range: {results['objective_ranges']['avg_penalty'][0]:.4f} - {results['objective_ranges']['avg_penalty'][1]:.4f}\n\n")
            
            # Best solutions
            f.write(f"BEST TIMESLOTS SOLUTION:\n")
            best_ts = results['best_timeslots_solution']
            f.write(f"  Timeslots used: {best_ts['objectives'][0]:.0f}\n")
            f.write(f"  Avg penalty per student: {best_ts['objectives'][1]:.4f}\n")
            f.write(f"  Total penalty: {best_ts['schedule']['total_penalty_sum']:.2f}\n\n")
            
            f.write(f"BEST PENALTY SOLUTION:\n")
            best_pen = results['best_penalty_solution']
            f.write(f"  Timeslots used: {best_pen['objectives'][0]:.0f}\n")
            f.write(f"  Avg penalty per student: {best_pen['objectives'][1]:.4f}\n")
            f.write(f"  Total penalty: {best_pen['schedule']['total_penalty_sum']:.2f}\n\n")
            
            # Trade-offs analysis
            f.write(f"TRADE-OFFS ANALYSIS:\n")
            timeslot_diff = best_pen['objectives'][0] - best_ts['objectives'][0]
            penalty_diff = best_ts['objectives'][1] - best_pen['objectives'][1]
            f.write(f"  Trading {timeslot_diff:.0f} extra timeslots reduces avg penalty by {penalty_diff:.4f}\n")
            f.write(f"  Penalty reduction percentage: {(penalty_diff/best_ts['objectives'][1]*100):.1f}%\n")
        
        print(f"Summary report saved: {report_path}")
    
    def _save_pareto_front(self, results: Dict) -> None:
        """Save Pareto front data as CSV"""
        
        pareto_path = os.path.join(self.output_dir, "pareto_front.csv")
        
        # Combine objectives and solution indices
        pareto_data = np.column_stack([
            results['pareto_front_objectives'],
            np.arange(len(results['pareto_front_objectives']))
        ])
        
        # Save with headers
        header = "timeslots,avg_penalty_per_student,solution_index"
        np.savetxt(pareto_path, pareto_data, delimiter=',', header=header, comments='')
        
        print(f"Pareto front data saved: {pareto_path}")
    
    def _save_plots(self, results: Dict) -> None:
        """Generate and save optimization plots"""
        
        # 1. Pareto front scatter plot
        plt.figure(figsize=(10, 6))
        
        objectives = results['pareto_front_objectives']
        plt.scatter(objectives[:, 0], objectives[:, 1], alpha=0.7, s=50)
        
        # Highlight best solutions
        best_ts = results['best_timeslots_solution']['objectives']
        best_pen = results['best_penalty_solution']['objectives']
        plt.scatter(best_ts[0], best_ts[1], color='red', s=100, marker='s', 
                   label=f'Best Timeslots ({best_ts[0]:.0f}, {best_ts[1]:.4f})')
        plt.scatter(best_pen[0], best_pen[1], color='blue', s=100, marker='D', 
                   label=f'Best Penalty ({best_pen[0]:.0f}, {best_pen[1]:.4f})')
        
        plt.xlabel('Timeslots Used')
        plt.ylabel('Average Penalty per Student')
        plt.title('STA83 NSGA-II Pareto Front')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        pareto_plot_path = os.path.join(self.output_dir, "pareto_front.png")
        plt.savefig(pareto_plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Pareto front plot saved: {pareto_plot_path}")
        
        # 2. Convergence plot (if history available)
        if results['history'] is not None:
            self._save_convergence_plot(results)
    
    def _save_convergence_plot(self, results: Dict) -> None:
        """Save convergence plot showing algorithm progress"""
        
        history = results['history']
        n_gens = len(history)
        
        # Extract metrics from history
        avg_timeslots = []
        avg_penalty = []
        best_timeslots = []
        best_penalty = []
        
        for gen_result in history:
            if hasattr(gen_result, 'F') and gen_result.F is not None:
                objectives = gen_result.F
                avg_timeslots.append(np.mean(objectives[:, 0]))
                avg_penalty.append(np.mean(objectives[:, 1]))
                best_timeslots.append(np.min(objectives[:, 0]))
                best_penalty.append(np.min(objectives[:, 1]))
        
        # Create convergence plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        generations = range(1, len(avg_timeslots) + 1)
        
        # Timeslots convergence
        ax1.plot(generations, avg_timeslots, 'b-', label='Average', alpha=0.7)
        ax1.plot(generations, best_timeslots, 'r-', label='Best', linewidth=2)
        ax1.set_ylabel('Timeslots Used')
        ax1.set_title('Timeslots Convergence')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Penalty convergence
        ax2.plot(generations, avg_penalty, 'b-', label='Average', alpha=0.7)
        ax2.plot(generations, best_penalty, 'r-', label='Best', linewidth=2)
        ax2.set_xlabel('Generation')
        ax2.set_ylabel('Avg Penalty per Student')
        ax2.set_title('Penalty Convergence')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        convergence_plot_path = os.path.join(self.output_dir, "convergence.png")
        plt.savefig(convergence_plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Convergence plot saved: {convergence_plot_path}")

def run_sta83_nsga2(population_size: int = 50, 
                   max_generations: int = 100,
                   seed: Optional[int] = 42,
                   output_dir: str = "nsga2_results") -> Dict:
    """
    Convenience function to run STA83 NSGA-II optimization
    
    Args:
        population_size: NSGA-II population size
        max_generations: Maximum number of generations
        seed: Random seed for reproducibility
        output_dir: Output directory for results
        
    Returns:
        Optimization results dictionary
    """
    print("STA83 EXAM TIMETABLING WITH NSGA-II")
    print("=" * 50)
    
    # Load data
    print("Loading STA83 dataset...")
    loader = STA83DataLoader()
    if not loader.load_data():
        raise RuntimeError("Failed to load STA83 dataset")
    
    # Quick dataset validation
    analysis = loader.analyze_dataset()
    
    # Run NSGA-II
    runner = NSGA2Runner(
        data_loader=loader,
        population_size=population_size,
        max_generations=max_generations,
        output_dir=output_dir
    )
    
    results = runner.run_optimization(seed=seed, verbose=True)
    
    print(f"\nNSGA-II optimization completed successfully!")
    print(f"Found {results['pareto_front_size']} Pareto optimal solutions")
    print(f"Results saved to: {output_dir}")
    
    return results

if __name__ == "__main__":
    # Run NSGA-II with default parameters
    results = run_sta83_nsga2(
        population_size=30,    # Smaller population for initial testing
        max_generations=50,    # Fewer generations for initial testing
        seed=42,
        output_dir="nsga2_initial_run"
    )
    
    # Display key results
    print(f"\nKEY RESULTS SUMMARY:")
    print(f"   Best timeslots solution: {results['best_timeslots_solution']['objectives'][0]:.0f} timeslots, {results['best_timeslots_solution']['objectives'][1]:.4f} avg penalty")
    print(f"   Best penalty solution: {results['best_penalty_solution']['objectives'][0]:.0f} timeslots, {results['best_penalty_solution']['objectives'][1]:.4f} avg penalty")
    print(f"   Optimization time: {results['optimization_time']:.2f} seconds")
