"""
Optimized DQN Training Script with Recommended Fixes
- Increased timeslots (25-30) to avoid "no valid actions"
- Early stopping at 80% success rate
- Enhanced monitoring and performance tracking
- Optimized hyperparameters for faster convergence
"""
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List, Optional
import time

from environment import ExamTimetablingEnv
from agent import DQNAgent

class OptimizedDQNTrainer:
    """Enhanced DQN trainer with performance optimizations"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.results_dir = self.create_results_directory()
        self.training_start_time = None
        
    def create_results_directory(self) -> str:
        """Create timestamped results directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = f"optimized_dqn_results_{timestamp}"
        os.makedirs(results_dir, exist_ok=True)
        print(f"📁 Results directory: {results_dir}")
        return results_dir
    
    def setup_environment_and_agent(self):
        """Setup environment and agent with optimized parameters"""
        print(f"\n🏗 Setting up environment with {self.config['max_timeslots']} timeslots...")
        
        # Create environment with increased timeslots
        self.env = ExamTimetablingEnv(
            max_timeslots=self.config['max_timeslots'],
            data_path=self.config['data_path']
        )
        
        print(f" Environment: {self.env.num_exams} exams, {self.env.num_students} students")
        print(f"   State size: {self.env.observation_space.shape[0]}, Action size: {self.env.action_space.n}")
        
        # Create optimized DQN agent
        state_size = self.env.observation_space.shape[0]
        action_size = self.env.action_space.n
        
        self.agent = DQNAgent(
            state_size=state_size,
            action_size=action_size,
            learning_rate=self.config['learning_rate'],
            gamma=self.config['gamma'],
            epsilon_start=self.config['epsilon_start'],
            epsilon_end=self.config['epsilon_end'],
            epsilon_decay=self.config['epsilon_decay'],
            buffer_size=self.config['buffer_size'],
            batch_size=self.config['batch_size'],
            target_update_freq=self.config['target_update_freq']
        )
        
        print(f" DQN Agent optimized for fast convergence")
        print(f"   Learning rate: {self.config['learning_rate']}")
        print(f"   Buffer size: {self.config['buffer_size']}")
        print(f"   Target update frequency: {self.config['target_update_freq']}")
    
    def train_with_early_stopping(self) -> Dict:
        """Train with early stopping when target success rate is reached"""
        print(f"\n Starting optimized training...")
        print(f"   Target success rate: {self.config['target_success_rate']}%")
        print(f"   Max episodes: {self.config['max_episodes']}")
        print(f"   Early stopping enabled: {self.config['early_stopping']}")
        
        self.training_start_time = time.time()
        
        # Training metrics
        episode_rewards = []
        episode_lengths = []
        success_rates = []
        rolling_success_rates = []
        training_times = []
        
        successful_episodes = 0
        best_reward = -float('inf')
        best_solution = None
        
        # Rolling window for success rate calculation
        window_size = 100
        recent_successes = []
        
        # Initialize variables for proper scope
        overall_success_rate = 0.0
        rolling_success_rate = 0.0
        episode = 0
        
        for episode in range(self.config['max_episodes']):
            episode_start_time = time.time()
            
            # Run episode
            state = self.env.reset()
            episode_reward = 0
            episode_length = 0
            
            for step in range(self.env.num_exams):
                # Get valid actions
                valid_actions = self.env.get_valid_actions()
                
                if not valid_actions:
                    print(f"⚠  No valid actions at step {step} - this should be rare with {self.config['max_timeslots']} timeslots")
                    break
                
                # Choose action
                action = self.agent.act(state, valid_actions)
                
                # Take step
                next_state, reward, done, info = self.env.step(action)
                
                # Store experience
                self.agent.remember(state, action, reward, next_state, done)
                
                # Train
                self.agent.replay()
                
                # Update state
                state = next_state
                episode_reward += reward
                episode_length += 1
                
                if done:
                    # Check if solution is valid
                    is_success = 'valid_solution' in info and info['valid_solution']
                    if is_success:
                        successful_episodes += 1
                        if episode_reward > best_reward:
                            best_reward = episode_reward
                            best_solution = self.env.get_solution_quality()
                    
                    # Update rolling success tracking
                    recent_successes.append(1 if is_success else 0)
                    if len(recent_successes) > window_size:
                        recent_successes.pop(0)
                    
                    break
            
            # Record metrics
            episode_time = time.time() - episode_start_time
            episode_rewards.append(episode_reward)
            episode_lengths.append(episode_length)
            training_times.append(episode_time)
            
            # Calculate success rates
            overall_success_rate = successful_episodes / (episode + 1)
            rolling_success_rate = np.mean(recent_successes) if recent_successes else 0
            
            success_rates.append(overall_success_rate)
            rolling_success_rates.append(rolling_success_rate)
            
            # Progress reporting
            if (episode + 1) % 50 == 0:
                elapsed_time = time.time() - self.training_start_time
                avg_episode_time = np.mean(training_times[-50:])
                
                print(f"\n Episode {episode + 1}/{self.config['max_episodes']}")
                print(f"   Overall Success Rate: {overall_success_rate:.3f} ({overall_success_rate*100:.1f}%)")
                print(f"   Rolling Success Rate: {rolling_success_rate:.3f} ({rolling_success_rate*100:.1f}%)")
                print(f"   Avg Reward (last 50): {np.mean(episode_rewards[-50:]):.2f}")
                print(f"   Avg Episode Time: {avg_episode_time:.3f}s")
                print(f"   Total Time: {elapsed_time/60:.1f} min")
                print(f"   Epsilon: {self.agent.epsilon:.4f}")
                print(f"   Buffer Size: {len(self.agent.replay_buffer)}")
                
                if best_solution:
                    print(f"   Best Solution: {best_solution['timeslots_used']} slots, "
                          f"{best_solution['avg_proximity_penalty']:.2f} avg penalty")
            
            # Early stopping check
            if (self.config['early_stopping'] and 
                len(recent_successes) >= window_size and 
                rolling_success_rate >= self.config['target_success_rate'] / 100):
                
                print(f"\n TARGET ACHIEVED!")
                print(f"   Rolling success rate: {rolling_success_rate:.3f} ({rolling_success_rate*100:.1f}%)")
                print(f"   Episodes completed: {episode + 1}")
                print(f"   Training time: {(time.time() - self.training_start_time)/60:.1f} minutes")
                break
        
        # Compile training statistics
        training_stats = {
            'episode_rewards': episode_rewards,
            'episode_lengths': episode_lengths,
            'success_rates': success_rates,
            'rolling_success_rates': rolling_success_rates,
            'training_times': training_times,
            'successful_episodes': successful_episodes,
            'final_success_rate': overall_success_rate,
            'final_rolling_success_rate': rolling_success_rate,
            'best_reward': best_reward,
            'best_solution': best_solution,
            'total_episodes': episode + 1,
            'total_training_time': time.time() - self.training_start_time,
            'target_achieved': rolling_success_rate >= self.config['target_success_rate'] / 100
        }
        
        return training_stats
    
    def evaluate_performance(self, num_eval_episodes: int = 20) -> Dict:
        """Comprehensive evaluation of trained agent"""
        print(f"\n🔍 Evaluating trained agent ({num_eval_episodes} episodes)...")
        
        # Disable exploration for evaluation
        original_epsilon = self.agent.epsilon
        self.agent.epsilon = 0.0
        
        eval_results = []
        eval_times = []
        
        for episode in range(num_eval_episodes):
            eval_start_time = time.time()
            
            state = self.env.reset()
            episode_reward = 0
            
            for step in range(self.env.num_exams):
                valid_actions = self.env.get_valid_actions()
                action = self.agent.act(state, valid_actions)
                state, reward, done, info = self.env.step(action)
                episode_reward += reward
                
                if done:
                    eval_time = time.time() - eval_start_time
                    eval_times.append(eval_time)
                    
                    if 'valid_solution' in info and info['valid_solution']:
                        solution = self.env.get_solution_quality()
                        eval_results.append({
                            'success': True,
                            'reward': episode_reward,
                            'time': eval_time,
                            'timeslots_used': solution['timeslots_used'],
                            'avg_proximity_penalty': solution['avg_proximity_penalty']
                        })
                    else:
                        eval_results.append({
                            'success': False,
                            'reward': episode_reward,
                            'time': eval_time
                        })
                    break
        
        # Restore epsilon
        self.agent.epsilon = original_epsilon
        
        # Calculate evaluation statistics
        successful_evals = [r for r in eval_results if r['success']]
        eval_success_rate = len(successful_evals) / len(eval_results)
        
        eval_stats = {
            'success_rate': eval_success_rate,
            'avg_eval_time': np.mean(eval_times),
            'results': eval_results
        }
        
        if successful_evals:
            eval_stats.update({
                'avg_timeslots': np.mean([r['timeslots_used'] for r in successful_evals]),
                'avg_proximity_penalty': np.mean([r['avg_proximity_penalty'] for r in successful_evals]),
                'min_timeslots': min([r['timeslots_used'] for r in successful_evals]),
                'max_timeslots': max([r['timeslots_used'] for r in successful_evals])
            })
        
        print(f" Evaluation Results:")
        print(f"   Success Rate: {eval_success_rate:.3f} ({eval_success_rate*100:.1f}%)")
        print(f"   Avg Evaluation Time: {eval_stats['avg_eval_time']:.3f}s")
        
        if successful_evals:
            print(f"   Avg Timeslots Used: {eval_stats['avg_timeslots']:.1f}")
            print(f"   Timeslot Range: {eval_stats['min_timeslots']}-{eval_stats['max_timeslots']}")
            print(f"   Avg Proximity Penalty: {eval_stats['avg_proximity_penalty']:.2f}")
        
        return eval_stats
    
    def save_results(self, training_stats: Dict, eval_stats: Dict):
        """Save comprehensive results"""
        # Save configuration
        config_path = os.path.join(self.results_dir, "config.json")
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        # Save training results
        results = {
            'config': self.config,
            'training_stats': training_stats,
            'eval_stats': eval_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        # Convert numpy arrays to lists for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.integer, np.floating)):
                return obj.item()
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            return obj
        
        results = convert_numpy(results)
        
        results_path = os.path.join(self.results_dir, "results.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f" Results saved to {results_path}")
        
        # Save model
        model_path = os.path.join(self.results_dir, "optimized_dqn_model.pth")
        self.agent.save_model(model_path)
        print(f" Model saved to {model_path}")
    
    def create_performance_plots(self, training_stats: Dict, eval_stats: Dict):
        """Create comprehensive performance visualization"""
        fig = plt.figure(figsize=(20, 12))
        
        # Success rate progression
        plt.subplot(2, 4, 1)
        episodes = range(1, len(training_stats['success_rates']) + 1)
        plt.plot(episodes, [r * 100 for r in training_stats['success_rates']], 
                label='Overall Success Rate', alpha=0.7)
        plt.plot(episodes, [r * 100 for r in training_stats['rolling_success_rates']], 
                label='Rolling Success Rate (100 episodes)', linewidth=2)
        plt.axhline(y=self.config['target_success_rate'], color='red', linestyle='--', 
                   label=f'Target ({self.config["target_success_rate"]}%)')
        plt.title('Success Rate Progression')
        plt.xlabel('Episode')
        plt.ylabel('Success Rate (%)')
        plt.legend()
        plt.grid(True)
        
        # Episode rewards
        plt.subplot(2, 4, 2)
        plt.plot(training_stats['episode_rewards'], alpha=0.7)
        plt.title('Episode Rewards')
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        plt.grid(True)
        
        # Episode lengths
        plt.subplot(2, 4, 3)
        plt.plot(training_stats['episode_lengths'], alpha=0.7)
        plt.title('Episode Lengths')
        plt.xlabel('Episode')
        plt.ylabel('Steps')
        plt.grid(True)
        
        # Training times
        plt.subplot(2, 4, 4)
        plt.plot(training_stats['training_times'], alpha=0.7)
        plt.title('Episode Training Times')
        plt.xlabel('Episode')
        plt.ylabel('Time (seconds)')
        plt.grid(True)
        
        # Evaluation results
        if eval_stats['results']:
            successful_evals = [r for r in eval_stats['results'] if r['success']]
            
            if successful_evals:
                plt.subplot(2, 4, 5)
                timeslots = [r['timeslots_used'] for r in successful_evals]
                plt.hist(timeslots, bins=10, alpha=0.7, edgecolor='black')
                plt.title('Timeslots Used (Evaluation)')
                plt.xlabel('Timeslots')
                plt.ylabel('Frequency')
                plt.grid(True)
                
                plt.subplot(2, 4, 6)
                penalties = [r['avg_proximity_penalty'] for r in successful_evals]
                plt.hist(penalties, bins=10, alpha=0.7, edgecolor='black')
                plt.title('Proximity Penalties (Evaluation)')
                plt.xlabel('Average Proximity Penalty')
                plt.ylabel('Frequency')
                plt.grid(True)
                
                plt.subplot(2, 4, 7)
                eval_times = [r['time'] for r in successful_evals]
                plt.hist(eval_times, bins=10, alpha=0.7, edgecolor='black')
                plt.title('Evaluation Times')
                plt.xlabel('Time (seconds)')
                plt.ylabel('Frequency')
                plt.grid(True)
        
        # Performance summary
        plt.subplot(2, 4, 8)
        plt.text(0.1, 0.9, f"Final Success Rate: {training_stats['final_rolling_success_rate']*100:.1f}%", 
                transform=plt.gca().transAxes, fontsize=12, fontweight='bold')
        plt.text(0.1, 0.8, f"Episodes: {training_stats['total_episodes']}", 
                transform=plt.gca().transAxes, fontsize=10)
        plt.text(0.1, 0.7, f"Training Time: {training_stats['total_training_time']/60:.1f} min", 
                transform=plt.gca().transAxes, fontsize=10)
        plt.text(0.1, 0.6, f"Target Achieved: {'' if training_stats['target_achieved'] else ''}", 
                transform=plt.gca().transAxes, fontsize=10)
        
        if eval_stats.get('avg_timeslots'):
            plt.text(0.1, 0.5, f"Avg Timeslots: {eval_stats['avg_timeslots']:.1f}", 
                    transform=plt.gca().transAxes, fontsize=10)
            plt.text(0.1, 0.4, f"Avg Penalty: {eval_stats['avg_proximity_penalty']:.2f}", 
                    transform=plt.gca().transAxes, fontsize=10)
        
        plt.text(0.1, 0.3, f"Eval Success: {eval_stats['success_rate']*100:.1f}%", 
                transform=plt.gca().transAxes, fontsize=10)
        plt.text(0.1, 0.2, f"Avg Eval Time: {eval_stats['avg_eval_time']:.3f}s", 
                transform=plt.gca().transAxes, fontsize=10)
        
        plt.title('Performance Summary')
        plt.axis('off')
        
        plt.tight_layout()
        
        # Save plot
        plot_path = os.path.join(self.results_dir, "performance_analysis.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f" Performance analysis saved to {plot_path}")
        plt.show()

def run_optimized_training():
    """Run optimized DQN training with recommended fixes"""
    
    # Optimized configuration with recommended fixes
    config = {
        # Environment settings
        'max_timeslots': 28,  # Increased from 18 to avoid "no valid actions"
        'data_path': 'data/',
        
        # Training settings
        'max_episodes': 2000,
        'target_success_rate': 80,  # Target 80% success rate
        'early_stopping': True,
        
        # DQN hyperparameters (optimized for faster convergence)
        'learning_rate': 0.0003,  # Slightly lower for stability
        'gamma': 0.99,
        'epsilon_start': 0.9,     # Start with more exploration
        'epsilon_end': 0.01,
        'epsilon_decay': 0.9995,  # Slower decay for better exploration
        'buffer_size': 20000,     # Larger buffer for better experience replay
        'batch_size': 64,         # Larger batch for more stable learning
        'target_update_freq': 50, # More frequent target updates
        
        # Evaluation settings
        'eval_episodes': 25
    }
    
    print(" Optimized DQN Training with Recommended Fixes")
    print("=" * 60)
    print(f" Key Improvements:")
    print(f"   • Increased timeslots: {config['max_timeslots']} (was 18)")
    print(f"   • Target success rate: {config['target_success_rate']}%")
    print(f"   • Early stopping enabled")
    print(f"   • Optimized hyperparameters for faster convergence")
    print(f"   • Enhanced monitoring and visualization")
    
    # Create trainer and run experiment
    trainer = OptimizedDQNTrainer(config)
    trainer.setup_environment_and_agent()
    
    # Train with early stopping
    training_stats = trainer.train_with_early_stopping()
    
    # Evaluate performance
    eval_stats = trainer.evaluate_performance(config['eval_episodes'])
    
    # Save results and create visualizations
    trainer.save_results(training_stats, eval_stats)
    trainer.create_performance_plots(training_stats, eval_stats)
    
    # Print final summary
    print(f"\n TRAINING COMPLETE!")
    print(f"=" * 60)
    print(f" Final Rolling Success Rate: {training_stats['final_rolling_success_rate']*100:.1f}%")
    print(f" Evaluation Success Rate: {eval_stats['success_rate']*100:.1f}%")
    print(f"⏱  Total Training Time: {training_stats['total_training_time']/60:.1f} minutes")
    print(f" Episodes Completed: {training_stats['total_episodes']}")
    print(f" Target Achieved: {'YES' if training_stats['target_achieved'] else 'NO'}")
    
    if eval_stats.get('avg_timeslots'):
        print(f" Average Timeslots Used: {eval_stats['avg_timeslots']:.1f}")
        print(f" Average Proximity Penalty: {eval_stats['avg_proximity_penalty']:.2f}")
    
    print(f" Results saved to: {trainer.results_dir}")
    
    return training_stats, eval_stats

if __name__ == "__main__":
    run_optimized_training() 