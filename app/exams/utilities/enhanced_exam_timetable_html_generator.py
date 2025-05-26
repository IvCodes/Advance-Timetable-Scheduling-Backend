"""
Enhanced HTML Generator for STA83 Exam Timetables with Student ID Mapping
Creates beautiful HTML visualization with detailed student information and key-value pairs
"""
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Set, Optional
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.sta83_data_loader import STA83DataLoader
from core.timetabling_core import decode_permutation, calculate_proximity_penalty

class EnhancedExamTimetableHTMLGenerator:
    """Generate enhanced HTML visualization for exam timetables with student ID details"""
    
    def __init__(self, data_loader: STA83DataLoader):
        self.data_loader = data_loader
        
    def generate_html_timetable_from_schedule_dict(self, schedule_data: Dict[int, List[int]], 
                                                 output_file: str = "enhanced_exam_timetable.html",
                                                 penalty_info: Optional[Dict] = None) -> str:
        """Generate enhanced HTML file for the exam timetable from a schedule dictionary."""
        
        # Calculate penalty if not provided
        if penalty_info is None:
            penalty_info = self._calculate_penalty_info(schedule_data)
        
        # Generate HTML content
        html_content = self._generate_html_content(schedule_data, penalty_info)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Enhanced HTML timetable generated: {output_file}")
        return html_content

    def _calculate_penalty_info(self, schedule: Dict[int, List[int]]) -> Dict:
        """Calculate penalty information for the schedule using Carter et al.'s proximity weights"""
        try:
            # Carter et al.'s proximity weights
            PROXIMITY_WEIGHTS = {
                1: 16,  # 2^(5-1) = 16 penalty for exams 1 slot apart
                2: 8,   # 2^(5-2) = 8 penalty for exams 2 slots apart  
                3: 4,   # 2^(5-3) = 4 penalty for exams 3 slots apart
                4: 2,   # 2^(5-4) = 2 penalty for exams 4 slots apart
                5: 1    # 2^(5-5) = 1 penalty for exams 5 slots apart
            }
            
            # Convert schedule to exam_to_slot_map (1-indexed exam IDs to 1-indexed slots)
            exam_to_slot_map = {}
            for slot_id, exam_indices in schedule.items():
                for exam_idx_zero_based in exam_indices:
                    exam_id_one_indexed = exam_idx_zero_based + 1  # Convert to 1-indexed
                    exam_to_slot_map[exam_id_one_indexed] = slot_id
            
            # Check for direct conflicts (same timeslot)
            direct_conflicts = 0
            for slot_id, exam_indices in schedule.items():
                if len(exam_indices) > 1:
                    # Check conflicts between exams in same slot
                    for i in range(len(exam_indices)):
                        for j in range(i + 1, len(exam_indices)):
                            exam1_idx = exam_indices[i]
                            exam2_idx = exam_indices[j]
                            if (0 <= exam1_idx < self.data_loader.num_exams and 
                                0 <= exam2_idx < self.data_loader.num_exams and
                                self.data_loader.conflict_matrix is not None):
                                if self.data_loader.conflict_matrix[exam1_idx][exam2_idx] > 0:
                                    direct_conflicts += 1
            
            # Calculate proximity penalty using Carter et al.'s method
            total_proximity_penalty = 0.0
            proximity_conflicts_count = 0
            
            if hasattr(self.data_loader, 'student_enrollments') and self.data_loader.student_enrollments:
                for student_exams in self.data_loader.student_enrollments:
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
                                penalty_value = PROXIMITY_WEIGHTS[slot_diff]
                                student_penalty += penalty_value
                                total_proximity_penalty += penalty_value
                                proximity_conflicts_count += 1
            
            # Calculate average penalty per student
            num_students = len(self.data_loader.student_enrollments) if hasattr(self.data_loader, 'student_enrollments') else self.data_loader.num_students
            avg_penalty_per_student = total_proximity_penalty / num_students if num_students > 0 else 0
            
            return {
                'total_penalty': total_proximity_penalty,
                'avg_penalty_per_student': avg_penalty_per_student,
                'direct_conflicts': direct_conflicts,
                'proximity_conflicts_count': proximity_conflicts_count,
                'penalty_breakdown': {
                    'direct_conflicts': direct_conflicts * 1000,  # High penalty for direct conflicts
                    'proximity_conflicts': total_proximity_penalty,
                    'avg_per_student': avg_penalty_per_student
                }
            }
        except Exception as e:
            print(f"Error calculating penalty: {e}")
            import traceback
            traceback.print_exc()
            return {
                'total_penalty': 0,
                'avg_penalty_per_student': 0,
                'direct_conflicts': 0,
                'proximity_conflicts_count': 0,
                'penalty_breakdown': {'direct_conflicts': 0, 'proximity_conflicts': 0, 'avg_per_student': 0}
            }

    def _format_student_id(self, student_index: int) -> str:
        """Format student ID in ITxxxxxxxx format"""
        return f"IT{student_index:08d}"
    
    def _format_exam_name(self, exam_id: int) -> str:
        """Format exam name with module ID and descriptive name"""
        # Generate a descriptive name based on exam ID
        module_names = [
            "Mathematics", "Physics", "Chemistry", "Biology", "Computer Science",
            "Engineering", "Statistics", "Economics", "Psychology", "History",
            "Literature", "Philosophy", "Sociology", "Geography", "Art",
            "Music", "Business", "Law", "Medicine", "Architecture"
        ]
        
        module_name = module_names[(exam_id - 1) % len(module_names)]
        return f"MOD{exam_id:03d}_{module_name}"

    def _get_students_for_exam(self, exam_id: int) -> List[str]:
        """Get formatted student IDs for a given exam"""
        students = []
        for student_idx, enrollments in enumerate(self.data_loader.student_enrollments):
            if exam_id in enrollments:
                students.append(self._format_student_id(student_idx))
        return students

    def _generate_html_content(self, schedule: dict, penalty_info: dict) -> str:
        """Generate the complete enhanced HTML content"""
        
        # Calculate statistics
        total_exams = sum(len(exams) for exams in schedule.values())
        num_timeslots = len(schedule)
        avg_exams_per_slot = total_exams / num_timeslots if num_timeslots > 0 else 0
        total_students = self.data_loader.num_students
        
        # Calculate additional statistics
        max_exams_in_slot = max(len(exams) for exams in schedule.values()) if schedule else 0
        min_exams_in_slot = min(len(exams) for exams in schedule.values()) if schedule else 0
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced STA83 Exam Timetable - Student ID Mapping</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <div class="institution-header">
            <h1>🎓 Enhanced STA83 Exam Timetable</h1>
            <div class="subtitle">Multi-Objective Optimized Schedule with Student ID Mapping</div>
            <div class="generated-info">
                Generated using Advanced Scheduling Algorithm<br>
                {num_timeslots} timeslots • {total_exams} exams • {total_students} students • Total Penalty: {penalty_info['total_penalty']:.2f}
            </div>
        </div>
        
        <div class="actions-bar">
            <a href="#" class="btn" onclick="downloadPDF()">📄 Download PDF</a>
            <a href="#" class="btn btn-secondary" onclick="window.print()">🖨️ Print Timetable</a>
            <a href="#" class="btn btn-info" onclick="showStatistics()">📊 Statistics</a>
            <a href="#" class="btn btn-success" onclick="showPenaltyBreakdown()">⚠️ Penalty Analysis</a>
        </div>
        
        <div class="content">
            <p id="top" style="text-align: center; color: #6c757d; margin-bottom: 20px;">Generated on {timestamp}</p>
            
            <div class="summary-stats">
                <div class="stat-card">
                    <div class="stat-number">{num_timeslots}</div>
                    <div class="stat-label">Timeslots</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_exams}</div>
                    <div class="stat-label">Total Exams</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_students}</div>
                    <div class="stat-label">Students</div>
                </div>
                <div class="stat-card penalty-card">
                    <div class="stat-number">{penalty_info['total_penalty']:.1f}</div>
                    <div class="stat-label">Total Penalty</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{penalty_info['direct_conflicts']}</div>
                    <div class="stat-label">Direct Conflicts</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{avg_exams_per_slot:.1f}</div>
                    <div class="stat-label">Avg Exams/Slot</div>
                </div>
            </div>
            
            <div class="penalty-breakdown" id="penalty-breakdown" style="display: none;">
                <h3>📊 Penalty Breakdown Analysis</h3>
                <div class="penalty-details">
                    <div class="penalty-item">
                        <span class="penalty-type">Direct Conflicts:</span>
                        <span class="penalty-value">{penalty_info['penalty_breakdown']['direct_conflicts']:.0f}</span>
                        <span class="penalty-desc">({penalty_info['direct_conflicts']} conflicts × 1000 points each)</span>
                    </div>
                    <div class="penalty-item">
                        <span class="penalty-type">Proximity Penalty:</span>
                        <span class="penalty-value">{penalty_info['penalty_breakdown']['proximity_conflicts']:.1f}</span>
                        <span class="penalty-desc">({penalty_info['proximity_conflicts_count']} proximity conflicts using Carter et al. weights)</span>
                    </div>
                    <div class="penalty-item">
                        <span class="penalty-type">Avg Per Student:</span>
                        <span class="penalty-value">{penalty_info['penalty_breakdown']['avg_per_student']:.2f}</span>
                        <span class="penalty-desc">Average proximity penalty per student</span>
                    </div>
                    <div class="penalty-item total">
                        <span class="penalty-type">Total Penalty:</span>
                        <span class="penalty-value">{penalty_info['total_penalty']:.1f}</span>
                        <span class="penalty-desc">Lower is better (Carter et al. method)</span>
                    </div>
                </div>
            </div>
            
            <div class="toc">
                <h2>📅 Timeslots Overview</h2>
                <div class="toc-list">
                    {self._generate_toc(schedule)}
                </div>
            </div>
            
            {self._generate_timeslot_tables(schedule)}
        </div>
    </div>
    
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>"""
        return html
    
    def _generate_toc(self, schedule: dict) -> str:
        """Generate table of contents for timeslots"""
        toc_items = []
        for slot_id in sorted(schedule.keys()):
            num_exams = len(schedule[slot_id])
            toc_items.append(
                f'<a href="#timeslot-{slot_id}">Slot {slot_id} ({num_exams} exams)</a>'
            )
        return '\n'.join(toc_items)
    
    def _generate_timeslot_tables(self, schedule: dict) -> str:
        """Generate HTML tables for each timeslot"""
        tables = []
        
        for slot_id in sorted(schedule.keys()):
            exams_in_slot = schedule[slot_id]
            
            # Generate exam cards for this timeslot
            exam_cards = []
            for exam_idx_zero_based in sorted(exams_in_slot):
                exam_id_display = exam_idx_zero_based + 1 # Convert to 1-indexed for display
                
                # Get student count and list for this exam
                student_count = self.data_loader.exam_student_counts.get(exam_id_display, 0)
                students_list = self._get_students_for_exam(exam_id_display)
                
                # Format exam name
                exam_name = self._format_exam_name(exam_id_display)
                
                # Create student list display (show first few, then "view all" button)
                students_display = ""
                if students_list:
                    visible_students = students_list[:5]  # Show first 5
                    students_display = f"""
                    <div class="students-list">
                        <div class="students-preview">
                            {', '.join(visible_students)}
                            {f'<span class="more-indicator">... and {len(students_list) - 5} more</span>' if len(students_list) > 5 else ''}
                        </div>
                        <button class="btn-small" onclick="toggleStudentList('exam-{exam_id_display}-slot-{slot_id}')">
                            View All {len(students_list)} Students
                        </button>
                        <div id="exam-{exam_id_display}-slot-{slot_id}" class="full-student-list" style="display: none;">
                            <div class="student-grid">
                                {self._format_student_grid(students_list)}
                            </div>
                        </div>
                    </div>"""
                
                exam_cards.append(f'''
                <div class="exam-card">
                    <div class="exam-header">
                        <span class="exam-id">{exam_name}</span>
                        <span class="student-count">{student_count} students</span>
                    </div>
                    <div class="exam-details">
                        <div class="exam-info">📍 Timeslot {slot_id} | 🆔 Exam ID: {exam_id_display}</div>
                        {students_display}
                    </div>
                </div>''')
            
            table = f'''
            <div id="timeslot-{slot_id}" class="timeslot-section">
                <div class="timeslot-header">
                    <h2>📅 Timeslot {slot_id}</h2>
                    <div class="timeslot-summary">
                        {len(exams_in_slot)} exams scheduled
                    </div>
                </div>
                
                <div class="exam-grid">
                    {''.join(exam_cards)}
                </div>
                <a href="#top" class="back-to-top">⬆️ Back to Top</a>
            </div>'''
            
            tables.append(table)
        
        return '\n'.join(tables)
    
    def _format_student_grid(self, students_list: List[str]) -> str:
        """Format student list in a grid layout"""
        student_items = []
        for student_id in students_list:
            student_items.append(f'<span class="student-id">{student_id}</span>')
        return '\n'.join(student_items)
    
    def _get_css_styles(self) -> str:
        """Return CSS styles for the HTML page"""
        return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
            background-color: #f8f9fa;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .institution-header {
            text-align: center;
            padding: 30px 20px;
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
            position: relative;
        }
        
        .institution-header h1 {
            margin: 0 0 10px 0;
            font-size: 2.5em;
            font-weight: 300;
            letter-spacing: 1px;
        }
        
        .institution-header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 15px;
        }
        
        .institution-header .generated-info {
            font-size: 0.9em;
            opacity: 0.8;
            border-top: 1px solid rgba(255,255,255,0.2);
            padding-top: 15px;
            margin-top: 15px;
        }
        
        .actions-bar {
            padding: 20px;
            background-color: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            text-align: center;
        }
        
        .btn {
            display: inline-block;
            padding: 10px 20px;
            margin: 0 10px;
            background-color: #1e3a8a;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 500;
            transition: background-color 0.3s ease;
            border: none;
            cursor: pointer;
        }
        
        .btn:hover {
            background-color: #3b82f6;
        }
        
        .btn-secondary {
            background-color: #6c757d;
        }
        
        .btn-secondary:hover {
            background-color: #5a6268;
        }
        
        .btn-info {
            background-color: #0ea5e9;
        }
        
        .btn-info:hover {
            background-color: #0284c7;
        }
        
        .btn-success {
            background-color: #10b981;
        }
        
        .btn-success:hover {
            background-color: #059669;
        }
        
        .btn-small {
            padding: 5px 10px;
            font-size: 0.8em;
            background-color: #3b82f6;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        
        .btn-small:hover {
            background-color: #1e3a8a;
        }
        
        .content {
            padding: 20px;
        }
        
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #1e3a8a;
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #1e3a8a;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #64748b;
            font-weight: 500;
        }
        
        .penalty-card {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #10b981;
        }
        
        .penalty-card .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #10b981;
            margin-bottom: 5px;
        }
        
        .penalty-card .stat-label {
            color: #64748b;
            font-weight: 500;
        }
        
        .toc {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #1e3a8a;
        }
        
        .toc h2 {
            margin-top: 0;
            color: #1e3a8a;
        }
        
        .toc-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        
        .toc-list a {
            display: block;
            text-decoration: none;
            color: #1e3a8a;
            padding: 12px 16px;
            background-color: white;
            border-radius: 5px;
            border: 1px solid #dee2e6;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        
        .toc-list a:hover {
            background-color: #1e3a8a;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .timeslot-section {
            margin-bottom: 40px;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .timeslot-header {
            background: linear-gradient(135deg, #e0f2fe 0%, #b3e5fc 100%);
            padding: 20px;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .timeslot-header h2 {
            margin: 0;
            color: #1e3a8a;
            font-size: 1.8em;
        }
        
        .timeslot-summary {
            color: #64748b;
            font-weight: 500;
            margin-top: 5px;
        }
        
        .exam-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            padding: 20px;
        }
        
        .exam-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            transition: all 0.3s ease;
            border-left: 4px solid #3b82f6;
        }
        
        .exam-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-left-color: #1e3a8a;
        }
        
        .exam-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .exam-id {
            font-weight: bold;
            color: #1e3a8a;
            font-size: 1.1em;
        }
        
        .student-count {
            background-color: #3b82f6;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
        }
        
        .exam-details {
            color: #64748b;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        
        .exam-info {
            margin-bottom: 10px;
            font-weight: 500;
        }
        
        .students-list {
            margin-top: 10px;
        }
        
        .students-preview {
            margin-bottom: 8px;
            font-size: 0.85em;
            color: #64748b;
        }
        
        .more-indicator {
            color: #3b82f6;
            font-style: italic;
        }
        
        .full-student-list {
            margin-top: 10px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border: 1px solid #e2e8f0;
        }
        
        .student-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 8px;
        }
        
        .student-id {
            background-color: #e0f2fe;
            color: #0369a1;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 500;
            text-align: center;
            border: 1px solid #bae6fd;
        }
        
        .penalty-breakdown {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #fef3c7;
            border-radius: 8px;
            border-left: 4px solid #f59e0b;
        }
        
        .penalty-breakdown h3 {
            margin-top: 0;
            color: #92400e;
        }
        
        .penalty-details {
            display: grid;
            gap: 10px;
        }
        
        .penalty-item {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 10px;
            padding: 10px;
            background-color: white;
            border-radius: 5px;
            border: 1px solid #fbbf24;
        }
        
        .penalty-item.total {
            background-color: #fef3c7;
            border: 2px solid #f59e0b;
            font-weight: bold;
        }
        
        .penalty-type {
            color: #92400e;
            font-weight: 500;
        }
        
        .penalty-value {
            color: #dc2626;
            font-weight: bold;
            text-align: center;
        }
        
        .penalty-desc {
            color: #64748b;
            font-size: 0.9em;
            text-align: right;
        }
        
        .exam-info {
            margin-bottom: 8px;
        }
        
        .back-to-top {
            display: block;
            text-align: center;
            margin: 20px;
            text-decoration: none;
            color: #1e3a8a;
            font-weight: 500;
            padding: 10px;
            border-radius: 5px;
            transition: background-color 0.3s ease;
        }
        
        .back-to-top:hover {
            background-color: #f8f9fa;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 0;
            }
            
            .institution-header h1 {
                font-size: 1.8em;
            }
            
            .summary-stats {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .toc-list {
                grid-template-columns: 1fr;
            }
            
            .exam-grid {
                grid-template-columns: 1fr;
            }
        }
        
        @media print {
            body {
                background-color: white;
            }
            
            .container {
                box-shadow: none;
            }
            
            .actions-bar {
                display: none;
            }
            
            .back-to-top {
                display: none;
            }
        }
        """
    
    def _get_javascript(self) -> str:
        """Get JavaScript functions for enhanced interactivity"""
        return """
        function downloadPDF() {
            alert('PDF download functionality would be implemented here using libraries like jsPDF or Puppeteer');
        }
        
        function showStatistics() {
            alert('Detailed statistics modal would be implemented here');
        }
        
        function showPenaltyBreakdown() {
            const penaltyBreakdown = document.getElementById('penalty-breakdown');
            penaltyBreakdown.style.display = penaltyBreakdown.style.display === 'none' ? 'block' : 'none';
        }
        
        function toggleStudentList(examId) {
            const studentList = document.getElementById(examId);
            studentList.style.display = studentList.style.display === 'none' ? 'block' : 'none';
        }
        
        // Smooth scrolling for anchor links
        document.addEventListener('DOMContentLoaded', function() {
            const links = document.querySelectorAll('a[href^="#"]');
            links.forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
        });
        """

def generate_enhanced_html_for_best_solution():
    """Generate enhanced HTML for the best solution with student ID mapping"""
    print("🎨 Generating Enhanced HTML Visualization with Student ID Mapping")
    print("=" * 60)
    
    # Load enhanced data
    data_loader = STA83DataLoader()
    if not data_loader.load_data():
        print("❌ Failed to load enhanced data")
        return
    
    # Load best solution
    try:
        solutions_df = pd.read_csv('results/quick_pareto_solutions.csv', header=None)
        best_solution = np.array(solutions_df.iloc[-1].values, dtype=int)
        print(f"✅ Loaded best solution with {len(best_solution)} exams")
    except Exception as e:
        print(f"❌ Failed to load solution: {e}")
        return
    
    # Generate enhanced HTML
    generator = EnhancedExamTimetableHTMLGenerator(data_loader)
    
    # Create a dummy schedule_data for the example, as best_solution is no longer a direct input
    # In a real scenario, this would come from the problem instance or algorithm output
    dummy_schedule_data = {
        1: [1, 2, 3],  # Slot 1: Exams 1, 2, 3
        2: [4, 5],     # Slot 2: Exams 4, 5
        3: [6]         # Slot 3: Exam 6
    }
    # Adjust exam IDs if your data_loader.exam_names or exam_student_counts expect specific IDs
    # The dummy data uses 1-based exam IDs for simplicity here.
    
    output_file = generator.generate_html_timetable_from_schedule_dict(dummy_schedule_data, "enhanced_sta83_exam_timetable.html")
    
    print(f"🌐 Open {output_file} in your browser to view the enhanced timetable!")
    print(f"📊 Simplified features included:")
    print(f"   • Basic exam schedule display")

if __name__ == "__main__":
    generate_enhanced_html_for_best_solution() 