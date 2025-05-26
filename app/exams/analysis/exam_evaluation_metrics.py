import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import sys

# Add paths for imports if running standalone for testing
sys.path.append('.')
sys.path.append('../') # To access core, data_loader etc.

from app.exams.core.sta83_data_loader import STA83DataLoader
from app.exams.core.timetabling_core import calculate_proximity_penalty, decode_permutation

# Constants for proximity penalty, can be adjusted
PROXIMITY_WEIGHTS = {
    1: 16,  # One slot apart
    2: 8,   # Two slots apart
    3: 4,   # Three slots apart
    4: 2,   # Four slots apart
    5: 1    # Five slots apart
}
DEFAULT_SLOTS_PER_DAY = 5 # Assuming 5 slots constitute a day for daily load analysis

class ExamEvaluationMetrics:
    """
    Calculates and stores various evaluation metrics for an exam timetable.
    """

    def __init__(self, data_loader: STA83DataLoader, solution_permutation: np.ndarray, slots_per_day: int = DEFAULT_SLOTS_PER_DAY):
        """
        Initialize the evaluation metrics calculator.

        Args:
            data_loader: An instance of STA83DataLoader.
            solution_permutation: A numpy array representing the exam timetable (permutation of exam indices).
            slots_per_day: Number of timeslots considered as one day for daily load analysis.
        """
        if not isinstance(data_loader, STA83DataLoader):
            raise ValueError("data_loader must be an instance of STA83DataLoader.")
        if not isinstance(solution_permutation, np.ndarray):
            raise ValueError("solution_permutation must be a numpy array.")
        
        self.data_loader = data_loader
        self.solution_permutation = solution_permutation # 0-indexed exam IDs
        self.slots_per_day = slots_per_day
        
        self.num_exams = self.data_loader.num_exams
        self.num_students = self.data_loader.num_students
        
        # Ensure conflict_matrix is loaded and is an ndarray
        conflict_matrix = self.data_loader.conflict_matrix
        if conflict_matrix is None:
            raise ValueError("Conflict matrix not found in data_loader. Ensure data is loaded successfully.")
        self.conflict_matrix: np.ndarray = conflict_matrix # Explicitly type for clarity post-check
        
        self.student_enrollments = self.data_loader.student_enrollments # List of lists of 1-indexed exam IDs

        self.metrics: Dict[str, Any] = {}
        self._calculate_all_metrics()

    def _decode_solution(self) -> Tuple[Dict[int, int], int]:
        """Decodes the permutation into an exam-to-slot mapping and total timeslots used."""
        # By this point, self.conflict_matrix is guaranteed to be np.ndarray due to the check in __init__
        exam_to_slot_map, total_timeslots = decode_permutation(
            self.solution_permutation,
            self.conflict_matrix, # This should now be recognized as np.ndarray
            self.num_exams
        )
        return exam_to_slot_map, total_timeslots

    def _calculate_hard_constraints(self, exam_to_slot_map: Dict[int, int]) -> Dict[str, int]:
        """
        Calculates hard constraint violations (primarily student clashes).
        Note: The decode_permutation logic aims to create clash-free schedules.
              This serves as a verification or for alternative decoding schemes.
        """
        student_clashes = 0
        # exam_to_slot_map uses 0-indexed exam IDs and 0-indexed timeslots
        
        for student_idx in range(self.num_students):
            student_exam_ids = self.student_enrollments[student_idx] # 1-indexed exam IDs
            slot_occupancy: Dict[int, int] = {} # timeslot -> count of exams for this student
            
            for exam_id_1_indexed in student_exam_ids:
                exam_id_0_indexed = exam_id_1_indexed - 1
                if exam_id_0_indexed in exam_to_slot_map:
                    slot = exam_to_slot_map[exam_id_0_indexed]
                    if slot in slot_occupancy:
                        slot_occupancy[slot] += 1
                    else:
                        slot_occupancy[slot] = 1
            
            for slot, count in slot_occupancy.items():
                if count > 1:
                    student_clashes += (count - 1) # Each additional exam in the same slot is a clash

        return {
            "student_clashes": student_clashes
        }

    def _calculate_performance_metrics(self, exam_to_slot_map: Dict[int, int], total_timeslots_used: int) -> Dict[str, Any]:
        """Calculates core performance metrics like timeslots used and proximity penalty."""
        
        avg_proximity_penalty = calculate_proximity_penalty(
            exam_to_slot_map, # expects 0-indexed exam IDs to 0-indexed slots
            self.student_enrollments, # expects list of lists of 1-indexed exam IDs
            self.num_students
        )
        
        return {
            "total_timeslots_used": total_timeslots_used,
            "average_proximity_penalty_per_student": avg_proximity_penalty,
        }

    def _calculate_detailed_proximity_analysis(self, exam_to_slot_map: Dict[int, int]) -> Dict[str, Any]:
        """Calculates detailed breakdown of proximity penalties."""
        student_penalties: List[float] = []
        
        for student_idx in range(self.num_students):
            student_exam_ids_1_indexed = self.student_enrollments[student_idx]
            
            # Create a temporary map for this student's exams and their slots
            student_single_exam_to_slot_map: Dict[int, int] = {}
            for exam_id_1_indexed in student_exam_ids_1_indexed:
                exam_id_0_indexed = exam_id_1_indexed - 1
                if exam_id_0_indexed in exam_to_slot_map:
                    student_single_exam_to_slot_map[exam_id_0_indexed] = exam_to_slot_map[exam_id_0_indexed]
            
            if not student_single_exam_to_slot_map:
                student_penalties.append(0.0)
                continue

            # Use the main penalty function for a single student
            # We pass only this student's enrollments (as a list containing one list)
            # and num_students as 1.
            penalty = calculate_proximity_penalty(
                student_single_exam_to_slot_map,
                [student_exam_ids_1_indexed], # This specific student's exams
                1 # Calculating for one student
            )
            student_penalties.append(penalty)

        max_penalty = 0.0
        penalty_distribution = {
            "level_0_0_penalty": 0,
            "level_1_1_5_penalty": 0,
            "level_2_6_10_penalty": 0,
            "level_3_11_20_penalty": 0,
            "level_4_gt_20_penalty": 0,
        }
        students_with_zero_penalty = 0
        students_high_penalty_count = 0
        high_penalty_threshold = 20 # Example threshold

        if student_penalties: # Check if list is not empty
            max_penalty = max(student_penalties)
            for penalty_value in student_penalties:
                if penalty_value == 0:
                    penalty_distribution["level_0_0_penalty"] += 1
                    students_with_zero_penalty += 1
                elif 1 <= penalty_value <= 5:
                    penalty_distribution["level_1_1_5_penalty"] += 1
                elif 6 <= penalty_value <= 10:
                    penalty_distribution["level_2_6_10_penalty"] += 1
                elif 11 <= penalty_value <= 20:
                    penalty_distribution["level_3_11_20_penalty"] += 1
                else: # penalty_value > 20
                    penalty_distribution["level_4_gt_20_penalty"] += 1
                
                if penalty_value > high_penalty_threshold:
                    students_high_penalty_count += 1
        
        percentage_zero_penalty = (students_with_zero_penalty / self.num_students) * 100 if self.num_students > 0 else 0

        return {
            "max_proximity_penalty_for_student": max_penalty,
            "student_proximity_penalty_distribution": penalty_distribution,
            "percentage_students_zero_penalty": percentage_zero_penalty,
            "students_exceeding_high_penalty_threshold": students_high_penalty_count,
            "high_penalty_threshold_value": high_penalty_threshold
        }

    def _calculate_daily_load_analysis(self, exam_to_slot_map: Dict[int, int]) -> Dict[str, Any]:
        """Analyzes student exam load per day."""
        if self.slots_per_day <= 0:
            return {
                "error": "slots_per_day must be positive for daily load analysis."
            }

        student_daily_loads: Dict[int, Dict[int, int]] = {i: {} for i in range(self.num_students)} # student_idx -> {day_idx: exam_count}

        for student_idx in range(self.num_students):
            student_exam_ids = self.student_enrollments[student_idx] # 1-indexed
            for exam_id_1_indexed in student_exam_ids:
                exam_id_0_indexed = exam_id_1_indexed - 1
                if exam_id_0_indexed in exam_to_slot_map:
                    slot = exam_to_slot_map[exam_id_0_indexed]
                    day_idx = slot // self.slots_per_day
                    student_daily_loads[student_idx][day_idx] = student_daily_loads[student_idx].get(day_idx, 0) + 1
        
        max_exams_single_day_for_any_student = 0
        total_active_student_days = 0
        total_exams_on_active_days = 0
        students_with_excessive_daily_load = 0
        excessive_load_threshold = 3 # e.g., more than 3 exams a day is excessive

        for student_idx in range(self.num_students):
            if not student_daily_loads[student_idx]:
                continue
            
            current_student_max_daily = max(student_daily_loads[student_idx].values())
            if current_student_max_daily > max_exams_single_day_for_any_student:
                max_exams_single_day_for_any_student = current_student_max_daily
            
            if current_student_max_daily > excessive_load_threshold:
                students_with_excessive_daily_load += 1
            
            for day, count in student_daily_loads[student_idx].items():
                total_active_student_days += 1
                total_exams_on_active_days += count
        
        average_exams_per_active_day = (total_exams_on_active_days / total_active_student_days) if total_active_student_days > 0 else 0
        
        return {
            "max_exams_single_day_for_any_student": max_exams_single_day_for_any_student,
            "average_exams_per_student_on_active_days": average_exams_per_active_day,
            "students_with_excessive_daily_load": students_with_excessive_daily_load,
            "excessive_daily_load_threshold": excessive_load_threshold,
            "slots_per_day_definition": self.slots_per_day
        }

    def _calculate_all_metrics(self):
        """Calculates all defined metrics and stores them."""
        exam_to_slot_map, total_timeslots_used = self._decode_solution()

        self.metrics["hard_constraints"] = self._calculate_hard_constraints(exam_to_slot_map)
        self.metrics["performance"] = self._calculate_performance_metrics(exam_to_slot_map, total_timeslots_used)
        self.metrics["detailed_proximity"] = self._calculate_detailed_proximity_analysis(exam_to_slot_map)
        self.metrics["daily_load"] = self._calculate_daily_load_analysis(exam_to_slot_map)
        self.metrics["solution_permutation"] = self.solution_permutation.tolist() # For storage/review
        self.metrics["exam_to_slot_map_generated"] = exam_to_slot_map # For review

    def get_metrics(self) -> Dict[str, Any]:
        """Returns all calculated metrics."""
        return self.metrics

    def print_summary(self):
        """Prints a summary of the calculated metrics."""
        print("--- Exam Timetable Evaluation Summary ---")
        
        hc = self.metrics.get("hard_constraints", {})
        print(f"\n[Hard Constraints]")
        print(f"  Student Clashes: {hc.get('student_clashes', 'N/A')}")

        perf = self.metrics.get("performance", {})
        print(f"\n[Performance Metrics]")
        print(f"  Total Timeslots Used: {perf.get('total_timeslots_used', 'N/A')}")
        print(f"  Avg Proximity Penalty per Student: {perf.get('average_proximity_penalty_per_student', 'N/A'):.4f}")

        prox = self.metrics.get("detailed_proximity", {})
        print(f"\n[Detailed Proximity Analysis]")
        print(f"  Max Proximity Penalty for a Student: {prox.get('max_proximity_penalty_for_student', 'N/A'):.2f}")
        print(f"  Percentage of Students with Zero Penalty: {prox.get('percentage_students_zero_penalty', 'N/A'):.2f}%")
        print(f"  Students Exceeding High Penalty Threshold ({prox.get('high_penalty_threshold_value', 'N/A')}): {prox.get('students_exceeding_high_penalty_threshold', 'N/A')}")
        print(f"  Student Penalty Distribution: {prox.get('student_proximity_penalty_distribution', {})}")
        
        daily = self.metrics.get("daily_load", {})
        if "error" in daily:
            print(f"\n[Daily Load Analysis (Slots per day: {self.slots_per_day})]")
            print(f"  Error: {daily['error']}")
        else:
            print(f"\n[Daily Load Analysis (Slots per day: {self.slots_per_day})]")
            print(f"  Max Exams on a Single Day for Any Student: {daily.get('max_exams_single_day_for_any_student', 'N/A')}")
            print(f"  Avg Exams per Student on Active Days: {daily.get('average_exams_per_student_on_active_days', 'N/A'):.2f}")
            print(f"  Students with >{daily.get('excessive_daily_load_threshold', 'N/A')} Exams in a Day: {daily.get('students_with_excessive_daily_load', 'N/A')}")
        
        print("\n--- End of Summary ---")


def test_exam_evaluation_metrics():
    """
    Test function for ExamEvaluationMetrics.
    This requires a valid STA83DataLoader and a sample solution permutation.
    """
    print("Testing ExamEvaluationMetrics...")
    try:
        # Setup: Requires data files to be accessible from this script's location or via adjusted path
        # Adjust path as necessary if running from a different directory
        crs_file_path = '../data/sta-f-83.crs'
        stu_file_path = '../data/sta-f-83.stu'
        
        data_loader = STA83DataLoader(crs_file=crs_file_path, stu_file=stu_file_path)
        if not data_loader.load_data():
            print("Failed to load data for testing. Ensure .crs and .stu files are correctly pathed.")
            return

        # Create a sample random permutation (0-indexed exam IDs)
        # In a real scenario, this would come from an algorithm's output
        sample_permutation = np.random.permutation(data_loader.num_exams)
        
        print(f"Number of exams: {data_loader.num_exams}")
        print(f"Sample permutation (first 10): {sample_permutation[:10]}")

        evaluator = ExamEvaluationMetrics(data_loader, sample_permutation, slots_per_day=5)
        metrics = evaluator.get_metrics()
        
        evaluator.print_summary()

        # Basic checks
        assert "hard_constraints" in metrics
        assert "performance" in metrics
        assert "detailed_proximity" in metrics
        assert "daily_load" in metrics
        assert metrics["performance"]["total_timeslots_used"] > 0
        
        print("\nExamEvaluationMetrics test completed successfully.")
        
    except FileNotFoundError:
        print("Error: STA-F-83 data files not found. Make sure they are in the expected 'data' directory relative to 'exams' or adjust path in test.")
    except Exception as e:
        print(f"An error occurred during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # This allows running the test directly
    # Ensure paths in test_exam_evaluation_metrics are correct for standalone execution
    test_exam_evaluation_metrics() 