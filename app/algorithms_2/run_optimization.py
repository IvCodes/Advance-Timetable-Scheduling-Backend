import sys
import os
import argparse

# Add the current directory to the Python path to ensure modules can be found
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from Nsga_II_optimized import run_nsga2_optimizer
from moead import run_moead_optimizer
from spea2 import run_spea2_optimizer
from evaluate import evaluate_timetable
from Data_Loading import spaces_dict, groups_dict, activities_dict, slots, lecturers_dict
from plots import plot_all_metrics

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run timetable optimization algorithms')
    parser.add_argument('--algorithm', type=str, default='nsga2', 
                        choices=['nsga2', 'moead', 'spea2'],
                        help='Optimization algorithm to use (nsga2, moead, or spea2)')
    parser.add_argument('--generations', type=int, default=100,
                        help='Number of generations to run')
    parser.add_argument('--population', type=int, default=50,
                        help='Population size')
    
    # Parse arguments
    args = parser.parse_args()
    
    print(f"Running {args.algorithm.upper()} optimization with population={args.population}, generations={args.generations}")
    
    # Run the selected optimizer
    if args.algorithm.lower() == 'nsga2':
        best_solution, metrics_tracker = run_nsga2_optimizer(
            population_size=args.population,
            generations=args.generations
        )
        
        # Export plots
        output_dir = f"nsga2_output_pop{args.population}_gen{args.generations}"
        os.makedirs(output_dir, exist_ok=True)
        # Get the metrics dictionary from the tracker
        metrics = metrics_tracker.get_metrics() if hasattr(metrics_tracker, 'get_metrics') else metrics_tracker
        plot_all_metrics(metrics, output_dir)
        
    elif args.algorithm.lower() == 'moead':
        # Use the MOEA/D implementation
        best_solution, metrics = run_moead_optimizer(
            activities_dict=activities_dict,
            groups_dict=groups_dict,
            spaces_dict=spaces_dict,
            slots=slots,
            population_size=args.population,
            generations=args.generations
        )
    elif args.algorithm.lower() == 'spea2':
        # Use the SPEA2 implementation
        output_dir = f"spea2_output_pop{args.population}_gen{args.generations}"
        best_solution, metrics = run_spea2_optimizer(
            population_size=args.population,
            generations=args.generations,
            output_dir=output_dir
        )
    else:
        print(f"Error: Unknown algorithm '{args.algorithm}'")
        return
    
    # Print separation line
    print("\n" + "-" * 40)
    
    # Convert the solution if necessary (for SPEA2 which uses activity IDs instead of objects)
    if args.algorithm.lower() == 'spea2':
        converted_solution = {}
        for slot in best_solution:
            converted_solution[slot] = {}
            for room, activity_id in best_solution[slot].items():
                if activity_id is not None:
                    converted_solution[slot][room] = activities_dict.get(activity_id)
                else:
                    converted_solution[slot][room] = None
        best_solution = converted_solution
    
    # Evaluate the best solution and print detailed results
    evaluate_timetable(
        best_solution, 
        activities_dict, 
        groups_dict, 
        spaces_dict, 
        lecturers_dict, 
        slots,
        verbose=True
    )
    
    # Create plots directory if it doesn't exist
    plots_dir = f"plots/{args.algorithm}"
    os.makedirs(plots_dir, exist_ok=True)
    
    # Plot and save all metrics (if available)
    if metrics:
        try:
            # Get the metrics dictionary from the tracker if it's a MetricsTracker object
            metrics_dict = metrics.get_metrics() if hasattr(metrics, 'get_metrics') else metrics
            plot_all_metrics(metrics_dict, save_dir=plots_dir)
            print(f"\nPerformance plots have been saved to the '{plots_dir}' directory.")
        except Exception as e:
            print(f"Error generating metrics dashboard: {str(e)}")
    else:
        print(f"\nNo metrics available for {args.algorithm}")

if __name__ == "__main__":
    main()
