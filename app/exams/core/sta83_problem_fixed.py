"""
STA83 Problem Definition for pymoo
Multi-objective exam timetabling problem using permutation encoding
"""
import numpy as np
from pymoo.core.problem import Problem
from typing import Dict, List
try:
    from .sta83_data_loader import STA83DataLoader
    from .timetabling_core import decode_permutation, calculate_proximity_penalty
except ImportError:
    from sta83_data_loader import STA83DataLoader
    from timetabling_core import decode_permutation, calculate_proximity_penalty
import traceback # Added for detailed error logging

class STA83Problem(Problem):
    """
    STA83 Exam Timetabling Problem for pymoo
    
    Objectives:
    1. Minimize number of timeslots used
    2. Minimize average proximity penalty per student
    
    Encoding: Permutation of exam IDs (1-indexed)
    """
    
    def __init__(self, data_loader: STA83DataLoader):
        """
        Initialize the STA83 problem
        
        Args:
            data_loader: Loaded STA83 dataset
        """
        if not data_loader.is_loaded:
            raise ValueError("Data loader must be loaded before creating problem")
        
        self.data_loader = data_loader
        self.num_exams = data_loader.num_exams
        self.num_students = data_loader.num_students
        self.conflict_matrix = data_loader.conflict_matrix
        self.student_enrollments = data_loader.student_enrollments
        
        # Initialize pymoo Problem
        # n_var: number of decision variables (exam permutation length)
        # n_obj: number of objectives (2: timeslots, penalty)
        # n_constr: number of constraints (0, handled by decoder)
        # xl, xu: lower and upper bounds for permutation (0 to num_exams-1)
        super().__init__(
            n_var=self.num_exams,
            n_obj=2,
            n_constr=0,
            xl=0,
            xu=self.num_exams - 1,
            elementwise_evaluation=False  # Handle vectorized evaluation
        )
    
    def _evaluate(self, X, out, *args, **kwargs):
        """
        Evaluate a population of solutions (permutations)
        
        Args:
            X: Population matrix (n_pop x n_var)
            out: Output dictionary to store objectives
        """
        # X is a 2D array where each row is a permutation
        n_pop = X.shape[0]
        F = np.zeros((n_pop, 2))
        
        for i in range(n_pop):
            individual_out = {}
            self._evaluate_single(X[i], individual_out)
            F[i] = individual_out["F"]
        
        out["F"] = F
    
    def _evaluate_single(self, x, out):
        """Evaluate a single permutation"""
        # Handle pymoo Individual objects or numpy arrays
        if hasattr(x, 'X'):
            # pymoo Individual object
            x_array = x.X
        else:
            # numpy array
            x_array = x
        
        # Handle both 0-indexed and 1-indexed permutations
        x_int = x_array.astype(int)
        
        # Check if permutation is 0-indexed (0 to n-1) or 1-indexed (1 to n)
        if np.min(x_int) == 0 and np.max(x_int) == self.num_exams - 1:
            # 0-indexed: convert to 1-indexed exam IDs
            exam_permutation = x_int + 1
        elif np.min(x_int) == 1 and np.max(x_int) == self.num_exams:
            # Already 1-indexed
            exam_permutation = x_int
        else:
            # Invalid permutation
            print(f"Warning: Invalid permutation range: {np.min(x_int)} to {np.max(x_int)}")
            out["F"] = [self.num_exams, 1000.0]
            return
        
        try:
            # Decode permutation to get exam schedule
            exam_to_slot_map, timeslots_used = decode_permutation(
                exam_permutation, 
                self.conflict_matrix, 
                self.num_exams
            )
            
            # Calculate proximity penalty
            total_penalty_sum = calculate_proximity_penalty(
                exam_to_slot_map,
                self.student_enrollments,
                self.num_students
            )
            
            # Calculate average penalty per student
            avg_penalty_per_student = total_penalty_sum / self.num_students
            
            # Set objectives
            # Objective 1: Minimize timeslots used
            # Objective 2: Minimize average penalty per student
            out["F"] = [timeslots_used, avg_penalty_per_student]
            
        except Exception as e:
            # If evaluation fails, assign large penalty values
            print(f"Warning: Evaluation failed for permutation {exam_permutation[:5]}...")
            traceback.print_exc() # Print full traceback
            out["F"] = [self.num_exams, 1000.0]  # Large penalty values
    
    def get_exam_schedule(self, permutation: np.ndarray) -> Dict:
        """
        Get detailed exam schedule from a permutation
        
        Args:
            permutation: Exam permutation (0-indexed)
            
        Returns:
            Dictionary with schedule details
        """
        # Convert to 1-indexed exam IDs
        exam_permutation = permutation.astype(int) + 1
        
        # Decode permutation
        exam_to_slot_map, timeslots_used = decode_permutation(
            exam_permutation,
            self.conflict_matrix,
            self.num_exams
        )
        
        # Calculate penalty
        total_penalty_sum = calculate_proximity_penalty(
            exam_to_slot_map,
            self.student_enrollments,
            self.num_students
        )
        
        # Organize schedule by timeslot
        slot_to_exams = {}
        for exam_id, slot_id in exam_to_slot_map.items():
            if slot_id not in slot_to_exams:
                slot_to_exams[slot_id] = []
            slot_to_exams[slot_id].append(exam_id)
        
        # Sort exams within each slot
        for slot_id in slot_to_exams:
            slot_to_exams[slot_id].sort()
        
        return {
            'exam_to_slot_map': exam_to_slot_map,
            'slot_to_exams': slot_to_exams,
            'timeslots_used': timeslots_used,
            'total_penalty_sum': total_penalty_sum,
            'avg_penalty_per_student': total_penalty_sum / self.num_students,
            'permutation': exam_permutation.tolist()
        }
    
    def validate_solution(self, permutation: np.ndarray) -> Dict:
        """
        Validate a solution and check for constraint violations
        
        Args:
            permutation: Exam permutation (0-indexed)
            
        Returns:
            Dictionary with validation results
        """
        # Convert to 1-indexed
        exam_permutation = permutation.astype(int) + 1
        
        # Check if permutation is valid
        expected_exams = set(range(1, self.num_exams + 1))
        actual_exams = set(exam_permutation)
        
        is_valid_permutation = (expected_exams == actual_exams)
        
        if not is_valid_permutation:
            return {
                'is_valid': False,
                'error': 'Invalid permutation: missing or duplicate exams',
                'missing_exams': expected_exams - actual_exams,
                'duplicate_exams': [x for x in actual_exams if list(exam_permutation).count(x) > 1]
            }
        
        # Get schedule
        schedule = self.get_exam_schedule(permutation)
        
        # Check for conflicts
        conflicts = []
        for slot_id, exams_in_slot in schedule['slot_to_exams'].items():
            for i in range(len(exams_in_slot)):
                for j in range(i + 1, len(exams_in_slot)):
                    exam1_id = exams_in_slot[i]
                    exam2_id = exams_in_slot[j]
                    exam1_idx = exam1_id - 1
                    exam2_idx = exam2_id - 1
                    
                    if self.conflict_matrix[exam1_idx][exam2_idx] == 1:
                        conflicts.append((exam1_id, exam2_id, slot_id))
        
        return {
            'is_valid': len(conflicts) == 0,
            'conflicts': conflicts,
            'num_conflicts': len(conflicts),
            'schedule': schedule
        }

def test_sta83_problem():
    """Test the STA83 problem definition"""
    print("Testing STA83 Problem Definition")
    print("="*40)
    
    # Load data
    loader = STA83DataLoader()
    if not loader.load_data():
        print("Failed to load data")
        return
    
    print("Data loaded successfully")
    
    # Create problem
    problem = STA83Problem(loader)
    print(f"Problem created: {problem.n_var} variables, {problem.n_obj} objectives")
    
    # Test with a random permutation
    np.random.seed(42)
    test_permutation = np.random.permutation(problem.n_var)
    
    print(f"\nTesting with random permutation: {test_permutation[:10]}...")
    
    # Evaluate solution
    out = {}
    problem._evaluate(test_permutation, out)
    objectives = out["F"]
    
    print(f"Objectives: {objectives[0]:.0f} timeslots, {objectives[1]:.4f} avg penalty")
    
    # Get detailed schedule
    schedule = problem.get_exam_schedule(test_permutation)
    print(f"Schedule details:")
    print(f"   Timeslots used: {schedule['timeslots_used']}")
    print(f"   Total penalty: {schedule['total_penalty_sum']:.2f}")
    print(f"   Avg penalty per student: {schedule['avg_penalty_per_student']:.4f}")
    
    # Show first few timeslots
    print(f"   First 3 timeslots:")
    for slot_id in sorted(schedule['slot_to_exams'].keys())[:3]:
        exams = schedule['slot_to_exams'][slot_id]
        print(f"     Slot {slot_id}: {len(exams)} exams ({exams[:5]}{'...' if len(exams) > 5 else ''})")
    
    # Validate solution
    validation = problem.validate_solution(test_permutation)
    print(f"\nSolution validation:")
    print(f"   Valid: {'Yes' if validation['is_valid'] else 'No'}")
    if not validation['is_valid']:
        print(f"   Conflicts: {validation['num_conflicts']}")
        if validation['conflicts']:
            print(f"   First conflict: Exams {validation['conflicts'][0][0]} and {validation['conflicts'][0][1]} in slot {validation['conflicts'][0][2]}")

if __name__ == "__main__":
    test_sta83_problem() 