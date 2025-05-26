"""
Core Timetabling Logic for STA83 Exam Scheduling
Implements order-based decoding and proximity penalty calculation
"""
import numpy as np
from typing import Tuple, Dict, List

# Carter et al.'s proximity weights
PROXIMITY_WEIGHTS = {
    1: 16,  # 2^(5-1) = 16 penalty for exams 1 slot apart
    2: 8,   # 2^(5-2) = 8 penalty for exams 2 slots apart  
    3: 4,   # 2^(5-3) = 4 penalty for exams 3 slots apart
    4: 2,   # 2^(5-4) = 2 penalty for exams 4 slots apart
    5: 1    # 2^(5-5) = 1 penalty for exams 5 slots apart
}

def decode_permutation(permutation: np.ndarray, conflict_matrix: np.ndarray, num_exams: int) -> Tuple[Dict[int, int], int]:
    """
    Decodes an exam permutation using greedy timeslot assignment.
    
    Args:
        permutation: 1D array of exam IDs (1-indexed) in assignment order
        conflict_matrix: 2D array (num_exams x num_exams) representing conflicts (0-indexed)
        num_exams: Total number of exams
    
    Returns:
        exam_to_slot_map: Dictionary mapping exam_id (1-indexed) to timeslot (1-indexed)
        timeslots_used: Total number of timeslots used
    """
    exam_to_slot_map = {}
    # slot_to_exams: key is slot_id (1-indexed), value is list of exam_ids (1-indexed)
    slot_to_exams: Dict[int, List[int]] = {}
    current_max_slot = 0

    for exam_id_1_indexed in permutation:
        exam_idx_0_indexed = exam_id_1_indexed - 1
        placed_in_existing_slot = False

        # Try to place in an existing slot
        for slot_id in range(1, current_max_slot + 1):
            can_place_in_this_slot = True
            if slot_id in slot_to_exams:
                for scheduled_exam_id_1_indexed in slot_to_exams[slot_id]:
                    scheduled_exam_idx_0_indexed = scheduled_exam_id_1_indexed - 1
                    if conflict_matrix[exam_idx_0_indexed][scheduled_exam_idx_0_indexed] == 1:
                        can_place_in_this_slot = False
                        break
            
            if can_place_in_this_slot:
                exam_to_slot_map[exam_id_1_indexed] = slot_id
                # Ensure the list for the slot exists, though it should if current_max_slot is managed correctly.
                if slot_id not in slot_to_exams:
                    slot_to_exams[slot_id] = [] 
                slot_to_exams[slot_id].append(exam_id_1_indexed)
                placed_in_existing_slot = True
                break
        
        # If not placed, create a new slot
        if not placed_in_existing_slot:
            current_max_slot += 1
            exam_to_slot_map[exam_id_1_indexed] = current_max_slot
            slot_to_exams[current_max_slot] = [exam_id_1_indexed]
            
    timeslots_used = current_max_slot if exam_to_slot_map else 0
    return exam_to_slot_map, timeslots_used

def calculate_proximity_penalty(exam_to_slot_map: Dict[int, int], 
                               student_enrollments: List[List[int]], 
                               num_students: int) -> float:
    """
    Calculates the total proximity penalty for all students.
    
    Args:
        exam_to_slot_map: Dictionary mapping exam_id (1-indexed) to timeslot (1-indexed)
        student_enrollments: List of lists, each containing exam_ids for one student
        num_students: Total number of students
    
    Returns:
        total_penalty_sum: Sum of all proximity penalties across all students
    """
    total_penalty_sum = 0.0
    
    for student_exams in student_enrollments:
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
        
        total_penalty_sum += student_penalty
    
    return total_penalty_sum

def test_timetabling_logic():
    """Test the core timetabling functions with simple examples"""
    print("Testing Core Timetabling Logic")
    print("="*40)
    
    # Test 1: Simple 5-exam example
    print("\nTest 1: Simple 5-exam example")
    
    # Create a simple conflict matrix for 5 exams
    # Exams 1-2 conflict, 2-3 conflict, 4-5 conflict
    conflict_matrix = np.array([
        [0, 1, 0, 0, 0],  # Exam 1 conflicts with 2
        [1, 0, 1, 0, 0],  # Exam 2 conflicts with 1,3
        [0, 1, 0, 0, 0],  # Exam 3 conflicts with 2
        [0, 0, 0, 0, 1],  # Exam 4 conflicts with 5
        [0, 0, 0, 1, 0]   # Exam 5 conflicts with 4
    ])
    
    # Test permutation: [1, 2, 3, 4, 5]
    permutation = np.array([1, 2, 3, 4, 5])
    exam_to_slot_map, timeslots_used = decode_permutation(permutation, conflict_matrix, 5)
    
    print(f"Permutation: {permutation}")
    print(f"Exam to slot mapping: {exam_to_slot_map}")
    print(f"Timeslots used: {timeslots_used}")
    
    # Expected: Exam 1->slot 1, Exam 2->slot 2, Exam 3->slot 1, Exam 4->slot 1, Exam 5->slot 2
    # Or similar clash-free assignment
    
    # Test 2: Proximity penalty calculation
    print("\nTest 2: Proximity penalty calculation")
    
    # Simple student enrollments
    student_enrollments = [
        [1, 2],     # Student 1: exams 1,2 (1 slot apart -> 16 penalty)
        [1, 3],     # Student 2: exams 1,3 (if in slots 1,1 -> 0 penalty, if 1,2 -> 16 penalty)
        [4, 5]      # Student 3: exams 4,5 (if in different slots -> penalty)
    ]
    
    total_penalty = calculate_proximity_penalty(exam_to_slot_map, student_enrollments, 3)
    print(f"Student enrollments: {student_enrollments}")
    print(f"Total proximity penalty: {total_penalty}")
    
    # Test 3: Different permutation order
    print("\nTest 3: Different permutation order")
    
    permutation2 = np.array([3, 1, 5, 2, 4])
    exam_to_slot_map2, timeslots_used2 = decode_permutation(permutation2, conflict_matrix, 5)
    
    print(f"Permutation: {permutation2}")
    print(f"Exam to slot mapping: {exam_to_slot_map2}")
    print(f"Timeslots used: {timeslots_used2}")
    
    total_penalty2 = calculate_proximity_penalty(exam_to_slot_map2, student_enrollments, 3)
    print(f"Total proximity penalty: {total_penalty2}")
    
    print(f"\nCore timetabling logic tests completed!")
    print(f"Different permutations can lead to different objectives:")
    print(f"  Permutation 1: {timeslots_used} slots, {total_penalty} penalty")
    print(f"  Permutation 2: {timeslots_used2} slots, {total_penalty2} penalty")

if __name__ == "__main__":
    test_timetabling_logic()
