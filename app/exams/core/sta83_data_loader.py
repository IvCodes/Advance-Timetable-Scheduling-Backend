"""
STA83 Data Loader for Exam Timetabling
Wraps the data loading functionality for the STA83 benchmark problem
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
import os

class STA83DataLoader:
    """
    Data loader for the STA83 exam timetabling benchmark problem
    """
    
    def __init__(self, crs_file: str = 'data/sta-f-83.crs', stu_file: str = 'data/sta-f-83.stu'):
        """
        Initialize the data loader
        
        Args:
            crs_file: Path to the .crs file (exam details)
            stu_file: Path to the .stu file (student enrollments)
        """
        self.crs_file = crs_file
        self.stu_file = stu_file
        
        # Data storage
        self.exam_student_counts: Dict[int, int] = {}
        self.student_enrollments: List[List[int]] = []
        self.conflict_matrix: Optional[np.ndarray] = None
        
        # Problem dimensions
        self.num_exams: int = 0
        self.num_students: int = 0
        
        # Load status
        self.is_loaded: bool = False
    
    def load_data(self) -> bool:
        """
        Load and parse the STA83 dataset
        
        Returns:
            True if data loaded successfully, False otherwise
        """
        try:
            # Load file contents
            crs_data = self._load_string_from_file(self.crs_file)
            stu_data = self._load_string_from_file(self.stu_file)
            
            if not crs_data or not stu_data:
                return False
            
            # Parse data
            self.exam_student_counts, max_exam_id = self._parse_crs_data(crs_data)
            self.student_enrollments = self._parse_stu_data(stu_data)
            
            # Set problem dimensions
            self.num_exams = max_exam_id
            self.num_students = len(self.student_enrollments)
            
            # Build conflict matrix
            self.conflict_matrix = self._build_conflict_matrix()
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"Error loading STA83 data: {e}")
            return False
    
    def _load_string_from_file(self, filename: str) -> Optional[str]:
        """Load file content as string"""
        try:
            with open(filename, 'r') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            return None
    
    def _parse_crs_data(self, crs_string_data: str) -> Tuple[Dict[int, int], int]:
        """Parse .crs file content"""
        exam_student_counts = {}
        lines = crs_string_data.strip().split('\n')
        max_exam_id = 0
        
        for line in lines:
            if not line.strip() or "crs" in line.lower():
                continue
            parts = line.split()
            if len(parts) == 2:
                try:
                    exam_id = int(parts[0])
                    student_count = int(parts[1])
                    exam_student_counts[exam_id] = student_count
                    if exam_id > max_exam_id:
                        max_exam_id = exam_id
                except ValueError:
                    print(f"Skipping malformed crs line: {line}")
        
        return exam_student_counts, max_exam_id
    
    def _parse_stu_data(self, stu_string_data: str) -> List[List[int]]:
        """Parse .stu file content"""
        student_enrollments = []
        lines = stu_string_data.strip().split('\n')
        
        for line in lines:
            if not line.strip() or "stu" in line.lower():
                continue
            cleaned_line = line.replace('\xa0', ' ').strip()
            parts = cleaned_line.split()
            if parts:
                try:
                    student_exams = [int(exam_id) for exam_id in parts]
                    student_enrollments.append(student_exams)
                except ValueError:
                    print(f"Skipping malformed stu line: {line}")
        
        return student_enrollments
    
    def _build_conflict_matrix(self) -> np.ndarray:
        """Build conflict matrix from student enrollments"""
        conflict_matrix = np.zeros((self.num_exams, self.num_exams), dtype=int)
        
        for student_exams in self.student_enrollments:
            for i in range(len(student_exams)):
                for j in range(i + 1, len(student_exams)):
                    exam1_id = student_exams[i]
                    exam2_id = student_exams[j]
                    idx1 = exam1_id - 1  # Convert to 0-indexed
                    idx2 = exam2_id - 1
                    
                    if 0 <= idx1 < self.num_exams and 0 <= idx2 < self.num_exams:
                        conflict_matrix[idx1][idx2] = 1
                        conflict_matrix[idx2][idx1] = 1
        
        return conflict_matrix
    
    def analyze_dataset(self) -> Dict:
        """Analyze the loaded dataset and return statistics"""
        if not self.is_loaded:
            raise RuntimeError("Data not loaded. Call load_data() first.")
        
        # Calculate conflict density
        num_conflicting_pairs = np.sum(np.triu(self.conflict_matrix, k=1))
        possible_pairs = self.num_exams * (self.num_exams - 1) / 2
        conflict_density = num_conflicting_pairs / possible_pairs
        
        # Calculate average exams per student
        avg_exams_per_student = np.mean([len(enrollments) for enrollments in self.student_enrollments])
        
        # Calculate exam size statistics
        exam_sizes = list(self.exam_student_counts.values())
        
        analysis = {
            'num_exams': self.num_exams,
            'num_students': self.num_students,
            'conflict_density': conflict_density,
            'num_conflicting_pairs': int(num_conflicting_pairs),
            'avg_exams_per_student': avg_exams_per_student,
            'exam_size_stats': {
                'min': min(exam_sizes),
                'max': max(exam_sizes),
                'mean': np.mean(exam_sizes),
                'std': np.std(exam_sizes)
            }
        }
        
        return analysis
    
    def get_exam_list(self) -> List[int]:
        """Get list of all exam IDs"""
        if not self.is_loaded:
            raise RuntimeError("Data not loaded. Call load_data() first.")
        return list(range(1, self.num_exams + 1))

if __name__ == "__main__":
    # Test the data loader
    print("Testing STA83 Data Loader")
    print("="*40)
    
    loader = STA83DataLoader()
    
    if loader.load_data():
        print("Data loaded successfully!")
        
        analysis = loader.analyze_dataset()
        print(f"\nDataset Analysis:")
        print(f"   Exams: {analysis['num_exams']}")
        print(f"   Students: {analysis['num_students']}")
        print(f"   Conflict density: {analysis['conflict_density']:.4f}")
        print(f"   Conflicting pairs: {analysis['num_conflicting_pairs']}")
        print(f"   Avg exams per student: {analysis['avg_exams_per_student']:.2f}")
        print(f"   Exam sizes - Min: {analysis['exam_size_stats']['min']}, Max: {analysis['exam_size_stats']['max']}, Mean: {analysis['exam_size_stats']['mean']:.1f}")
    else:
        print("Failed to load data") 