"""
Training Progress Monitor for DQN Sessions
Real-time monitoring of training progress and results
"""
import os
import json
import glob
import time
from datetime import datetime
import matplotlib.pyplot as plt

def find_latest_results():
    """Find the most recent training results"""
    # Look for both regular and enhanced results
    patterns = [
        "dqn_sta83_results_*",
        "enhanced_dqn_results_*"
    ]
    
    all_dirs = []
    for pattern in patterns:
        dirs = glob.glob(pattern)
        all_dirs.extend(dirs)
    
    if not all_dirs:
        return None
    
    # Sort by modification time
    all_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return all_dirs[0]

def load_training_progress(results_dir):
    """Load training progress from results directory"""
    try:
        # Try enhanced results first
        enhanced_path = os.path.join(results_dir, "enhanced_training_results.json")
        if os.path.exists(enhanced_path):
            with open(enhanced_path, 'r') as f:
                return json.load(f), "enhanced"
        
        # Try regular results
        regular_path = os.path.join(results_dir, "training_results.json")
        if os.path.exists(regular_path):
            with open(regular_path, 'r') as f:
                return json.load(f), "regular"
        
        return None, None
    except Exception as e:
        print(f"Error loading results: {e}")
        return None, None

def display_current_status():
    """Display current training status"""
    print("🔍 DQN Training Progress Monitor")
    print("="*50)
    
    # Find latest results
    latest_dir = find_latest_results()
    if not latest_dir:
        print(" No training results found")
        print("   Start training with: python train_dqn_sta83.py")
        return
    
    print(f"📁 Latest results: {latest_dir}")
    
    # Load progress
    results, result_type = load_training_progress(latest_dir)
    if not results:
        print("⚠ No progress data available yet")
        return
    
    # Display progress based on type
    if result_type == "enhanced":
        display_enhanced_progress(results, latest_dir)
    else:
        display_regular_progress(results, latest_dir)

def display_enhanced_progress(results, results_dir):
    """Display enhanced training progress"""
    print(f"\n Enhanced Training Progress")
    print(f"-" * 30)
    
    training_stats = results.get('training_stats', {})
    
    # Overall progress
    total_episodes = results.get('total_episodes', 0)
    final_success_rate = results.get('final_success_rate', 0)
    target_achieved = results.get('target_achieved', False)
    
    print(f"Total Episodes: {total_episodes}")
    print(f"Final Success Rate: {final_success_rate:.3f}")
    print(f"Target (80%) Achieved: {' YES' if target_achieved else ' NO'}")
    
    # Phase progress
    phase_transitions = training_stats.get('phase_transitions', [])
    if phase_transitions:
        print(f"\n Phase Progress:")
        for phase in phase_transitions:
            status = "" if phase['success_rate'] >= phase['target_rate'] else "⚠"
            print(f"   {status} {phase['phase'].title()}: {phase['success_rate']:.3f} "
                  f"(target: {phase['target_rate']:.3f})")
    
    # Best solutions
    best_solutions = training_stats.get('best_solutions', [])
    if best_solutions:
        best_sol = min(best_solutions, key=lambda x: x['timeslots'])
        print(f"\n Best Solution Found:")
        print(f"   Timeslots: {best_sol['timeslots']}")
        print(f"   Episode: {best_sol['episode']}")
        print(f"   Phase: {best_sol['phase']}")
        print(f"   Proximity Penalty: {best_sol['proximity_penalty']:.2f}")
    
    # Evaluation results
    eval_stats = results.get('evaluation_stats', {})
    if eval_stats:
        print(f"\n🔍 Final Evaluation:")
        print(f"   Success Rate: {eval_stats.get('success_rate', 0):.3f}")
        if eval_stats.get('solutions'):
            print(f"   Avg Timeslots: {eval_stats.get('avg_timeslots', 0):.1f}")
            print(f"   Avg Proximity Penalty: {eval_stats.get('avg_proximity_penalty', 0):.2f}")

def display_regular_progress(results, results_dir):
    """Display regular training progress"""
    print(f"\n Regular Training Progress")
    print(f"-" * 30)
    
    # Basic stats
    episode_rewards = results.get('episode_rewards', [])
    success_rate = results.get('success_rate', 0)
    successful_episodes = results.get('successful_episodes', 0)
    
    total_episodes = len(episode_rewards)
    
    print(f"Total Episodes: {total_episodes}")
    print(f"Successful Episodes: {successful_episodes}")
    print(f"Success Rate: {success_rate:.3f}")
    print(f"Target (80%) Achieved: {' YES' if success_rate >= 0.8 else ' NO'}")
    
    # Recent performance
    if len(episode_rewards) >= 100:
        recent_rewards = episode_rewards[-100:]
        recent_successes = sum(1 for r in recent_rewards if r > 0)
        recent_success_rate = recent_successes / 100
        print(f"Recent Success Rate (last 100): {recent_success_rate:.3f}")
    
    # Best solution
    best_solution = results.get('best_solution')
    if best_solution:
        print(f"\n Best Solution:")
        print(f"   Timeslots: {best_solution.get('timeslots_used', 'N/A')}")
        print(f"   Proximity Penalty: {best_solution.get('avg_proximity_penalty', 'N/A'):.2f}")

def monitor_live_training(check_interval=30):
    """Monitor training progress in real-time"""
    print("🔄 Live Training Monitor (Ctrl+C to stop)")
    print("="*50)
    
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
            
            print(f"🕒 Last updated: {datetime.now().strftime('%H:%M:%S')}")
            display_current_status()
            
            print(f"\n⏱ Next update in {check_interval} seconds...")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print(f"\n👋 Monitoring stopped")

def create_quick_plot():
    """Create a quick plot of current progress"""
    latest_dir = find_latest_results()
    if not latest_dir:
        print(" No results to plot")
        return
    
    results, result_type = load_training_progress(latest_dir)
    if not results:
        print(" No data to plot")
        return
    
    plt.figure(figsize=(15, 10))
    
    if result_type == "enhanced":
        training_stats = results.get('training_stats', {})
        
        # Success rate over time
        plt.subplot(2, 2, 1)
        success_rates = training_stats.get('success_rates', [])
        if success_rates:
            plt.plot(success_rates, color='green', linewidth=2)
            plt.axhline(y=0.8, color='red', linestyle='--', label='Target (80%)')
            plt.title('Success Rate Over Time')
            plt.xlabel('Episode')
            plt.ylabel('Rolling Success Rate')
            plt.legend()
            plt.grid(True, alpha=0.3)
        
        # Episode rewards
        plt.subplot(2, 2, 2)
        episode_rewards = training_stats.get('episode_rewards', [])
        if episode_rewards:
            plt.plot(episode_rewards, alpha=0.6, color='blue')
            plt.title('Episode Rewards')
            plt.xlabel('Episode')
            plt.ylabel('Reward')
            plt.grid(True, alpha=0.3)
        
        # Phase progress
        plt.subplot(2, 2, 3)
        phase_transitions = training_stats.get('phase_transitions', [])
        if phase_transitions:
            phases = [p['phase'] for p in phase_transitions]
            rates = [p['success_rate'] for p in phase_transitions]
            targets = [p['target_rate'] for p in phase_transitions]
            
            x = range(len(phases))
            plt.bar(x, rates, alpha=0.7, label='Achieved', color='lightblue')
            plt.bar(x, targets, alpha=0.5, label='Target', color='red')
            plt.xticks(x, phases)
            plt.title('Phase Success Rates')
            plt.ylabel('Success Rate')
            plt.legend()
            plt.grid(True, alpha=0.3)
        
        # Best solutions
        plt.subplot(2, 2, 4)
        best_solutions = training_stats.get('best_solutions', [])
        if best_solutions:
            episodes = [s['episode'] for s in best_solutions]
            timeslots = [s['timeslots'] for s in best_solutions]
            plt.scatter(episodes, timeslots, alpha=0.7, color='green')
            plt.title('Best Solutions Over Time')
            plt.xlabel('Episode')
            plt.ylabel('Timeslots Used')
            plt.grid(True, alpha=0.3)
    
    else:
        # Regular training plots
        episode_rewards = results.get('episode_rewards', [])
        if episode_rewards:
            plt.subplot(2, 1, 1)
            plt.plot(episode_rewards, alpha=0.6)
            plt.title('Episode Rewards')
            plt.xlabel('Episode')
            plt.ylabel('Reward')
            plt.grid(True, alpha=0.3)
            
            # Success rate calculation
            plt.subplot(2, 1, 2)
            window_size = 100
            if len(episode_rewards) >= window_size:
                success_indicators = [1 if r > 0 else 0 for r in episode_rewards]
                rolling_rates = []
                for i in range(window_size, len(success_indicators)):
                    rate = sum(success_indicators[i-window_size:i]) / window_size
                    rolling_rates.append(rate)
                
                plt.plot(range(window_size, len(episode_rewards)), rolling_rates, color='green')
                plt.axhline(y=0.8, color='red', linestyle='--', label='Target (80%)')
                plt.title('Rolling Success Rate')
                plt.xlabel('Episode')
                plt.ylabel('Success Rate')
                plt.legend()
                plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    plot_path = os.path.join(latest_dir, "current_progress.png")
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f" Progress plot saved to {plot_path}")
    plt.show()

def main():
    """Main monitoring interface"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "live":
            monitor_live_training()
        elif sys.argv[1] == "plot":
            create_quick_plot()
        else:
            print("Usage: python monitor_training.py [live|plot]")
    else:
        display_current_status()

if __name__ == "__main__":
    main() 