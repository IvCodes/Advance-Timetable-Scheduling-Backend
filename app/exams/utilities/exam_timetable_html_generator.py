"""
HTML Generator for STA83 Exam Timetables
Creates beautiful HTML visualization of optimized exam schedules
"""
import numpy as np
import pandas as pd
from datetime import datetime
from sta83_data_loader import STA83DataLoader
from timetabling_core import decode_permutation, calculate_proximity_penalty

class ExamTimetableHTMLGenerator:
    """Generate HTML visualization for exam timetables"""
    
    def __init__(self, data_loader: STA83DataLoader):
        self.data_loader = data_loader
        
    def generate_html(self, solution_permutation: np.ndarray, output_file: str = "exam_timetable.html"):
        """Generate HTML file for the exam timetable"""
        
        # Decode the solution
        exam_to_slot_map, timeslots_used = decode_permutation(solution_permutation, self.data_loader.conflict_matrix, self.data_loader.num_exams)
        penalty = calculate_proximity_penalty(exam_to_slot_map, self.data_loader.student_enrollments, self.data_loader.num_students)
        
        # Convert to schedule format (slot_id -> list of exam_ids)
        schedule = {}
        for exam_id, slot_id in exam_to_slot_map.items():
            if slot_id not in schedule:
                schedule[slot_id] = []
            schedule[slot_id].append(exam_id - 1)  # Convert to 0-indexed for consistency
        
        # Generate HTML content
        html_content = self._generate_html_content(schedule, penalty)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML timetable generated: {output_file}")
        return output_file
    
    def _generate_html_content(self, schedule: dict, penalty: float) -> str:
        """Generate the complete HTML content"""
        
        # Calculate statistics
        total_exams = sum(len(exams) for exams in schedule.values())
        num_timeslots = len(schedule)
        avg_exams_per_slot = total_exams / num_timeslots if num_timeslots > 0 else 0
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STA83 Exam Timetable - Optimized Schedule</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <div class="institution-header">
            <h1>STA83 Exam Timetable</h1>
            <div class="subtitle">Multi-Objective Optimized Schedule</div>
            <div class="generated-info">
                Generated using NSGA-II Algorithm<br>
                {num_timeslots} timeslots • {total_exams} exams • Penalty: {penalty:.2f}
            </div>
        </div>
        
        <div class="actions-bar">
            <a href="#" class="btn" onclick="downloadPDF()">Download PDF</a>
            <a href="#" class="btn btn-secondary" onclick="window.print()">Print Timetable</a>
            <a href="#" class="btn btn-info" onclick="showStatistics()">Statistics</a>
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
                    <div class="stat-label">Exams</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{avg_exams_per_slot:.1f}</div>
                    <div class="stat-label">Avg per Slot</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{penalty:.1f}</div>
                    <div class="stat-label">Penalty Score</div>
                </div>
            </div>
            
            <div class="toc">
                <h2>Timeslots Overview</h2>
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
            total_students = sum(self.data_loader.exam_student_counts.get(exam_id + 1, 0) 
                               for exam_id in schedule[slot_id])
            toc_items.append(
                f'<a href="#timeslot-{slot_id}">Slot {slot_id} ({num_exams} exams, {total_students} students)</a>'
            )
        return '\\n'.join(toc_items)
    
    def _generate_timeslot_tables(self, schedule: dict) -> str:
        """Generate HTML tables for each timeslot"""
        tables = []
        
        for slot_id in sorted(schedule.keys()):
            exams = schedule[slot_id]
            total_students = sum(self.data_loader.exam_student_counts.get(exam_id + 1, 0) 
                               for exam_id in exams)
            
            # Generate exam cards for this timeslot
            exam_cards = []
            for exam_id in sorted(exams):
                exam_id_display = exam_id + 1  # Convert to 1-indexed
                student_count = self.data_loader.exam_student_counts.get(exam_id_display, 0)
                
                # Find students enrolled in this exam
                enrolled_students = []
                for student_idx, student_exams in enumerate(self.data_loader.student_enrollments):
                    if exam_id_display in student_exams:
                        enrolled_students.append(student_idx + 1)
                
                exam_cards.append(f'''
                <div class="exam-card">
                    <div class="exam-header">
                        <span class="exam-id">Exam {exam_id_display:03d}</span>
                        <span class="student-count">{student_count} students</span>
                    </div>
                    <div class="exam-details">
                        <div class="exam-info">Duration: 3 hours</div>
                        <div class="exam-students">Students: {len(enrolled_students)} enrolled</div>
                    </div>
                </div>''')
            
            table = f'''
            <div id="timeslot-{slot_id}" class="timeslot-section">
                <div class="timeslot-header">
                    <h2>Timeslot {slot_id}</h2>
                    <div class="timeslot-summary">
                        {len(exams)} exams • {total_students} total students
                    </div>
                </div>
                <div class="exam-grid">
                    {''.join(exam_cards)}
                </div>
                <a href="#top" class="back-to-top">Back to Top</a>
            </div>'''
            
            tables.append(table)
        
        return '\\n'.join(tables)
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the HTML"""
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
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
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
        }
        
        .exam-info, .exam-students {
            margin-bottom: 4px;
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
        """Get JavaScript for the HTML"""
        return """
        async function downloadPDF() {
            // Simple alert for now - would need jsPDF library for full implementation
            alert('PDF download functionality would require jsPDF library integration.');
        }
        
        function showStatistics() {
            alert('Detailed statistics view coming soon!');
        }
        
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
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
        """

def generate_html_for_best_solution():
    """Generate HTML for the best solution from NSGA-II results"""
    print("🎨 Generating HTML Visualization for Best Solution")
    print("=" * 50)
    
    # Load data
    data_loader = STA83DataLoader()
    if not data_loader.load_data():
        print(" Failed to load data")
        return
    
    # Load best solution (9 timeslots)
    try:
        solutions_df = pd.read_csv('quick_pareto_solutions.csv', header=None)
        best_solution = np.array(solutions_df.iloc[-1].values, dtype=int)
        print(f" Loaded best solution with {len(best_solution)} exams")
    except Exception as e:
        print(f" Failed to load solution: {e}")
        return
    
    # Generate HTML
    generator = ExamTimetableHTMLGenerator(data_loader)
    output_file = generator.generate_html(best_solution, "sta83_exam_timetable.html")
    
    print(f"🌐 Open {output_file} in your browser to view the timetable!")

if __name__ == "__main__":
    generate_html_for_best_solution() 