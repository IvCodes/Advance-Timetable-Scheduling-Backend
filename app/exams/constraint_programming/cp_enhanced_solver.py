#!/usr/bin/env python3
"""
Enhanced CP-SAT Solver with Direct Penalty Optimization and MOEA Integration
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
from constraint_programming.cp_sta83_solver import STA83CPSolver

class EnhancedSTA83CPSolver(STA83CPSolver):
    """
    Enhanced CP solver with direct penalty optimization and MOEA integration
    """
    
    def __init__(self, data_loader: STA83DataLoader):
        super().__init__(data_loader)
        self.penalty_vars = {}  # Variables for penalty calculation
        self.slot_diff_vars = {}  # Variables for slot differences
        
    def create_penalty_optimization_model(self, fixed_timeslots: int) -> cp_model.CpModel:
        """
        Create CP model that directly optimizes proximity penalty
        
        Args:
            fixed_timeslots: Fixed number of timeslots to use
            
        Returns:
            CP model that minimizes penalty directly
        """
        print(f"\nCreating penalty optimization model with {fixed_timeslots} timeslots...")
        
        self.model = cp_model.CpModel()
        self.conflicting_pairs = self._extract_conflicts()
        
        # 1. Create exam timeslot variables
        print("Creating exam timeslot variables...")
        for exam_id in range(1, self.num_exams + 1):
            var_name = f"T_{exam_id}"
            self.exam_timeslot_vars[exam_id] = self.model.NewIntVar(
                0, fixed_timeslots - 1, var_name
            )
        
        # 2. Add conflict constraints
        print("Adding conflict constraints...")
        for exam1_id, exam2_id in self.conflicting_pairs:
            self.model.Add(
                self.exam_timeslot_vars[exam1_id] != self.exam_timeslot_vars[exam2_id]
            )
        
        # 3. Create penalty optimization variables and constraints
        print("Creating penalty optimization variables...")
        penalty_terms = []
        penalty_weights = {1: 16, 2: 8, 3: 4, 4: 2, 5: 1}
        
        # Handle both dict and list formats for student enrollments
        if isinstance(self.student_enrollments, dict):
            student_data = self.student_enrollments.items()
        else:
            student_data = enumerate(self.student_enrollments)
        
        constraint_count = 0
        for student_id, exams in student_data:
            if len(exams) < 2:
                continue
                
            # For each pair of exams this student takes
            for i in range(len(exams)):
                for j in range(i + 1, len(exams)):
                    exam1_id = exams[i]
                    exam2_id = exams[j]
                    
                    # Create variable for slot difference
                    diff_var = self.model.NewIntVar(0, fixed_timeslots - 1, 
                                                   f"diff_{student_id}_{exam1_id}_{exam2_id}")
                    
                    # Constraint: diff_var = |slot[exam1] - slot[exam2]|
                    self.model.AddAbsEquality(diff_var, 
                                            self.exam_timeslot_vars[exam1_id] - 
                                            self.exam_timeslot_vars[exam2_id])
                    
                    # Create penalty contribution variables for each possible difference
                    for slot_diff in range(1, 6):  # Only differences 1-5 contribute to penalty
                        if slot_diff in penalty_weights:
                            # Boolean variable: is the difference exactly slot_diff?
                            is_diff_k = self.model.NewBoolVar(f"is_diff_{slot_diff}_{student_id}_{exam1_id}_{exam2_id}")
                            
                            # Constraint: is_diff_k == 1 iff diff_var == slot_diff
                            self.model.Add(diff_var == slot_diff).OnlyEnforceIf(is_diff_k)
                            self.model.Add(diff_var != slot_diff).OnlyEnforceIf(is_diff_k.Not())
                            
                            # Add penalty contribution
                            penalty_terms.append(is_diff_k * penalty_weights[slot_diff])
                            constraint_count += 1
        
        print(f"Created {constraint_count} penalty constraints")
        
        # 4. Set objective: minimize total penalty
        if penalty_terms:
            total_penalty = sum(penalty_terms)
            self.model.Minimize(total_penalty)
            print(f"Objective: minimize sum of {len(penalty_terms)} penalty terms")
        else:
            print("WARNING: No penalty terms created - using feasibility only")
        
        return self.model
    
    def solve_penalty_optimization(self, fixed_timeslots: int, time_limit_seconds: int = 300) -> Dict:
        """
        Solve with direct penalty optimization
        
        Args:
            fixed_timeslots: Fixed number of timeslots
            time_limit_seconds: Time limit for solving
            
        Returns:
            Solution dictionary
        """
        print(f"\nSolving penalty optimization model...")
        
        # Create the penalty optimization model
        self.create_penalty_optimization_model(fixed_timeslots)
        
        # Solve
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = time_limit_seconds
        self.solver.parameters.log_search_progress = False  # Reduce output for complex model
        
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
            'proximity_penalty': None,
            'cp_optimized_penalty': True  # Flag to indicate this was directly optimized
        }
        
        if result['feasible']:
            # Extract solution
            for exam_id in range(1, self.num_exams + 1):
                timeslot = self.solver.Value(self.exam_timeslot_vars[exam_id])
                result['exam_schedule'][exam_id] = timeslot
                
                if timeslot not in result['slot_to_exams']:
                    result['slot_to_exams'][timeslot] = []
                result['slot_to_exams'][timeslot].append(exam_id)
            
            # Calculate proximity penalty (should match CP objective)
            result['proximity_penalty'] = self._calculate_proximity_penalty(
                result['exam_schedule']
            )
            
            print(f"Penalty-optimized solution found!")
            print(f"   Status: {'OPTIMAL' if result['optimal'] else 'FEASIBLE'}")
            print(f"   Timeslots used: {result['timeslots_used']}")
            print(f"   Optimized penalty: {result['proximity_penalty']:.4f}")
            print(f"   Solve time: {solve_time:.2f}s")
        else:
            print(f"No penalty-optimized solution found")
            print(f"   Status: {self._status_name(status)}")
        
        return result
    
    def export_solution_for_moea(self, result: Dict, filename: Optional[str] = None) -> np.ndarray:
        """
        Export CP solution in format suitable for seeding MOEAs
        
        Args:
            result: Solution dictionary from CP solver
            filename: Optional file to save the solution
            
        Returns:
            Permutation array suitable for MOEA seeding
        """
        if not result['feasible']:
            raise ValueError("Cannot export infeasible solution")
        
        # Convert exam schedule to permutation format
        # Sort exams by their assigned timeslots, then by exam ID for consistency
        exam_schedule = result['exam_schedule']
        
        # Create list of (timeslot, exam_id) pairs
        exam_timeslot_pairs = [(timeslot, exam_id) for exam_id, timeslot in exam_schedule.items()]
        
        # Sort by timeslot first, then by exam_id
        exam_timeslot_pairs.sort(key=lambda x: (x[0], x[1]))
        
        # Extract just the exam IDs in the sorted order
        permutation = [exam_id for _, exam_id in exam_timeslot_pairs]
        
        # Convert to numpy array (adjust indices to 0-based for MOEA)
        permutation_array = np.array([exam_id - 1 for exam_id in permutation])
        
        if filename:
            np.save(filename, permutation_array)
            print(f"Solution exported to {filename}")
        
        print(f"Exported permutation: first 10 elements = {permutation_array[:10]}")
        return permutation_array
    
    def create_multiple_solutions(self, fixed_timeslots: int, num_solutions: int = 5) -> List[Dict]:
        """
        Create multiple diverse solutions for the same timeslot constraint
        
        Args:
            fixed_timeslots: Number of timeslots to use
            num_solutions: Number of different solutions to generate
            
        Returns:
            List of solution dictionaries
        """
        solutions = []
        
        for i in range(num_solutions):
            print(f"\nGenerating solution {i+1}/{num_solutions}...")
            
            # Use different random seeds or solver parameters for diversity
            result = self.solve_penalty_optimization(fixed_timeslots, time_limit_seconds=60)
            
            if result['feasible']:
                solutions.append(result)
                print(f"Solution {i+1}: penalty = {result['proximity_penalty']:.4f}")
            else:
                print(f"Solution {i+1}: infeasible")
        
        print(f"\nGenerated {len(solutions)} feasible solutions")
        return solutions

def test_enhanced_cp_solver():
    """Test the enhanced CP solver"""
    print("Testing Enhanced CP Solver")
    print("=" * 40)
    
    # Load data
    data_loader = STA83DataLoader()
    if not data_loader.load_data():
        print("Failed to load data")
        return
    
    print(f"Loaded {data_loader.num_exams} exams, {data_loader.num_students} students")
    
    # Create enhanced solver
    solver = EnhancedSTA83CPSolver(data_loader)
    
    # Test penalty optimization
    print("\nTesting penalty optimization...")
    result = solver.solve_penalty_optimization(fixed_timeslots=13, time_limit_seconds=120)
    
    if result['feasible']:
        print("\nSolution found!")
        solver.print_solution_summary(result)
        
        # Export for MOEA
        print("\nExporting solution for MOEA...")
        permutation = solver.export_solution_for_moea(result, "test_cp_solution.npy")
        print(f"Exported permutation shape: {permutation.shape}")
    else:
        print("No solution found")

if __name__ == "__main__":
    test_enhanced_cp_solver() 