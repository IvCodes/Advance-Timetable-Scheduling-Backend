"""
Enhanced STA83 Data Loader with Student ID Mapping
Extends the basic data loader to include key-value pairs for student IDs and exam assignments
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.sta83_data_loader import STA83DataLoader

class EnhancedSTA83DataLoader(STA83DataLoader):
    """
    Enhanced data loader that includes student ID mappings and key-value pairs
    for better HTML timetable visualization
    """
    
    def __init__(self, crs_file: str = 'data/sta-f-83.crs', stu_file: str = 'data/sta-f-83.stu'):
        """
        Initialize the enhanced data loader
        
        Args:
            crs_file: Path to the .crs file (exam details)
            stu_file: Path to the .stu file (student enrollments)
        """
        super().__init__(crs_file, stu_file)
        
        # Enhanced data structures with key-value pairs
        self.student_id_to_exams: Dict[str, List[int]] = {}  # Student ID -> List of exam IDs
        self.exam_id_to_students: Dict[int, List[str]] = {}  # Exam ID -> List of student IDs
        self.student_id_to_slots: Dict[str, List[int]] = {}  # Student ID -> List of assigned slots
        self.slot_to_students: Dict[int, Set[str]] = {}      # Slot -> Set of student IDs
        
        # Student ID generation settings
        self.student_id_prefix = "IT"
        self.student_id_start = 20000
        
    def load_data(self) -> bool:
        """
        Load and parse the STA83 dataset with enhanced student ID mapping
        
        Returns:
            True if data loaded successfully, False otherwise
        """
        # First load the basic data
        if not super().load_data():
            return False
        
        # Now enhance with student ID mappings
        self._create_student_id_mappings()
        self._create_exam_to_student_mappings()
        
        return True
    
    def _create_student_id_mappings(self):
        """Create mappings from student indices to formatted student IDs"""
        self.student_id_to_exams = {}
        
        for student_idx, exam_list in enumerate(self.student_enrollments):
            # Generate student ID (IT20001, IT20002, etc.)
            student_id = f"{self.student_id_prefix}{self.student_id_start + student_idx + 1:05d}"
            self.student_id_to_exams[student_id] = exam_list.copy()
    
    def _create_exam_to_student_mappings(self):
        """Create reverse mappings from exams to student IDs"""
        self.exam_id_to_students = {}
        
        # Initialize exam mappings
        for exam_id in range(1, self.num_exams + 1):
            self.exam_id_to_students[exam_id] = []
        
        # Populate mappings
        for student_id, exam_list in self.student_id_to_exams.items():
            for exam_id in exam_list:
                if exam_id in self.exam_id_to_students:
                    self.exam_id_to_students[exam_id].append(student_id)
    
    def assign_student_slots(self, exam_to_slot_map: Dict[int, int]):
        """
        Assign timeslots to students based on exam schedule
        
        Args:
            exam_to_slot_map: Dictionary mapping exam_id -> timeslot
        """
        self.student_id_to_slots = {}
        self.slot_to_students = {}
        
        # Initialize slot mappings
        for slot in exam_to_slot_map.values():
            self.slot_to_students[slot] = set()
        
        # Assign slots to students
        for student_id, exam_list in self.student_id_to_exams.items():
            student_slots = []
            for exam_id in exam_list:
                if exam_id in exam_to_slot_map:
                    slot = exam_to_slot_map[exam_id]
                    student_slots.append(slot)
                    self.slot_to_students[slot].add(student_id)
            
            self.student_id_to_slots[student_id] = sorted(list(set(student_slots)))
    
    def get_students_for_exam(self, exam_id: int) -> List[str]:
        """
        Get list of student IDs enrolled in a specific exam
        
        Args:
            exam_id: The exam ID to query
            
        Returns:
            List of student IDs enrolled in the exam
        """
        return self.exam_id_to_students.get(exam_id, [])
    
    def get_exams_for_student(self, student_id: str) -> List[int]:
        """
        Get list of exam IDs for a specific student
        
        Args:
            student_id: The student ID to query
            
        Returns:
            List of exam IDs the student is enrolled in
        """
        return self.student_id_to_exams.get(student_id, [])
    
    def get_slots_for_student(self, student_id: str) -> List[int]:
        """
        Get list of timeslots assigned to a specific student
        
        Args:
            student_id: The student ID to query
            
        Returns:
            List of timeslots assigned to the student
        """
        return self.student_id_to_slots.get(student_id, [])
    
    def get_students_in_slot(self, slot: int) -> List[str]:
        """
        Get list of student IDs assigned to a specific timeslot
        
        Args:
            slot: The timeslot to query
            
        Returns:
            List of student IDs assigned to the timeslot
        """
        return sorted(list(self.slot_to_students.get(slot, set())))
    
    def get_student_schedule_summary(self, student_id: str) -> Dict:
        """
        Get a comprehensive schedule summary for a student
        
        Args:
            student_id: The student ID to query
            
        Returns:
            Dictionary with student's complete schedule information
        """
        if student_id not in self.student_id_to_exams:
            return {}
        
        exams = self.get_exams_for_student(student_id)
        slots = self.get_slots_for_student(student_id)
        
        return {
            'student_id': student_id,
            'total_exams': len(exams),
            'exam_ids': exams,
            'timeslots': slots,
            'total_slots': len(slots),
            'exam_to_slot': {exam: slot for exam, slot in zip(exams, slots) if hasattr(self, 'current_exam_to_slot_map')}
        }
    
    def get_exam_details_with_students(self, exam_id: int) -> Dict:
        """
        Get detailed information about an exam including enrolled students
        
        Args:
            exam_id: The exam ID to query
            
        Returns:
            Dictionary with exam details and student information
        """
        students = self.get_students_for_exam(exam_id)
        student_count = self.exam_student_counts.get(exam_id, 0)
        
        return {
            'exam_id': exam_id,
            'student_count': student_count,
            'enrolled_students': students,
            'verified_count': len(students),
            'count_matches': student_count == len(students)
        }
    
    def export_student_exam_mapping(self, filename: str = "student_exam_mapping.csv"):
        """
        Export student-exam mappings to CSV file
        
        Args:
            filename: Output filename for the CSV
        """
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Student_ID', 'Exam_IDs', 'Total_Exams'])
            
            for student_id, exam_list in self.student_id_to_exams.items():
                exam_ids_str = ';'.join(map(str, exam_list))
                writer.writerow([student_id, exam_ids_str, len(exam_list)])
        
        print(f"Student-exam mapping exported to {filename}")
    
    def export_exam_student_mapping(self, filename: str = "exam_student_mapping.csv"):
        """
        Export exam-student mappings to CSV file
        
        Args:
            filename: Output filename for the CSV
        """
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Exam_ID', 'Student_IDs', 'Total_Students'])
            
            for exam_id in sorted(self.exam_id_to_students.keys()):
                student_list = self.exam_id_to_students[exam_id]
                student_ids_str = ';'.join(student_list)
                writer.writerow([exam_id, student_ids_str, len(student_list)])
        
        print(f"Exam-student mapping exported to {filename}")
    
    def analyze_enhanced_dataset(self) -> Dict:
        """
        Analyze the enhanced dataset and return comprehensive statistics
        
        Returns:
            Dictionary with enhanced analysis including student ID mappings
        """
        basic_analysis = super().analyze_dataset()
        
        # Enhanced analysis
        student_exam_counts = [len(exams) for exams in self.student_id_to_exams.values()]
        exam_student_counts = [len(students) for students in self.exam_id_to_students.values()]
        
        enhanced_analysis = {
            **basic_analysis,
            'student_id_mappings': {
                'total_students_mapped': len(self.student_id_to_exams),
                'student_id_prefix': self.student_id_prefix,
                'student_id_range': f"{self.student_id_prefix}{self.student_id_start + 1:05d} - {self.student_id_prefix}{self.student_id_start + len(self.student_id_to_exams):05d}"
            },
            'student_exam_distribution': {
                'min_exams_per_student': min(student_exam_counts) if student_exam_counts else 0,
                'max_exams_per_student': max(student_exam_counts) if student_exam_counts else 0,
                'avg_exams_per_student': np.mean(student_exam_counts) if student_exam_counts else 0,
                'std_exams_per_student': np.std(student_exam_counts) if student_exam_counts else 0
            },
            'exam_student_distribution': {
                'min_students_per_exam': min(exam_student_counts) if exam_student_counts else 0,
                'max_students_per_exam': max(exam_student_counts) if exam_student_counts else 0,
                'avg_students_per_exam': np.mean(exam_student_counts) if exam_student_counts else 0,
                'std_students_per_exam': np.std(exam_student_counts) if exam_student_counts else 0
            }
        }
        
        return enhanced_analysis

if __name__ == "__main__":
    # Test the enhanced data loader
    print("Testing Enhanced STA83 Data Loader")
    print("="*50)
    
    loader = EnhancedSTA83DataLoader()
    
    if loader.load_data():
        print("✅ Enhanced data loaded successfully!")
        
        # Basic analysis
        analysis = loader.analyze_enhanced_dataset()
        print(f"\n📊 Enhanced Dataset Analysis:")
        print(f"   Exams: {analysis['num_exams']}")
        print(f"   Students: {analysis['num_students']}")
        print(f"   Student ID Range: {analysis['student_id_mappings']['student_id_range']}")
        print(f"   Avg exams per student: {analysis['student_exam_distribution']['avg_exams_per_student']:.2f}")
        print(f"   Avg students per exam: {analysis['exam_student_distribution']['avg_students_per_exam']:.1f}")
        
        # Test specific queries
        print(f"\n🔍 Sample Queries:")
        sample_student = list(loader.student_id_to_exams.keys())[0]
        sample_exam = 3  # Exam with many students
        
        print(f"   Student {sample_student} enrolled in: {loader.get_exams_for_student(sample_student)}")
        print(f"   Exam {sample_exam} has students: {loader.get_students_for_exam(sample_exam)[:5]}... (showing first 5)")
        
        # Export mappings
        print(f"\n💾 Exporting mappings...")
        loader.export_student_exam_mapping()
        loader.export_exam_student_mapping()
        
    else:
        print("❌ Failed to load enhanced data") 