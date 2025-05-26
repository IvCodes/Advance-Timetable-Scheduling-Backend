"""
Reinforcement Learning Environment for STA83 Exam Timetabling
Sequential construction approach using DQN
"""
import numpy as np
import gym
from gym import spaces
from typing import Dict, List, Tuple, Optional
import torch
from core.sta83_data_loader import STA83DataLoader
from core.timetabling_core import PROXIMITY_WEIGHTS

class ExamTimetablingEnv(gym.Env):
    """
    RL Environment for Sequential Exam Timetabling Construction
    
    The agent sequentially assigns exams to timeslots, learning to avoid clashes
    and optimize for minimal timeslots and proximity penalties.
    """
    
    def __init__(self, max_timeslots: int = 20, data_path: str = 'data/'):
        """
        Initialize the exam timetabling environment
        
        Args:
            max_timeslots: Maximum number of timeslots to consider
            data_path: Path to the data directory containing STA83 files
        """
        super(ExamTimetablingEnv, self).__init__()
        
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
        
        # State space: current exam index + timetable representation + timeslot usage
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
        
        # Reward parameters
        self.clash_penalty = -100.0
        self.step_reward = 0.1
        self.completion_bonus = 500.0
        self.timeslot_penalty = -1.0
        self.proximity_penalty_weight = -0.01
        
        print(f" ExamTimetablingEnv initialized:")
        print(f"   Exams: {self.num_exams}, Students: {self.num_students}")
        print(f"   Max timeslots: {self.max_timeslots}")
        print(f"   State size: {state_size}")
    
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
            return self._get_state(), reward, True, info
        
        # Check for clashes with already assigned exams in this timeslot
        current_exam_id = self.current_exam_idx + 1  # Convert to 1-indexed
        clash_detected = False
        
        for exam_idx in range(self.num_exams):
            if self.timetable[exam_idx] == action:  # Exam already in this timeslot
                exam_id = exam_idx + 1  # Convert to 1-indexed
                if self.conflict_matrix[self.current_exam_idx][exam_idx] == 1:
                    clash_detected = True
                    break
        
        if clash_detected:
            reward = self.clash_penalty
            info['clash_detected'] = True
            info['exam_id'] = current_exam_id
            info['timeslot'] = action
            return self._get_state(), reward, True, info
        
        # Valid assignment - update state
        self.timetable[self.current_exam_idx] = action
        self.timeslot_usage[action] += 1
        
        # Calculate reward components
        reward += self.step_reward
        
        # Penalty for using a new timeslot
        if self.timeslot_usage[action] == 1:  # First exam in this timeslot
            used_timeslots = np.sum(self.timeslot_usage > 0)
            reward += self.timeslot_penalty * used_timeslots
        
        # Move to next exam
        self.current_exam_idx += 1
        self.episode_step += 1
        
        # Check if episode is complete
        done = self.current_exam_idx >= self.num_exams
        
        if done:
            # Calculate final rewards
            completion_reward = self.completion_bonus
            
            # Penalty based on total timeslots used
            used_timeslots = np.sum(self.timeslot_usage > 0)
            timeslot_penalty = self.timeslot_penalty * used_timeslots * 10
            
            # Proximity penalty
            proximity_penalty = self._calculate_proximity_penalty() * self.proximity_penalty_weight
            
            reward += completion_reward + timeslot_penalty + proximity_penalty
            
            info['completion_bonus'] = completion_reward
            info['timeslot_penalty'] = timeslot_penalty
            info['proximity_penalty'] = proximity_penalty
            info['total_timeslots'] = used_timeslots
            info['valid_solution'] = True
        
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
            
            # Check if current exam conflicts with any exam already in this timeslot
            for exam_idx in range(self.num_exams):
                if self.timetable[exam_idx] == timeslot:
                    if self.conflict_matrix[self.current_exam_idx][exam_idx] == 1:
                        has_conflict = True
                        break
            
            conflict_indicators.append(1.0 if has_conflict else 0.0)
        
        return conflict_indicators
    
    def _calculate_proximity_penalty(self) -> float:
        """Calculate total proximity penalty for current timetable"""
        if np.any(self.timetable == -1):
            return 0.0  # Incomplete timetable
        
        # Convert to exam_to_slot_map format (1-indexed)
        exam_to_slot_map = {}
        for exam_idx in range(self.num_exams):
            exam_id = exam_idx + 1
            timeslot = self.timetable[exam_idx] + 1  # Convert to 1-indexed
            exam_to_slot_map[exam_id] = timeslot
        
        total_penalty = 0.0
        
        for student_exams in self.student_enrollments:
            student_penalty = 0.0
            
            # Get timeslots for this student's exams
            student_slots = []
            for exam_id in student_exams:
                if exam_id in exam_to_slot_map:
                    student_slots.append(exam_to_slot_map[exam_id])
            
            # Calculate proximity penalties for this student
            for i in range(len(student_slots)):
                for j in range(i + 1, len(student_slots)):
                    slot_diff = abs(student_slots[i] - student_slots[j])
                    
                    # Apply proximity penalty if slots are close (1-5 slots apart)
                    if 1 <= slot_diff <= 5:
                        student_penalty += PROXIMITY_WEIGHTS[slot_diff]
            
            total_penalty += student_penalty
        
        return total_penalty
    
    def get_valid_actions(self) -> List[int]:
        """Get list of valid actions (timeslots without conflicts)"""
        if self.current_exam_idx >= self.num_exams:
            return []
        
        valid_actions = []
        conflict_indicators = self._get_conflict_indicators()
        
        for action in range(self.max_timeslots):
            if conflict_indicators[action] == 0.0:  # No conflict
                valid_actions.append(action)
        
        return valid_actions
    
    def render(self, mode='human'):
        """Render the current state"""
        if mode == 'human':
            print(f"\n Episode Step: {self.episode_step}/{self.max_episode_steps}")
            print(f"Current Exam: {self.current_exam_idx + 1}/{self.num_exams}")
            
            if self.current_exam_idx < self.num_exams:
                valid_actions = self.get_valid_actions()
                print(f"Valid timeslots: {[a+1 for a in valid_actions]}")
            
            # Show timeslot usage
            used_timeslots = np.sum(self.timeslot_usage > 0)
            print(f"Timeslots used: {used_timeslots}")
            
            for i, count in enumerate(self.timeslot_usage):
                if count > 0:
                    print(f"  Slot {i+1}: {count} exams")
    
    def get_solution_quality(self) -> Dict:
        """Get quality metrics for current solution"""
        if np.any(self.timetable == -1):
            return {'valid': False, 'reason': 'Incomplete timetable'}
        
        used_timeslots = np.sum(self.timeslot_usage > 0)
        proximity_penalty = self._calculate_proximity_penalty()
        
        return {
            'valid': True,
            'timeslots_used': int(used_timeslots),
            'proximity_penalty': float(proximity_penalty),
            'avg_proximity_penalty': float(proximity_penalty / self.num_students),
            'timetable': self.timetable.copy()
        }

def test_environment():
    """Test the exam timetabling environment"""
    print(" Testing ExamTimetablingEnv")
    print("="*50)
    
    try:
        env = ExamTimetablingEnv(max_timeslots=15)
        
        # Test reset
        state = env.reset()
        print(f" Environment reset successful")
        print(f"   Initial state shape: {state.shape}")
        print(f"   State range: [{state.min():.3f}, {state.max():.3f}]")
        
        # Test a few random steps
        print(f"\n🎮 Testing random actions:")
        for step in range(5):
            valid_actions = env.get_valid_actions()
            if valid_actions:
                action = np.random.choice(valid_actions)
                state, reward, done, info = env.step(action)
                
                print(f"   Step {step+1}: Action {action+1}, Reward {reward:.2f}, Done {done}")
                if 'clash_detected' in info:
                    print(f"      Clash detected!")
                    break
                if done:
                    print(f"      Episode completed!")
                    quality = env.get_solution_quality()
                    print(f"     Solution: {quality}")
                    break
            else:
                print(f"   Step {step+1}: No valid actions available")
                break
        
        print(f"\n Environment test completed successfully!")
        
    except Exception as e:
        print(f" Environment test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_environment() 