"""
Deep Q-Network (DQN) Agent for STA83 Exam Timetabling
Implements DQN with experience replay and target network
"""
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import deque, namedtuple
import random
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Optional
from environment import ExamTimetablingEnv

# Experience tuple for replay buffer
Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done'])

class DQNNetwork(nn.Module):
    """
    Deep Q-Network for exam timetabling
    """
    
    def __init__(self, state_size: int, action_size: int, hidden_sizes: List[int] = [128, 64]):
        """
        Initialize the DQN network
        
        Args:
            state_size: Size of the state space
            action_size: Size of the action space (number of timeslots)
            hidden_sizes: List of hidden layer sizes
        """
        super(DQNNetwork, self).__init__()
        
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

class ReplayBuffer:
    """
    Experience replay buffer for DQN
    """
    
    def __init__(self, capacity: int = 10000):
        """
        Initialize replay buffer
        
        Args:
            capacity: Maximum number of experiences to store
        """
        self.buffer = deque(maxlen=capacity)
        self.capacity = capacity
    
    def push(self, state, action, reward, next_state, done):
        """Add experience to buffer"""
        experience = Experience(state, action, reward, next_state, done)
        self.buffer.append(experience)
    
    def sample(self, batch_size: int) -> List[Experience]:
        """Sample batch of experiences"""
        return random.sample(self.buffer, batch_size)
    
    def __len__(self):
        return len(self.buffer)

class DQNAgent:
    """
    DQN Agent for exam timetabling
    """
    
    def __init__(self, 
                 state_size: int,
                 action_size: int,
                 learning_rate: float = 0.001,
                 gamma: float = 0.99,
                 epsilon_start: float = 1.0,
                 epsilon_end: float = 0.01,
                 epsilon_decay: float = 0.995,
                 buffer_size: int = 10000,
                 batch_size: int = 32,
                 target_update_freq: int = 100,
                 device: Optional[str] = None):
        """
        Initialize DQN agent
        
        Args:
            state_size: Size of state space
            action_size: Size of action space
            learning_rate: Learning rate for optimizer
            gamma: Discount factor
            epsilon_start: Initial exploration rate
            epsilon_end: Final exploration rate
            epsilon_decay: Exploration decay rate
            buffer_size: Size of replay buffer
            batch_size: Batch size for training
            target_update_freq: Frequency of target network updates
            device: Device to run on (cuda/cpu)
        """
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        
        # Device setup
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        print(f" DQN Agent using device: {self.device}")
        
        # Networks
        self.q_network = DQNNetwork(state_size, action_size).to(self.device)
        self.target_network = DQNNetwork(state_size, action_size).to(self.device)
        
        # Copy weights to target network
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Replay buffer
        self.replay_buffer = ReplayBuffer(buffer_size)
        
        # Training metrics
        self.training_step = 0
        self.losses = []
        self.episode_rewards = []
        self.episode_lengths = []
        self.epsilon_history = []
    
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
                action = random.randrange(self.action_size)
        
        return action
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay buffer"""
        self.replay_buffer.push(state, action, reward, next_state, done)
    
    def replay(self):
        """Train the network on a batch of experiences"""
        if len(self.replay_buffer) < self.batch_size:
            return
        
        # Sample batch
        experiences = self.replay_buffer.sample(self.batch_size)
        
        # Convert to tensors efficiently
        states = torch.FloatTensor(np.array([e.state for e in experiences])).to(self.device)
        actions = torch.LongTensor(np.array([e.action for e in experiences])).to(self.device)
        rewards = torch.FloatTensor(np.array([e.reward for e in experiences])).to(self.device)
        next_states = torch.FloatTensor(np.array([e.next_state for e in experiences])).to(self.device)
        dones = torch.BoolTensor(np.array([e.done for e in experiences])).to(self.device)
        
        # Current Q values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Next Q values from target network
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0]
            target_q_values = rewards + (self.gamma * next_q_values * ~dones)
        
        # Compute loss
        loss = F.mse_loss(current_q_values.squeeze(), target_q_values)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), max_norm=1.0)
        
        self.optimizer.step()
        
        # Update target network
        self.training_step += 1
        if self.training_step % self.target_update_freq == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
        
        # Store loss
        self.losses.append(loss.item())
        
        # Decay epsilon
        if self.epsilon > self.epsilon_end:
            self.epsilon *= self.epsilon_decay
    
    def train(self, env: ExamTimetablingEnv, num_episodes: int = 1000, 
              max_steps_per_episode: Optional[int] = None, verbose: bool = True) -> Dict:
        """
        Train the DQN agent
        
        Args:
            env: Environment to train on
            num_episodes: Number of training episodes
            max_steps_per_episode: Maximum steps per episode
            verbose: Whether to print progress
            
        Returns:
            Training statistics
        """
        if max_steps_per_episode is None:
            max_steps_per_episode = env.num_exams
        
        print(f" Starting DQN training for {num_episodes} episodes")
        print(f"   Max steps per episode: {max_steps_per_episode}")
        print(f"   Replay buffer size: {len(self.replay_buffer)}")
        
        successful_episodes = 0
        best_reward = -float('inf')
        best_solution = None
        
        for episode in range(num_episodes):
            state = env.reset()
            episode_reward = 0
            episode_length = 0
            
            for step in range(max_steps_per_episode):
                # Get valid actions for action masking
                valid_actions = env.get_valid_actions()
                
                # Choose action
                action = self.act(state, valid_actions)
                
                # Take step
                next_state, reward, done, info = env.step(action)
                
                # Store experience
                self.remember(state, action, reward, next_state, done)
                
                # Train
                self.replay()
                
                # Update state
                state = next_state
                episode_reward += reward
                episode_length += 1
                
                if done:
                    if 'valid_solution' in info and info['valid_solution']:
                        successful_episodes += 1
                        if episode_reward > best_reward:
                            best_reward = episode_reward
                            best_solution = env.get_solution_quality()
                    break
            
            # Store episode metrics
            self.episode_rewards.append(episode_reward)
            self.episode_lengths.append(episode_length)
            self.epsilon_history.append(self.epsilon)
            
            # Print progress
            if verbose and (episode + 1) % 100 == 0:
                avg_reward = np.mean(self.episode_rewards[-100:])
                avg_length = np.mean(self.episode_lengths[-100:])
                success_rate = successful_episodes / (episode + 1)
                
                print(f"Episode {episode + 1}/{num_episodes}")
                print(f"  Avg Reward (last 100): {avg_reward:.2f}")
                print(f"  Avg Length (last 100): {avg_length:.1f}")
                print(f"  Success Rate: {success_rate:.3f}")
                print(f"  Epsilon: {self.epsilon:.3f}")
                print(f"  Buffer Size: {len(self.replay_buffer)}")
                
                if best_solution:
                    print(f"  Best Solution: {best_solution['timeslots_used']} slots, "
                          f"{best_solution['avg_proximity_penalty']:.2f} avg penalty")
        
        training_stats = {
            'episode_rewards': self.episode_rewards,
            'episode_lengths': self.episode_lengths,
            'epsilon_history': self.epsilon_history,
            'losses': self.losses,
            'successful_episodes': successful_episodes,
            'success_rate': successful_episodes / num_episodes,
            'best_reward': best_reward,
            'best_solution': best_solution
        }
        
        print(f"\n Training completed!")
        print(f"   Success rate: {training_stats['success_rate']:.3f}")
        print(f"   Best reward: {best_reward:.2f}")
        
        return training_stats
    
    def evaluate(self, env: ExamTimetablingEnv, num_episodes: int = 10) -> Dict:
        """
        Evaluate the trained agent
        
        Args:
            env: Environment to evaluate on
            num_episodes: Number of evaluation episodes
            
        Returns:
            Evaluation statistics
        """
        print(f"🔍 Evaluating agent for {num_episodes} episodes")
        
        # Disable exploration
        original_epsilon = self.epsilon
        self.epsilon = 0.0
        
        eval_rewards = []
        eval_solutions = []
        successful_evaluations = 0
        
        for episode in range(num_episodes):
            state = env.reset()
            episode_reward = 0
            
            for step in range(env.num_exams):
                valid_actions = env.get_valid_actions()
                action = self.act(state, valid_actions)
                state, reward, done, info = env.step(action)
                episode_reward += reward
                
                if done:
                    if 'valid_solution' in info and info['valid_solution']:
                        successful_evaluations += 1
                        solution = env.get_solution_quality()
                        eval_solutions.append(solution)
                    break
            
            eval_rewards.append(episode_reward)
        
        # Restore epsilon
        self.epsilon = original_epsilon
        
        eval_stats = {
            'rewards': eval_rewards,
            'solutions': eval_solutions,
            'success_rate': successful_evaluations / num_episodes,
            'avg_reward': np.mean(eval_rewards),
            'avg_timeslots': np.mean([s['timeslots_used'] for s in eval_solutions]) if eval_solutions else 0,
            'avg_proximity_penalty': np.mean([s['avg_proximity_penalty'] for s in eval_solutions]) if eval_solutions else 0
        }
        
        print(f" Evaluation Results:")
        print(f"   Success Rate: {eval_stats['success_rate']:.3f}")
        print(f"   Average Reward: {eval_stats['avg_reward']:.2f}")
        if eval_solutions:
            print(f"   Average Timeslots: {eval_stats['avg_timeslots']:.1f}")
            print(f"   Average Proximity Penalty: {eval_stats['avg_proximity_penalty']:.2f}")
        
        return eval_stats
    
    def plot_training_progress(self, save_path: Optional[str] = None):
        """Plot training progress"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Episode rewards
        axes[0, 0].plot(self.episode_rewards)
        axes[0, 0].set_title('Episode Rewards')
        axes[0, 0].set_xlabel('Episode')
        axes[0, 0].set_ylabel('Reward')
        
        # Episode lengths
        axes[0, 1].plot(self.episode_lengths)
        axes[0, 1].set_title('Episode Lengths')
        axes[0, 1].set_xlabel('Episode')
        axes[0, 1].set_ylabel('Steps')
        
        # Epsilon decay
        axes[1, 0].plot(self.epsilon_history)
        axes[1, 0].set_title('Epsilon Decay')
        axes[1, 0].set_xlabel('Episode')
        axes[1, 0].set_ylabel('Epsilon')
        
        # Training loss
        if self.losses:
            axes[1, 1].plot(self.losses)
            axes[1, 1].set_title('Training Loss')
            axes[1, 1].set_xlabel('Training Step')
            axes[1, 1].set_ylabel('Loss')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f" Training plots saved to {save_path}")
        
        plt.show()
    
    def save_model(self, filepath: str):
        """Save the trained model"""
        torch.save({
            'q_network_state_dict': self.q_network.state_dict(),
            'target_network_state_dict': self.target_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'training_step': self.training_step,
            'hyperparameters': {
                'state_size': self.state_size,
                'action_size': self.action_size,
                'learning_rate': self.learning_rate,
                'gamma': self.gamma,
                'epsilon_end': self.epsilon_end,
                'epsilon_decay': self.epsilon_decay,
                'batch_size': self.batch_size,
                'target_update_freq': self.target_update_freq
            }
        }, filepath)
        print(f" Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load a trained model"""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
        self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint['epsilon']
        self.training_step = checkpoint['training_step']
        
        print(f"📂 Model loaded from {filepath}")

def test_dqn_agent():
    """Test the DQN agent implementation"""
    print(" Testing DQN Agent")
    print("="*50)
    
    try:
        # Create environment
        env = ExamTimetablingEnv(max_timeslots=15)
        
        # Create agent
        state_size = env.observation_space.shape[0]
        action_size = env.action_space.n
        
        agent = DQNAgent(
            state_size=state_size,
            action_size=action_size,
            learning_rate=0.001,
            epsilon_start=1.0,
            epsilon_end=0.01,
            epsilon_decay=0.995
        )
        
        print(f" Agent created successfully")
        print(f"   State size: {state_size}")
        print(f"   Action size: {action_size}")
        print(f"   Network: {agent.q_network}")
        
        # Test a few episodes
        print(f"\n🎮 Testing agent for 5 episodes:")
        
        for episode in range(5):
            state = env.reset()
            episode_reward = 0
            steps = 0
            
            for step in range(env.num_exams):
                valid_actions = env.get_valid_actions()
                action = agent.act(state, valid_actions)
                next_state, reward, done, info = env.step(action)
                
                agent.remember(state, action, reward, next_state, done)
                state = next_state
                episode_reward += reward
                steps += 1
                
                if done:
                    break
            
            print(f"   Episode {episode+1}: {steps} steps, reward {episode_reward:.2f}")
            
            # Train on collected experiences
            if len(agent.replay_buffer) >= agent.batch_size:
                agent.replay()
        
        print(f"\n DQN agent test completed successfully!")
        
    except Exception as e:
        print(f" DQN agent test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dqn_agent() 