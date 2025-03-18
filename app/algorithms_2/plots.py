"""
Visualization module for optimization algorithms.
Generates plots to visualize the performance of optimization algorithms.
"""

import os
import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("Warning: matplotlib and/or numpy not installed. Plotting functionality will be disabled.")
    print("Run 'pip install -r requirements.txt' to enable plotting.")

# Constants
PLOTTING_ERROR_MSG = "Plotting not available. Install matplotlib and numpy."
LABEL_BEST_SOLUTION = "Best Solution"
LABEL_POPULATION_AVG = "Population Average"
LABEL_NO_DATA = "No data available"

def plot_convergence(metrics, save_dir='.'):
    """
    Plot convergence metrics for the optimization algorithm.
    
    Args:
        metrics: Dictionary containing tracked metrics
        save_dir: Directory to save the plots
    """
    if not PLOTTING_AVAILABLE:
        print(PLOTTING_ERROR_MSG)
        return
        
    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    # Setup figure
    plt.figure(figsize=(12, 10))
    
    # Plot hard constraint violations (primary objective)
    plt.subplot(2, 1, 1)
    x = range(len(metrics['best_hard_violations']))
    
    if x:  # Only plot if we have data
        plt.plot(x, metrics['best_hard_violations'], 'b-', label=LABEL_BEST_SOLUTION, linewidth=2)
        plt.plot(x, metrics['average_hard_violations'], 'r--', label=LABEL_POPULATION_AVG)
        
        plt.title('Hard Constraint Violations Over Generations', fontsize=14)
        plt.xlabel('Generation', fontsize=12)
        plt.ylabel('Total Violations', fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Ensure y-axis starts from 0 or min value for better visibility
        min_value = min(min(metrics['best_hard_violations']), 0)
        plt.ylim(min_value, max(metrics['average_hard_violations']) * 1.1)
    else:
        plt.text(0.5, 0.5, LABEL_NO_DATA, 
                horizontalalignment='center', verticalalignment='center',
                transform=plt.gca().transAxes, fontsize=14)
    
    # Plot soft constraint score (secondary objective)
    plt.subplot(2, 1, 2)
    
    if x:  # Only plot if we have data
        plt.plot(x, metrics['best_soft_score'], 'g-', label=LABEL_BEST_SOLUTION, linewidth=2)
        plt.plot(x, metrics['average_soft_score'], 'm--', label=LABEL_POPULATION_AVG)
        
        plt.title('Soft Constraint Score Over Generations', fontsize=14)
        plt.xlabel('Generation', fontsize=12)
        plt.ylabel('Soft Score (lower is better)', fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Ensure y-axis starts from 0 or min value for better visibility
        min_value = min(min(metrics['best_soft_score']), 0)
        plt.ylim(min_value, max(metrics['average_soft_score']) * 1.1)
    else:
        plt.text(0.5, 0.5, LABEL_NO_DATA, 
                horizontalalignment='center', verticalalignment='center',
                transform=plt.gca().transAxes, fontsize=14)
    
    plt.tight_layout()
    plt.savefig(f'{save_dir}/convergence.png', dpi=300)
    plt.close()
    
    print(f"Convergence plot saved to {save_dir}/convergence.png")


def plot_constraint_violations(metrics, save_dir='.'):
    """
    Plot the breakdown of constraint violations over generations.
    
    Args:
        metrics: Dictionary containing tracked metrics
        save_dir: Directory to save the plots
    """
    if not PLOTTING_AVAILABLE:
        print(PLOTTING_ERROR_MSG)
        return
        
    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    if not metrics['constraint_violations']:
        print("No constraint violation data available for plotting.")
        return
    
    # Extract violation types and prepare data
    violation_types = list(metrics['constraint_violations'][0].keys())
    
    # Remove 'total' for the detailed plot
    if 'total' in violation_types:
        violation_types.remove('total')
    
    x = range(len(metrics['constraint_violations']))
    
    # Setup figure
    plt.figure(figsize=(14, 8))
    
    # Plot each violation type
    for violation_type in violation_types:
        values = [v[violation_type] for v in metrics['constraint_violations']]
        plt.plot(x, values, marker='o', linestyle='-', markersize=4, linewidth=2,
                label=violation_type.replace('_', ' ').title())
    
    plt.title('Constraint Violations by Type Over Generations', fontsize=14)
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Number of Violations', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(f'{save_dir}/constraint_violations.png', dpi=300)
    plt.close()
    
    print(f"Constraint violations plot saved to {save_dir}/constraint_violations.png")


def plot_constraint_violations_by_type(metrics, output_path=None):
    """
    Plot the evolution of different types of constraint violations over generations.
    
    Parameters:
        metrics (dict): Dictionary containing optimization metrics
        output_path (str): Path to save the plot (if None, plot will be displayed)
    """
    if not metrics['constraint_violations']:
        return
    
    try:
        # Extract violation types and prepare data
        # constraint_violations now contains tuples of (hard_violations, soft_violations)
        hard_violations, _ = metrics['constraint_violations'][0]
        
        # Check if hard_violations is a dictionary or tuple
        if isinstance(hard_violations, dict):
            violation_types = list(hard_violations.keys())
            
            # Remove 'total' for the detailed plot
            if 'total' in violation_types:
                violation_types.remove('total')
            
            x = range(len(metrics['constraint_violations']))
            
            # Setup figure
            plt.figure(figsize=(14, 8))
            
            # Plot each violation type
            for violation_type in violation_types:
                values = [v[0][violation_type] for v in metrics['constraint_violations']]
                plt.plot(x, values, marker='o', linestyle='-', markersize=4, linewidth=2,
                        label=violation_type.replace('_', ' ').title())
        else:
            # If hard_violations is a tuple, plot each index separately
            violation_names = ["Room Capacity", "Room Availability", "Lecturer Availability", 
                              "Group Availability", "Consecutive Sessions"]
            
            x = range(len(metrics['constraint_violations']))
            
            # Setup figure
            plt.figure(figsize=(14, 8))
            
            # Plot each violation type
            for i, violation_name in enumerate(violation_names):
                if i < len(hard_violations):  # Make sure we don't go out of bounds
                    values = [v[0][i] if i < len(v[0]) else 0 for v in metrics['constraint_violations']]
                    plt.plot(x, values, marker='o', linestyle='-', markersize=4, linewidth=2,
                            label=violation_name)
        
        plt.title('Constraint Violations by Type Over Generations', fontsize=14)
        plt.xlabel('Generation', fontsize=12)
        plt.ylabel('Number of Violations', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # Save or show plot
        if output_path:
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            plt.close()
        else:
            plt.tight_layout()
            plt.show()
    except Exception as e:
        print(f"Error generating plots: {str(e)}")


def plot_pareto_front(metrics, save_dir='.'):
    """
    Plot the Pareto front size over generations.
    
    Args:
        metrics: Dictionary containing tracked metrics
        save_dir: Directory to save the plots
    """
    if not PLOTTING_AVAILABLE:
        print(PLOTTING_ERROR_MSG)
        return
        
    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    if not metrics['pareto_front_size']:
        print("No Pareto front data available for plotting.")
        return
    
    x = range(len(metrics['pareto_front_size']))
    
    plt.figure(figsize=(10, 6))
    plt.plot(x, metrics['pareto_front_size'], 'b-o', markersize=4, linewidth=2)
    
    plt.title('Pareto Front Size Over Generations', fontsize=14)
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Number of Solutions in Pareto Front', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(f'{save_dir}/pareto_front_size.png', dpi=300)
    plt.close()
    
    print(f"Pareto front size plot saved to {save_dir}/pareto_front_size.png")


def plot_hypervolume(metrics, save_dir='.'):
    """
    Plot the hypervolume indicator over generations.
    
    Args:
        metrics: Dictionary containing tracked metrics
        save_dir: Directory to save the plots
    """
    if not PLOTTING_AVAILABLE:
        print(PLOTTING_ERROR_MSG)
        return
        
    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    if not metrics['hypervolume']:
        print("No hypervolume data available for plotting.")
        return
    
    x = range(len(metrics['hypervolume']))
    
    plt.figure(figsize=(10, 6))
    plt.plot(x, metrics['hypervolume'], 'g-o', markersize=4, linewidth=2)
    
    plt.title('Hypervolume Over Generations', fontsize=14)
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Hypervolume', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(f'{save_dir}/hypervolume.png', dpi=300)
    plt.close()
    
    print(f"Hypervolume plot saved to {save_dir}/hypervolume.png")


def plot_spacing(metrics, save_dir='.'):
    """
    Plot the spacing metric over generations.
    
    Args:
        metrics: Dictionary containing tracked metrics
        save_dir: Directory to save the plots
    """
    if not PLOTTING_AVAILABLE:
        print(PLOTTING_ERROR_MSG)
        return
        
    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    if not metrics['spacing']:
        print("No spacing data available for plotting.")
        return
    
    x = range(len(metrics['spacing']))
    
    plt.figure(figsize=(10, 6))
    plt.plot(x, metrics['spacing'], 'm-o', markersize=4, linewidth=2)
    
    plt.title('Spacing Over Generations', fontsize=14)
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Spacing', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(f'{save_dir}/spacing.png', dpi=300)
    plt.close()
    
    print(f"Spacing plot saved to {save_dir}/spacing.png")


def plot_igd(metrics, save_dir='.'):
    """
    Plot the IGD metric over generations.
    
    Args:
        metrics: Dictionary containing tracked metrics
        save_dir: Directory to save the plots
    """
    if not PLOTTING_AVAILABLE:
        print(PLOTTING_ERROR_MSG)
        return
        
    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    if not metrics['igd']:
        print("No IGD data available for plotting.")
        return
    
    x = range(len(metrics['igd']))
    
    plt.figure(figsize=(10, 6))
    plt.plot(x, metrics['igd'], 'c-o', markersize=4, linewidth=2)
    
    plt.title('Inverted Generational Distance Over Generations', fontsize=14)
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('IGD', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(f'{save_dir}/igd.png', dpi=300)
    plt.close()
    
    print(f"IGD plot saved to {save_dir}/igd.png")


def plot_execution_time(metrics, save_dir='.'):
    """
    Plot the execution time over generations.
    
    Args:
        metrics: Dictionary containing tracked metrics
        save_dir: Directory to save the plots
    """
    if not PLOTTING_AVAILABLE:
        print(PLOTTING_ERROR_MSG)
        return
        
    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    if not metrics['execution_time']:
        print("No execution time data available for plotting.")
        return
    
    x = range(len(metrics['execution_time']))
    
    plt.figure(figsize=(10, 6))
    # Plot total time
    plt.plot(x, metrics['execution_time'], 'k-o', markersize=4, linewidth=2)
    
    plt.title('Execution Time Over Generations', fontsize=14)
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Time (seconds)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(f'{save_dir}/execution_time.png', dpi=300)
    plt.close()
    
    print(f"Execution time plot saved to {save_dir}/execution_time.png")


def plot_all_metrics(metrics, save_dir='plots'):
    """
    Generate all plots for the metrics.
    
    Args:
        metrics: Dictionary containing tracked metrics
        save_dir: Directory to save the plots
    """
    if not PLOTTING_AVAILABLE:
        print("\nWarning: Plotting functionality is disabled because matplotlib and/or numpy are not installed.")
        print("To enable plotting, install the required dependencies:")
        print("    pip install -r requirements.txt")
        print("\nMetrics data is still being collected and can be plotted later when dependencies are installed.")
        return
    
    # Generate comprehensive metrics dashboard
    plot_metrics_dashboard(metrics, save_dir)
    
    # Individual plots
    plot_convergence(metrics, save_dir)
    plot_constraint_violations_by_type(metrics, f'{save_dir}/constraint_violations.png')
    plot_pareto_front(metrics, save_dir)
    plot_hypervolume(metrics, save_dir)
    plot_spacing(metrics, save_dir)
    plot_igd(metrics, save_dir)
    plot_execution_time(metrics, save_dir)


def plot_metrics_dashboard(metrics, save_dir='.'):
    """
    Plot a comprehensive dashboard of all optimization metrics.
    
    Args:
        metrics: Dictionary containing tracked metrics
        save_dir: Directory to save the plots
    """
    if not PLOTTING_AVAILABLE:
        print(PLOTTING_ERROR_MSG)
        return
        
    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    # Setup figure
    plt.figure(figsize=(20, 16))
    
    # Plot sections of the dashboard
    _plot_dashboard_hard_constraints(plt.subplot(3, 2, 1), metrics)
    _plot_dashboard_soft_constraints(plt.subplot(3, 2, 2), metrics)
    _plot_dashboard_violations_by_type(plt.subplot(3, 2, 3), metrics)
    _plot_dashboard_pareto_size(plt.subplot(3, 2, 4), metrics)
    _plot_dashboard_performance_metrics(plt.subplot(3, 2, 5), metrics)
    _plot_dashboard_execution_time(plt.subplot(3, 2, 6), metrics)
    
    plt.tight_layout()
    plt.savefig(f'{save_dir}/metrics_dashboard.png', dpi=300)
    plt.close()
    
    print(f"Metrics dashboard saved to {save_dir}/metrics_dashboard.png")

def _plot_dashboard_hard_constraints(ax, metrics):
    """Helper function to plot hard constraint violations on dashboard"""
    if metrics['best_hard_violations']:
        x = range(len(metrics['best_hard_violations']))
        ax.plot(x, metrics['best_hard_violations'], 'b-', label=LABEL_BEST_SOLUTION, linewidth=2)
        ax.plot(x, metrics['average_hard_violations'], 'r--', label=LABEL_POPULATION_AVG)
        ax.set_title('Hard Constraint Violations', fontsize=14)
        ax.set_xlabel('Generation', fontsize=12)
        ax.set_ylabel('Violations', fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
    else:
        ax.text(0.5, 0.5, LABEL_NO_DATA, 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14)

def _plot_dashboard_soft_constraints(ax, metrics):
    """Helper function to plot soft constraint scores on dashboard"""
    if metrics['best_soft_score']:
        x = range(len(metrics['best_soft_score']))
        ax.plot(x, metrics['best_soft_score'], 'g-', label=LABEL_BEST_SOLUTION, linewidth=2)
        ax.plot(x, metrics['average_soft_score'], 'm--', label=LABEL_POPULATION_AVG)
        ax.set_title('Soft Constraint Score', fontsize=14)
        ax.set_xlabel('Generation', fontsize=12)
        ax.set_ylabel('Score', fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
    else:
        ax.text(0.5, 0.5, LABEL_NO_DATA, 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14)

def _plot_dashboard_violations_by_type(ax, metrics):
    """Helper function to plot constraint violations by type on dashboard"""
    if metrics['constraint_violations']:
        try:
            # constraint_violations now contains tuples of (hard_violations, soft_violations)
            hard_violations, _ = metrics['constraint_violations'][0]
            
            if isinstance(hard_violations, dict):
                violation_types = list(hard_violations.keys())
                if 'total' in violation_types:
                    violation_types.remove('total')
                
                x = range(len(metrics['constraint_violations']))
                
                for violation_type in violation_types:
                    values = [v[0][violation_type] for v in metrics['constraint_violations']]
                    ax.plot(x, values, marker='o', linestyle='-', markersize=3, linewidth=1.5,
                            label=violation_type.replace('_', ' ').title())
            else:
                # If hard_violations is a tuple, plot each index separately
                violation_names = ["Room Capacity", "Room Availability", "Lecturer Availability", 
                                  "Group Availability", "Consecutive Sessions"]
                
                x = range(len(metrics['constraint_violations']))
                
                for i, violation_name in enumerate(violation_names):
                    if i < len(hard_violations):  # Make sure we don't go out of bounds
                        values = [v[0][i] if i < len(v[0]) else 0 for v in metrics['constraint_violations']]
                        ax.plot(x, values, marker='o', linestyle='-', markersize=3, linewidth=1.5,
                                label=violation_name)
            
            ax.set_title('Constraint Violations by Type', fontsize=14)
            ax.set_xlabel('Generation', fontsize=12)
            ax.set_ylabel('Count', fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.4)
            ax.legend(loc='upper right', fontsize=8)
        except Exception as e:
            print(f"Error generating violation plots: {str(e)}")
            ax.text(0.5, 0.5, f"Error: {str(e)}", 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes, fontsize=10)
    else:
        ax.text(0.5, 0.5, LABEL_NO_DATA, 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14)

def _plot_dashboard_pareto_size(ax, metrics):
    """Helper function to plot Pareto front size on dashboard"""
    if metrics['pareto_front_size']:
        x = range(len(metrics['pareto_front_size']))
        ax.plot(x, metrics['pareto_front_size'], 'b-o', markersize=3, linewidth=1.5)
        ax.set_title('Pareto Front Size', fontsize=14)
        ax.set_xlabel('Generation', fontsize=12)
        ax.set_ylabel('Count', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
    else:
        ax.text(0.5, 0.5, LABEL_NO_DATA, 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14)

def _plot_dashboard_performance_metrics(ax, metrics):
    """Helper function to plot performance metrics on dashboard"""
    # Determine which metrics to plot
    available_metrics = []
    if metrics['hypervolume']: available_metrics.append(('hypervolume', 'Hypervolume', 'g-'))
    if metrics['spacing']: available_metrics.append(('spacing', 'Spacing', 'm-'))
    if metrics['igd']: available_metrics.append(('igd', 'IGD', 'c-'))
    
    if available_metrics:
        for metric_key, metric_name, style in available_metrics:
            # Normalize to [0, 1] for comparison
            values = metrics[metric_key]
            if values:
                min_val = min(values)
                max_val = max(values)
                if max_val > min_val:
                    normalized = [(v - min_val) / (max_val - min_val) for v in values]
                else:
                    normalized = [0.5 for _ in values]  # If all values are the same
                
                x = range(len(values))
                ax.plot(x, normalized, style, linewidth=1.5, label=metric_name)
        
        ax.set_title('Performance Metrics (Normalized)', fontsize=14)
        ax.set_xlabel('Generation', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
    else:
        ax.text(0.5, 0.5, LABEL_NO_DATA, 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14)

def _plot_dashboard_execution_time(ax, metrics):
    """Helper function to plot execution time on dashboard"""
    if metrics['execution_time']:
        x = range(len(metrics['execution_time']))
        ax.plot(x, metrics['execution_time'], 'k-', linewidth=1.5)
        ax.set_title('Execution Time', fontsize=14)
        ax.set_xlabel('Generation', fontsize=12)
        ax.set_ylabel('Time (seconds)', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
    else:
        ax.text(0.5, 0.5, LABEL_NO_DATA, 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14)
