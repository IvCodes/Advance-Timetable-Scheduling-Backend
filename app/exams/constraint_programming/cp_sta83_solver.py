#!/usr/bin/env python3
"""
STA83 Exam Timetabling using Google OR-Tools CP-SAT Solver
Constraint Programming approach for finding optimal exam schedules
"""
import sys
import os
import time
import numpy as np
from typing import Dict, List, Tuple, Optional
from ortools.sat.python import cp_model

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.sta83_data_loader import STA83DataLoader

class STA83CPSolver:
    """
    Constraint Programming solver for STA83 exam timetabling problem
    Uses Google OR-Tools CP-SAT solver
    """
    
    def __init__(self, data_loader: STA83DataLoader):
        """
        Initialize the CP solver with STA83 data
        
        Args:
            data_loader: Loaded STA83 dataset
        """
        if not data_loader.is_loaded:
            raise ValueError("Data loader must be loaded before creating solver")
        
        self.data_loader = data_loader
        self.num_exams = data_loader.num_exams
        self.num_students = data_loader.num_students
        self.conflict_matrix = data_loader.conflict_matrix
        self.student_enrollments = data_loader.student_enrollments
        
        # CP model components
        self.model = None
        self.solver = None
        self.exam_timeslot_vars = {}  # T_i variables for each exam
        self.max_timeslot_var = None
        self.conflicting_pairs = []
        
        print(f"CP Solver initialized for STA83:")
        print(f"   Exams: {self.num_exams}")
        print(f"   Students: {self.num_students}")
        
    def _extract_conflicts(self) -> List[Tuple[int, int]]:
        """
        Extract conflicting exam pairs from conflict matrix
        
        Returns:
            List of (exam1_id, exam2_id) tuples that conflict
        """
        conflicts = []
        
        # Convert 0-indexed matrix to 1-indexed exam IDs
        for i in range(self.num_exams):
            for j in range(i + 1, self.num_exams):
                if self.conflict_matrix[i][j] == 1:
                    exam1_id = i + 1  # Convert to 1-indexed
                    exam2_id = j + 1
                    conflicts.append((exam1_id, exam2_id))
        
        print(f"Found {len(conflicts)} conflicting exam pairs")
        return conflicts
    
    def create_model(self, max_timeslots: int = 20) -> cp_model.CpModel:
        """
        Create the CP-SAT model for exam timetabling
        
        Args:
            max_timeslots: Maximum number of timeslots to consider
            
        Returns:
            CP model ready for solving
        """
        print(f"\nCreating CP model with max {max_timeslots} timeslots...")
        
        self.model = cp_model.CpModel()
        
        # 1. Extract conflicting pairs
        self.conflicting_pairs = self._extract_conflicts()
        
        # 2. Create variables: T_i for each exam (timeslot assignment)
        print("Creating exam timeslot variables...")
        for exam_id in range(1, self.num_exams + 1):
            var_name = f"T_{exam_id}"
            self.exam_timeslot_vars[exam_id] = self.model.NewIntVar(
                0, max_timeslots - 1, var_name
            )
        
        # 3. Create max_timeslot variable for objective
        self.max_timeslot_var = self.model.NewIntVar(
            0, max_timeslots - 1, "max_timeslot_used"
        )
        
        # 4. Add hard constraints: No clashes
        print("Adding conflict constraints...")
        for exam1_id, exam2_id in self.conflicting_pairs:
            # T_i != T_j for conflicting exams
            self.model.Add(
                self.exam_timeslot_vars[exam1_id] != self.exam_timeslot_vars[exam2_id]
            )
        
        # 5. Link max_timeslot with individual exam timeslots
        print("Adding max timeslot constraints...")
        for exam_id in range(1, self.num_exams + 1):
            self.model.Add(
                self.max_timeslot_var >= self.exam_timeslot_vars[exam_id]
            )
        
        # 6. Set objective: Minimize number of timeslots used
        self.model.Minimize(self.max_timeslot_var)
        
        print(f"CP model created:")
        print(f"   Variables: {len(self.exam_timeslot_vars)} exam assignments + 1 max timeslot")
        print(f"   Constraints: {len(self.conflicting_pairs)} conflict constraints")
        
        return self.model
    
    def solve(self, time_limit_seconds: int = 300) -> Dict:
        """
        Solve the CP model
        
        Args:
            time_limit_seconds: Maximum solving time
            
        Returns:
            Dictionary with solution details
        """
        if self.model is None:
            raise ValueError("Model must be created before solving")
        
        print(f"\nSolving CP model (time limit: {time_limit_seconds}s)...")
        
        # Create solver
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = time_limit_seconds
        self.solver.parameters.log_search_progress = True
        
        # Solve
        start_time = time.time()
        status = self.solver.Solve(self.model)
        solve_time = time.time() - start_time
        
        # Process results
        result = {
            'status': status,
            'solve_time': solve_time,
            'optimal': status == cp_model.OPTIMAL,
            'feasible': status in [cp_model.OPTIMAL, cp_model.FEASIBLE],
            'timeslots_used': None,
            'exam_schedule': {},
            'slot_to_exams': {},
            'proximity_penalty': None
        }
        
        if result['feasible']:
            # Extract solution
            result['timeslots_used'] = self.solver.Value(self.max_timeslot_var) + 1
            
            # Build exam schedule
            for exam_id in range(1, self.num_exams + 1):
                timeslot = self.solver.Value(self.exam_timeslot_vars[exam_id])
                result['exam_schedule'][exam_id] = timeslot
                
                if timeslot not in result['slot_to_exams']:
                    result['slot_to_exams'][timeslot] = []
                result['slot_to_exams'][timeslot].append(exam_id)
            
            # Calculate proximity penalty
            result['proximity_penalty'] = self._calculate_proximity_penalty(
                result['exam_schedule']
            )
            
            print(f"Solution found!")
            print(f"   Status: {'OPTIMAL' if result['optimal'] else 'FEASIBLE'}")
            print(f"   Timeslots used: {result['timeslots_used']}")
            print(f"   Proximity penalty: {result['proximity_penalty']:.2f}")
            print(f"   Solve time: {solve_time:.2f}s")
            
        else:
            print(f"No solution found")
            print(f"   Status: {self._status_name(status)}")
            print(f"   Solve time: {solve_time:.2f}s")
        
        return result
    
    def _calculate_proximity_penalty(self, exam_schedule: Dict[int, int]) -> float:
        """
        Calculate Carter proximity penalty for a given schedule
        
        Args:
            exam_schedule: Dictionary mapping exam_id -> timeslot
            
        Returns:
            Total proximity penalty
        """
        penalty_weights = {1: 16, 2: 8, 3: 4, 4: 2, 5: 1}
        total_penalty = 0.0
        
        # Handle both dict and list formats for student enrollments
        if isinstance(self.student_enrollments, dict):
            student_data = self.student_enrollments.items()
        else:
            # Convert list format to dict format
            student_data = enumerate(self.student_enrollments)
        
        for student_id, exams in student_data:
            if len(exams) < 2:
                continue
            
            # Check all pairs of exams for this student
            for i in range(len(exams)):
                for j in range(i + 1, len(exams)):
                    exam1_id = exams[i]
                    exam2_id = exams[j]
                    
                    slot1 = exam_schedule[exam1_id]
                    slot2 = exam_schedule[exam2_id]
                    
                    slot_diff = abs(slot1 - slot2)
                    
                    if 1 <= slot_diff <= 5:
                        total_penalty += penalty_weights[slot_diff]
        
        return total_penalty / self.num_students
    
    def _status_name(self, status: int) -> str:
        """Convert CP solver status to readable name"""
        status_names = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE", 
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.UNKNOWN: "UNKNOWN",
            cp_model.MODEL_INVALID: "MODEL_INVALID"
        }
        return status_names.get(status, f"UNKNOWN_STATUS_{status}")
    
    def solve_with_fixed_timeslots(self, fixed_timeslots: int, time_limit_seconds: int = 300) -> Dict:
        """
        Solve with a fixed number of timeslots, optimizing for proximity penalty
        
        Args:
            fixed_timeslots: Fixed number of timeslots to use
            time_limit_seconds: Maximum solving time
            
        Returns:
            Dictionary with solution details
        """
        print(f"\nSolving with fixed {fixed_timeslots} timeslots...")
        
        # Create new model with fixed timeslots
        self.model = cp_model.CpModel()
        self.conflicting_pairs = self._extract_conflicts()
        
        # Create variables with fixed domain
        for exam_id in range(1, self.num_exams + 1):
            var_name = f"T_{exam_id}"
            self.exam_timeslot_vars[exam_id] = self.model.NewIntVar(
                0, fixed_timeslots - 1, var_name
            )
        
        # Add conflict constraints
        for exam1_id, exam2_id in self.conflicting_pairs:
            self.model.Add(
                self.exam_timeslot_vars[exam1_id] != self.exam_timeslot_vars[exam2_id]
            )
        
        # For proximity penalty optimization, we'll use a simplified approach
        # Just find any feasible solution with fixed timeslots
        # (Full penalty optimization would require many auxiliary variables)
        
        # Solve
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = time_limit_seconds
        
        start_time = time.time()
        status = self.solver.Solve(self.model)
        solve_time = time.time() - start_time
        
        # Process results
        result = {
            'status': status,
            'solve_time': solve_time,
            'optimal': status == cp_model.OPTIMAL,
            'feasible': status in [cp_model.OPTIMAL, cp_model.FEASIBLE],
            'timeslots_used': fixed_timeslots if status in [cp_model.OPTIMAL, cp_model.FEASIBLE] else None,
            'exam_schedule': {},
            'slot_to_exams': {},
            'proximity_penalty': None
        }
        
        if result['feasible']:
            # Extract solution
            for exam_id in range(1, self.num_exams + 1):
                timeslot = self.solver.Value(self.exam_timeslot_vars[exam_id])
                result['exam_schedule'][exam_id] = timeslot
                
                if timeslot not in result['slot_to_exams']:
                    result['slot_to_exams'][timeslot] = []
                result['slot_to_exams'][timeslot].append(exam_id)
            
            # Calculate proximity penalty
            result['proximity_penalty'] = self._calculate_proximity_penalty(
                result['exam_schedule']
            )
            
            print(f"Fixed timeslot solution found!")
            print(f"   Timeslots used: {result['timeslots_used']}")
            print(f"   Proximity penalty: {result['proximity_penalty']:.2f}")
            print(f"   Solve time: {solve_time:.2f}s")
        else:
            print(f"No solution with {fixed_timeslots} timeslots")
        
        return result
    
    def print_solution_summary(self, result: Dict):
        """Print detailed solution summary"""
        if not result['feasible']:
            print("No feasible solution to summarize")
            return
        
        print(f"\nSolution Summary:")
        print(f"{'='*50}")
        print(f"Status: {'OPTIMAL' if result['optimal'] else 'FEASIBLE'}")
        print(f"Timeslots used: {result['timeslots_used']}")
        print(f"Proximity penalty: {result['proximity_penalty']:.4f}")
        print(f"Solve time: {result['solve_time']:.2f} seconds")
        
        print(f"\nTimeslot Distribution:")
        for slot in sorted(result['slot_to_exams'].keys()):
            exams = result['slot_to_exams'][slot]
            print(f"   Slot {slot}: {len(exams)} exams ({exams[:5]}{'...' if len(exams) > 5 else ''})")

def test_cp_solver():
    """Test the CP solver with STA83 data"""
    print("Testing CP-SAT Solver for STA83")
    print("="*50)
    
    # Load data
    loader = STA83DataLoader()
    if not loader.load_data():
        print("Failed to load STA83 data")
        return
    
    print("STA83 data loaded successfully")
    
    # Create solver
    cp_solver = STA83CPSolver(loader)
    
    # Test 1: Find minimum timeslots
    print(f"\nTest 1: Finding minimum number of timeslots...")
    cp_solver.create_model(max_timeslots=20)
    result1 = cp_solver.solve(time_limit_seconds=120)
    
    if result1['feasible']:
        cp_solver.print_solution_summary(result1)
        
        # Test 2: Optimize with fixed timeslots
        min_timeslots = result1['timeslots_used']
        print(f"\nTest 2: Optimizing with fixed {min_timeslots} timeslots...")
        result2 = cp_solver.solve_with_fixed_timeslots(min_timeslots, time_limit_seconds=60)
        
        if result2['feasible']:
            cp_solver.print_solution_summary(result2)
            
            # Compare results
            print(f"\nComparison:")
            print(f"   Minimum timeslots approach: {result1['proximity_penalty']:.4f} penalty")
            print(f"   Fixed timeslots approach: {result2['proximity_penalty']:.4f} penalty")
        
    else:
        print("Could not find feasible solution")

if __name__ == "__main__":
    test_cp_solver() 