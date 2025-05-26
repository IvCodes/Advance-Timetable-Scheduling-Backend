"""
SARSA Environment for STA83 Exam Timetabling
Sequential construction approach using SARSA (on-policy learning)
"""
import numpy as np
import gym
from gym import spaces
from typing import Dict, List, Tuple, Optional
import torch
from app.exams.core.sta83_data_loader import STA83DataLoader
from app.exams.core.timetabling_core import PROXIMITY_WEIGHTS

class ExamTimetablingSARSAEnv(gym.Env):
    """
    SARSA Environment for Sequential Exam Timetabling Construction
    
    The agent sequentially assigns exams to timeslots, learning to avoid clashes
    and optimize for minimal timeslots and proximity penalties using on-policy SARSA.
    """
    
    def __init__(self, max_timeslots: int = 20, data_path: str = 'app/exams/data/'):
        """
        Initialize the SARSA exam timetabling environment
        
        Args:
            max_timeslots: Maximum number of timeslots to consider
            data_path: Path to the data directory containing STA83 files
        """
        super(ExamTimetablingSARSAEnv, self).__init__()
        
        # Environment parameters
        self.max_timeslots = max_timeslots
        self.data_path = data_path
        
        # Load STA83 data
        self.data_loader = STA83DataLoader(
            crs_file=f'{data_path}sta-f-83.crs',
            stu_file=f'{data_path}sta-f-83.stu'
        )
        
        if not self.data_loader.load_data():
            raise RuntimeError("Failed to load STA83 data")
        
        # Problem dimensions
        self.num_exams = self.data_loader.num_exams
        self.num_students = self.data_loader.num_students
        self.conflict_matrix = self.data_loader.conflict_matrix
        self.student_enrollments = self.data_loader.student_enrollments
        
        # Action space: choose timeslot for current exam (0 to max_timeslots-1)
        self.action_space = spaces.Discrete(max_timeslots)
        
        # State space: current exam index + timetable representation + timeslot usage + conflict indicators
        # State components:
        # - Current exam index (1 value)
        # - Timetable: which timeslot each exam is assigned to (-1 if unassigned) (num_exams values)
        # - Timeslot usage: how many exams in each timeslot (max_timeslots values)
        # - Conflict indicators: conflicts with current exam for each timeslot (max_timeslots values)
        state_size = 1 + self.num_exams + self.max_timeslots + self.max_timeslots
        self.observation_space = spaces.Box(
            low=-1, high=max(self.num_exams, max_timeslots), 
            shape=(state_size,), dtype=np.float32
        )
        
        # Environment state
        self.current_exam_idx = 0  # 0-indexed
        self.timetable = np.full(self.num_exams, -1, dtype=int)  # -1 means unassigned
        self.timeslot_usage = np.zeros(self.max_timeslots, dtype=int)
        self.episode_step = 0
        self.max_episode_steps = self.num_exams
        
        # Reward parameters (focused on clash-free construction)
        self.clash_penalty = -100.0  # Large penalty for clashes
        self.step_reward = 1.0  # Positive reward for valid placements
        self.completion_bonus = 500.0  # Large bonus for completing clash-free timetable
        self.timeslot_penalty = -1.0  # Small penalty for opening new timeslots
        self.proximity_penalty_weight = -0.01  # Small weight for proximity penalties
        
        print(f"🎯 SARSA ExamTimetablingEnv initialized:")
        print(f"   📚 Exams: {self.num_exams}, Students: {self.num_students}")
        print(f"   ⏰ Max timeslots: {self.max_timeslots}")
        print(f"   🧠 State size: {state_size}")
        print(f"   🎯 Primary goal: Clash-free timetable construction")
    
    def reset(self) -> np.ndarray:
        """Reset the environment to initial state"""
        self.current_exam_idx = 0
        self.timetable = np.full(self.num_exams, -1, dtype=int)
        self.timeslot_usage = np.zeros(self.max_timeslots, dtype=int)
        self.episode_step = 0
        
        return self._get_state()
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute one step in the environment
        
        Args:
            action: Timeslot to assign current exam to (0-indexed)
            
        Returns:
            next_state, reward, done, info
        """
        info = {}
        reward = 0.0
        
        # Validate action
        if action < 0 or action >= self.max_timeslots:
            reward = self.clash_penalty
            info['invalid_action'] = True
            info['termination_reason'] = 'invalid_action'
            return self._get_state(), reward, True, info
        
        # Check for clashes with already assigned exams in this timeslot
        current_exam_id = self.current_exam_idx + 1  # Convert to 1-indexed
        clash_detected = False
        
        for exam_idx in range(self.num_exams):
            if self.timetable[exam_idx] == action:  # Exam already in this timeslot
                exam_id = exam_idx + 1  # Convert to 1-indexed
                if self.conflict_matrix[self.current_exam_idx][exam_idx] == 1:
                    clash_detected = True
                    info['conflicting_exam'] = exam_id
                    break
        
        if clash_detected:
            reward = self.clash_penalty
            info['clash_detected'] = True
            info['exam_id'] = current_exam_id
            info['timeslot'] = action
            info['termination_reason'] = 'clash'
            return self._get_state(), reward, True, info
        
        # Valid assignment - update state
        self.timetable[self.current_exam_idx] = action
        self.timeslot_usage[action] += 1
        
        # Calculate reward components
        reward += self.step_reward  # Positive reward for valid placement
        
        # Small penalty for using a new timeslot (encourage compactness)
        if self.timeslot_usage[action] == 1:  # First exam in this timeslot
            reward += self.timeslot_penalty
        
        # Move to next exam
        self.current_exam_idx += 1
        self.episode_step += 1
        
        # Check if episode is complete
        done = self.current_exam_idx >= self.num_exams
        
        if done:
            # Calculate final rewards for successful completion
            completion_reward = self.completion_bonus
            
            # Additional penalty based on total timeslots used
            used_timeslots = np.sum(self.timeslot_usage > 0)
            timeslot_penalty = self.timeslot_penalty * used_timeslots * 5  # Moderate penalty
            
            # Proximity penalty (secondary objective)
            proximity_penalty = self._calculate_proximity_penalty() * self.proximity_penalty_weight
            
            reward += completion_reward + timeslot_penalty + proximity_penalty
            
            info['completion_bonus'] = completion_reward
            info['timeslot_penalty'] = timeslot_penalty
            info['proximity_penalty'] = proximity_penalty
            info['total_timeslots'] = used_timeslots
            info['valid_solution'] = True
            info['termination_reason'] = 'success'
        
        info['exam_id'] = current_exam_id
        info['assigned_timeslot'] = action
        info['step'] = self.episode_step
        
        return self._get_state(), reward, done, info
    
    def _get_state(self) -> np.ndarray:
        """
        Get current state representation
        
        Returns:
            State vector containing:
            - Current exam index (normalized)
            - Timetable assignments
            - Timeslot usage counts
            - Conflict indicators for current exam
        """
        state = []
        
        # Current exam index (normalized)
        state.append(self.current_exam_idx / self.num_exams)
        
        # Timetable assignments (normalized)
        normalized_timetable = self.timetable.astype(float) / self.max_timeslots
        state.extend(normalized_timetable)
        
        # Timeslot usage (normalized)
        normalized_usage = self.timeslot_usage.astype(float) / self.num_exams
        state.extend(normalized_usage)
        
        # Conflict indicators for current exam with each timeslot
        conflict_indicators = self._get_conflict_indicators()
        state.extend(conflict_indicators)
        
        return np.array(state, dtype=np.float32)
    
    def _get_conflict_indicators(self) -> List[float]:
        """
        Get conflict indicators for current exam with each timeslot
        
        Returns:
            List of conflict indicators (1.0 if conflict, 0.0 if safe)
        """
        if self.current_exam_idx >= self.num_exams:
            return [0.0] * self.max_timeslots
        
        conflict_indicators = []
        
        for timeslot in range(self.max_timeslots):
            has_conflict = False
            
            # Check if any exam already in this timeslot conflicts with current exam
            for exam_idx in range(self.num_exams):
                if self.timetable[exam_idx] == timeslot:
                    if self.conflict_matrix[self.current_exam_idx][exam_idx] == 1:
                        has_conflict = True
                        break
            
            conflict_indicators.append(1.0 if has_conflict else 0.0)
        
        return conflict_indicators
    
    def _calculate_proximity_penalty(self) -> float:
        """
        Calculate proximity penalty using Carter et al.'s weights
        
        Returns:
            Total proximity penalty
        """
        total_penalty = 0.0
        
        for student_exams in self.student_enrollments:
            # Get timeslots for this student's exams
            student_timeslots = []
            for exam_id in student_exams:
                exam_idx = exam_id - 1  # Convert to 0-indexed
                if 0 <= exam_idx < self.num_exams:
                    timeslot = self.timetable[exam_idx]
                    if timeslot >= 0:  # Exam is assigned
                        student_timeslots.append(timeslot)
            
            # Calculate penalties for exam pairs
            student_timeslots.sort()
            for i in range(len(student_timeslots)):
                for j in range(i + 1, len(student_timeslots)):
                    distance = abs(student_timeslots[j] - student_timeslots[i])
                    if 1 <= distance <= 5:
                        weight = PROXIMITY_WEIGHTS.get(distance, 0)
                        total_penalty += weight
        
        return total_penalty
    
    def get_valid_actions(self) -> List[int]:
        """
        Get list of valid actions (timeslots without conflicts)
        
        Returns:
            List of valid timeslot indices
        """
        if self.current_exam_idx >= self.num_exams:
            return []
        
        valid_actions = []
        conflict_indicators = self._get_conflict_indicators()
        
        for timeslot in range(self.max_timeslots):
            if conflict_indicators[timeslot] == 0.0:  # No conflict
                valid_actions.append(timeslot)
        
        return valid_actions
    
    def render(self, mode='human'):
        """Render the current state"""
        if mode == 'human':
            print(f"\n📊 SARSA Environment State:")
            print(f"   Current exam: {self.current_exam_idx + 1}/{self.num_exams}")
            print(f"   Episode step: {self.episode_step}")
            
            used_timeslots = np.sum(self.timeslot_usage > 0)
            print(f"   Timeslots used: {used_timeslots}")
            
            if used_timeslots > 0:
                print(f"   Timeslot usage: {self.timeslot_usage[:used_timeslots+2]}")
            
            valid_actions = self.get_valid_actions()
            print(f"   Valid actions: {len(valid_actions)}/{self.max_timeslots}")
    
    def get_solution_quality(self) -> Dict:
        """
        Get quality metrics for the current solution
        
        Returns:
            Dictionary with solution quality metrics
        """
        used_timeslots = np.sum(self.timeslot_usage > 0)
        proximity_penalty = self._calculate_proximity_penalty()
        
        return {
            'timeslots_used': used_timeslots,
            'proximity_penalty': proximity_penalty,
            'is_complete': self.current_exam_idx >= self.num_exams,
            'is_feasible': True  # If we reach here, no clashes detected
        }

def test_sarsa_environment():
    """Test the SARSA environment"""
    print("🧪 Testing SARSA Environment")
    print("="*50)
    
    try:
        env = ExamTimetablingSARSAEnv(max_timeslots=15)
        
        print(f"\n✅ Environment created successfully")
        print(f"   State space: {env.observation_space.shape}")
        print(f"   Action space: {env.action_space.n}")
        
        # Test reset
        state = env.reset()
        print(f"\n🔄 Reset successful, state shape: {state.shape}")
        
        # Test a few steps
        print(f"\n🎯 Testing steps:")
        for step in range(min(5, env.num_exams)):
            valid_actions = env.get_valid_actions()
            if valid_actions:
                action = valid_actions[0]  # Choose first valid action
                next_state, reward, done, info = env.step(action)
                
                print(f"   Step {step+1}: Action {action}, Reward {reward:.1f}, Done {done}")
                if done:
                    print(f"   Termination reason: {info.get('termination_reason', 'unknown')}")
                    break
            else:
                print(f"   Step {step+1}: No valid actions available")
                break
        
        print(f"\n📈 Final solution quality:")
        quality = env.get_solution_quality()
        for key, value in quality.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ Error testing environment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sarsa_environment() 