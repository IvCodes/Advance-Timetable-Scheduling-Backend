"""
SARSA Agent for STA83 Exam Timetabling
Implements SARSA with neural network function approximation (on-policy learning)
"""
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import random
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Optional
from app.exams.rl.sarsa_environment import ExamTimetablingSARSAEnv

class SARSANetwork(nn.Module):
    """
    Neural Network for SARSA Q-function approximation
    """
    
    def __init__(self, state_size: int, action_size: int, hidden_sizes: List[int] = [128, 64]):
        """
        Initialize the SARSA network
        
        Args:
            state_size: Size of the state space
            action_size: Size of the action space (number of timeslots)
            hidden_sizes: List of hidden layer sizes
        """
        super(SARSANetwork, self).__init__()
        
        self.state_size = state_size
        self.action_size = action_size
        
        # Build network layers
        layers = []
        prev_size = state_size
        
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            prev_size = hidden_size
        
        # Output layer
        layers.append(nn.Linear(prev_size, action_size))
        
        self.network = nn.Sequential(*layers)
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        """Initialize network weights"""
        if isinstance(module, nn.Linear):
            torch.nn.init.xavier_uniform_(module.weight)
            module.bias.data.fill_(0.01)
    
    def forward(self, state):
        """Forward pass through the network"""
        return self.network(state)

class SARSAAgent:
    """
    SARSA Agent for exam timetabling with neural network function approximation
    """
    
    def __init__(self, 
                 state_size: int,
                 action_size: int,
                 learning_rate: float = 0.001,
                 gamma: float = 0.99,
                 epsilon_start: float = 1.0,
                 epsilon_end: float = 0.01,
                 epsilon_decay: float = 0.995,
                 device: Optional[str] = None):
        """
        Initialize SARSA agent
        
        Args:
            state_size: Size of state space
            action_size: Size of action space
            learning_rate: Learning rate for optimizer
            gamma: Discount factor
            epsilon_start: Initial exploration rate
            epsilon_end: Final exploration rate
            epsilon_decay: Exploration decay rate
            device: Device to run on (cuda/cpu)
        """
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        
        # Device setup
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        print(f"🧠 SARSA Agent using device: {self.device}")
        
        # Q-Network (no target network needed for SARSA)
        self.q_network = SARSANetwork(state_size, action_size).to(self.device)
        
        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Training metrics
        self.training_step = 0
        self.losses = []
        self.episode_rewards = []
        self.episode_lengths = []
        self.epsilon_history = []
        self.success_rate = []
        self.timeslots_used = []
        
        print(f"🎯 SARSA Agent initialized:")
        print(f"   🧠 Network: {state_size} → {action_size}")
        print(f"   📚 Learning rate: {learning_rate}")
        print(f"   🎲 Epsilon: {epsilon_start} → {epsilon_end}")
        print(f"   💾 Discount factor: {gamma}")
    
    def act(self, state: np.ndarray, valid_actions: Optional[List[int]] = None) -> int:
        """
        Choose action using epsilon-greedy policy with action masking
        
        Args:
            state: Current state
            valid_actions: List of valid actions (for action masking)
            
        Returns:
            Selected action
        """
        # Convert state to tensor
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        # Epsilon-greedy action selection
        if random.random() > self.epsilon:
            # Exploit: choose best action
            with torch.no_grad():
                q_values = self.q_network(state_tensor)
                
                # Apply action masking if valid actions provided
                if valid_actions is not None and len(valid_actions) > 0:
                    # Mask invalid actions with very negative values
                    masked_q_values = q_values.clone()
                    mask = torch.ones(self.action_size, dtype=torch.bool)
                    mask[valid_actions] = False
                    masked_q_values[0][mask] = -float('inf')
                    action = masked_q_values.argmax().item()
                else:
                    action = q_values.argmax().item()
        else:
            # Explore: choose random action
            if valid_actions is not None and len(valid_actions) > 0:
                action = random.choice(valid_actions)
            else:
                action = random.randint(0, self.action_size - 1)
        
        return action
    
    def update(self, state: np.ndarray, action: int, reward: float, 
               next_state: np.ndarray, next_action: int, done: bool):
        """
        Update Q-network using SARSA update rule
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            next_action: Next action (chosen by policy)
            done: Whether episode is done
        """
        # Convert to tensors
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
        reward_tensor = torch.FloatTensor([reward]).to(self.device)
        done_tensor = torch.BoolTensor([done]).to(self.device)
        
        # Current Q-value
        current_q = self.q_network(state_tensor)[0][action]
        
        # Next Q-value (key difference from DQN - use next_action, not max)
        with torch.no_grad():
            if done:
                next_q = torch.tensor(0.0).to(self.device)
            else:
                next_q = self.q_network(next_state_tensor)[0][next_action]
        
        # SARSA target: R + γ * Q(S', A')
        target_q = reward_tensor + (self.gamma * next_q * (~done_tensor))
        
        # Calculate loss (ensure same shape)
        loss = F.mse_loss(current_q.unsqueeze(0), target_q)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Record loss
        self.losses.append(loss.item())
        self.training_step += 1
        
        # Decay epsilon
        if self.epsilon > self.epsilon_end:
            self.epsilon *= self.epsilon_decay
    
    def train(self, env: ExamTimetablingSARSAEnv, num_episodes: int = 100, 
              max_steps_per_episode: Optional[int] = None, verbose: bool = True) -> Dict:
        """
        Train the SARSA agent
        
        Args:
            env: SARSA environment
            num_episodes: Number of episodes to train
            max_steps_per_episode: Maximum steps per episode
            verbose: Whether to print progress
            
        Returns:
            Training statistics
        """
        if verbose:
            print(f"\n🚀 Starting SARSA Training")
            print(f"   📊 Episodes: {num_episodes}")
            print(f"   🎯 Goal: Learn clash-free timetable construction")
        
        successful_episodes = 0
        
        for episode in range(num_episodes):
            # Reset environment
            state = env.reset()
            total_reward = 0
            episode_length = 0
            
            # Choose initial action
            valid_actions = env.get_valid_actions()
            action = self.act(state, valid_actions)
            
            # Episode loop
            while True:
                # Take action
                next_state, reward, done, info = env.step(action)
                total_reward += reward
                episode_length += 1
                
                if done:
                    # Terminal state - no next action needed
                    self.update(state, action, reward, next_state, 0, done)
                    
                    # Track success
                    if info.get('termination_reason') == 'success':
                        successful_episodes += 1
                        if 'total_timeslots' in info:
                            self.timeslots_used.append(info['total_timeslots'])
                    
                    break
                else:
                    # Choose next action using current policy
                    valid_next_actions = env.get_valid_actions()
                    next_action = self.act(next_state, valid_next_actions)
                    
                    # SARSA update
                    self.update(state, action, reward, next_state, next_action, done)
                    
                    # Move to next state-action pair
                    state = next_state
                    action = next_action
                
                # Check for max steps
                if max_steps_per_episode and episode_length >= max_steps_per_episode:
                    break
            
            # Record episode metrics
            self.episode_rewards.append(total_reward)
            self.episode_lengths.append(episode_length)
            self.epsilon_history.append(self.epsilon)
            
            # Calculate success rate over last 10 episodes
            recent_episodes = min(10, episode + 1)
            recent_success_rate = successful_episodes / (episode + 1) if episode < 10 else \
                                sum(1 for i in range(episode - 9, episode + 1) 
                                    if i < len(self.episode_rewards) and 
                                    self.episode_rewards[i] > 400) / 10  # Approximate success threshold
            self.success_rate.append(recent_success_rate)
            
            # Progress reporting
            if verbose and (episode + 1) % max(1, num_episodes // 10) == 0:
                avg_reward = np.mean(self.episode_rewards[-10:])
                avg_length = np.mean(self.episode_lengths[-10:])
                success_pct = recent_success_rate * 100
                
                print(f"   Episode {episode + 1:3d}/{num_episodes}: "
                      f"Reward {avg_reward:6.1f}, Length {avg_length:4.1f}, "
                      f"Success {success_pct:4.1f}%, ε {self.epsilon:.3f}")
        
        # Training summary
        final_success_rate = successful_episodes / num_episodes
        avg_final_reward = np.mean(self.episode_rewards[-10:]) if len(self.episode_rewards) >= 10 else np.mean(self.episode_rewards)
        
        if verbose:
            print(f"\n📊 Training Complete!")
            print(f"   ✅ Success rate: {final_success_rate:.1%}")
            print(f"   🏆 Avg final reward: {avg_final_reward:.1f}")
            print(f"   📈 Total training steps: {self.training_step}")
            if self.timeslots_used:
                print(f"   ⏰ Avg timeslots (successful): {np.mean(self.timeslots_used):.1f}")
        
        return {
            'success_rate': final_success_rate,
            'avg_reward': avg_final_reward,
            'total_episodes': num_episodes,
            'successful_episodes': successful_episodes,
            'training_steps': self.training_step,
            'avg_timeslots': np.mean(self.timeslots_used) if self.timeslots_used else None
        }
    
    def evaluate(self, env: ExamTimetablingSARSAEnv, num_episodes: int = 10) -> Dict:
        """
        Evaluate the trained SARSA agent
        
        Args:
            env: SARSA environment
            num_episodes: Number of evaluation episodes
            
        Returns:
            Evaluation statistics
        """
        print(f"\n🔍 Evaluating SARSA Agent ({num_episodes} episodes)")
        
        # Save current epsilon and set to 0 for evaluation (no exploration)
        original_epsilon = self.epsilon
        self.epsilon = 0.0
        
        successful_episodes = 0
        total_rewards = []
        episode_lengths = []
        timeslots_used = []
        proximity_penalties = []
        
        for episode in range(num_episodes):
            state = env.reset()
            total_reward = 0
            episode_length = 0
            
            while True:
                valid_actions = env.get_valid_actions()
                action = self.act(state, valid_actions)
                next_state, reward, done, info = env.step(action)
                
                total_reward += reward
                episode_length += 1
                state = next_state
                
                if done:
                    if info.get('termination_reason') == 'success':
                        successful_episodes += 1
                        if 'total_timeslots' in info:
                            timeslots_used.append(info['total_timeslots'])
                        if 'proximity_penalty' in info:
                            proximity_penalties.append(abs(info['proximity_penalty']))
                    break
            
            total_rewards.append(total_reward)
            episode_lengths.append(episode_length)
        
        # Restore original epsilon
        self.epsilon = original_epsilon
        
        # Calculate statistics
        success_rate = successful_episodes / num_episodes
        avg_reward = np.mean(total_rewards)
        avg_length = np.mean(episode_lengths)
        avg_timeslots = np.mean(timeslots_used) if timeslots_used else None
        avg_proximity = np.mean(proximity_penalties) if proximity_penalties else None
        
        print(f"   ✅ Success rate: {success_rate:.1%}")
        print(f"   🏆 Average reward: {avg_reward:.1f}")
        print(f"   📏 Average episode length: {avg_length:.1f}")
        if avg_timeslots:
            print(f"   ⏰ Average timeslots used: {avg_timeslots:.1f}")
        if avg_proximity:
            print(f"   📍 Average proximity penalty: {avg_proximity:.1f}")
        
        return {
            'success_rate': success_rate,
            'avg_reward': avg_reward,
            'avg_episode_length': avg_length,
            'successful_episodes': successful_episodes,
            'avg_timeslots': avg_timeslots,
            'avg_proximity_penalty': avg_proximity,
            'total_episodes': num_episodes
        }
    
    def plot_training_progress(self, save_path: Optional[str] = None):
        """Plot training progress"""
        if not self.episode_rewards:
            print("No training data to plot")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('SARSA Training Progress', fontsize=16)
        
        # Episode rewards
        axes[0, 0].plot(self.episode_rewards)
        axes[0, 0].set_title('Episode Rewards')
        axes[0, 0].set_xlabel('Episode')
        axes[0, 0].set_ylabel('Total Reward')
        axes[0, 0].grid(True)
        
        # Episode lengths
        axes[0, 1].plot(self.episode_lengths)
        axes[0, 1].set_title('Episode Lengths')
        axes[0, 1].set_xlabel('Episode')
        axes[0, 1].set_ylabel('Steps')
        axes[0, 1].grid(True)
        
        # Epsilon decay
        axes[1, 0].plot(self.epsilon_history)
        axes[1, 0].set_title('Epsilon Decay')
        axes[1, 0].set_xlabel('Episode')
        axes[1, 0].set_ylabel('Epsilon')
        axes[1, 0].grid(True)
        
        # Success rate
        if self.success_rate:
            axes[1, 1].plot(self.success_rate)
            axes[1, 1].set_title('Success Rate')
            axes[1, 1].set_xlabel('Episode')
            axes[1, 1].set_ylabel('Success Rate')
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Training plots saved to: {save_path}")
        
        plt.show()
    
    def save_model(self, filepath: str):
        """Save the trained model"""
        torch.save({
            'q_network_state_dict': self.q_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'training_step': self.training_step,
            'episode_rewards': self.episode_rewards,
            'episode_lengths': self.episode_lengths,
            'hyperparameters': {
                'state_size': self.state_size,
                'action_size': self.action_size,
                'learning_rate': self.learning_rate,
                'gamma': self.gamma,
                'epsilon_end': self.epsilon_end,
                'epsilon_decay': self.epsilon_decay
            }
        }, filepath)
        print(f"💾 SARSA model saved to: {filepath}")
    
    def load_model(self, filepath: str):
        """Load a trained model"""
        checkpoint = torch.load(filepath, map_location=self.device, weights_only=False)
        
        self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint['epsilon']
        self.training_step = checkpoint['training_step']
        self.episode_rewards = checkpoint.get('episode_rewards', [])
        self.episode_lengths = checkpoint.get('episode_lengths', [])
        
        print(f"📂 SARSA model loaded from: {filepath}")
        print(f"   Training steps: {self.training_step}")
        print(f"   Current epsilon: {self.epsilon:.4f}")

def test_sarsa_agent():
    """Test the SARSA agent"""
    print("🧪 Testing SARSA Agent")
    print("="*50)
    
    try:
        # Create environment
        env = ExamTimetablingSARSAEnv(max_timeslots=15)
        
        # Create agent
        state_size = env.observation_space.shape[0]
        action_size = env.action_space.n
        
        agent = SARSAAgent(
            state_size=state_size,
            action_size=action_size,
            epsilon_start=0.8,
            epsilon_decay=0.99
        )
        
        print(f"\n✅ Agent created successfully")
        
        # Quick training test
        print(f"\n🏃‍♂️ Quick training test (5 episodes)...")
        training_stats = agent.train(env, num_episodes=5, verbose=True)
        
        print(f"\n📊 Training stats: {training_stats}")
        
        # Quick evaluation test
        print(f"\n🔍 Quick evaluation test (3 episodes)...")
        eval_stats = agent.evaluate(env, num_episodes=3)
        
        print(f"\n📈 Evaluation stats: {eval_stats}")
        
    except Exception as e:
        print(f"❌ Error testing SARSA agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sarsa_agent() 