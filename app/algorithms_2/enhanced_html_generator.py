"""
Enhanced HTML Generator for Backend Timetables with Student ID Mapping
Creates beautiful HTML visualization with detailed student information and key-value pairs
"""
import os
import datetime
from typing import Dict, List, Set, Optional
from enhanced_data_loader import enhanced_data_loader
from Data_Loading import activities_dict, groups_dict, spaces_dict, lecturers_dict, slots

class EnhancedHTMLGenerator:
    """Generate enhanced HTML visualization for timetables with student ID details"""
    
    def __init__(self):
        """Initialize the HTML generator with enhanced data loader"""
        self.data_loader = enhanced_data_loader
        self.html_header = self._get_html_header()
        self.html_footer = self._get_html_footer()
    
    def _get_html_header(self) -> str:
        """Get the HTML header with enhanced styling"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced SLIIT Computing Timetable with Student IDs</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 20px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            display: block;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .toc {
            background: #f8f9fa;
            padding: 30px;
            border-bottom: 1px solid #dee2e6;
        }
        
        .toc h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        .toc-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }
        
        .toc-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .toc-item:hover {
            transform: translateY(-2px);
        }
        
        .toc-item a {
            text-decoration: none;
            color: #3498db;
            font-weight: 600;
            display: block;
            margin-bottom: 5px;
        }
        
        .toc-item .student-count {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        
        .group-section {
            padding: 30px;
            border-bottom: 1px solid #eee;
        }
        
        .group-header {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .group-header h2 {
            font-size: 1.8em;
            margin-bottom: 10px;
        }
        
        .group-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .info-card {
            background: rgba(255,255,255,0.1);
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        
        .timetable {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .timetable th {
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
            color: white;
            padding: 15px;
            text-align: center;
            font-weight: 600;
            font-size: 1.1em;
        }
        
        .timetable td {
            padding: 12px;
            text-align: center;
            border-bottom: 1px solid #eee;
            vertical-align: top;
            min-height: 80px;
        }
        
        .time-slot {
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
            width: 120px;
        }
        
        .activity {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            padding: 10px;
            border-radius: 8px;
            margin: 2px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        
        .activity:hover {
            transform: scale(1.02);
        }
        
        .activity-title {
            font-weight: bold;
            font-size: 1em;
            margin-bottom: 5px;
        }
        
        .activity-details {
            font-size: 0.85em;
            opacity: 0.9;
        }
        
        .lecturer {
            margin: 2px 0;
        }
        
        .venue {
            margin: 2px 0;
            font-weight: 600;
        }
        
        .student-info {
            margin: 2px 0;
            font-size: 0.8em;
            background: rgba(255,255,255,0.2);
            padding: 3px 6px;
            border-radius: 3px;
        }
        
        .empty-slot {
            color: #bdc3c7;
            font-style: italic;
            padding: 20px;
        }
        
        .lunch-break {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            font-weight: bold;
            text-align: center;
        }
        
        .lunch-break-row td {
            padding: 10px;
        }
        
        .back-to-top {
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            transition: background 0.3s ease;
        }
        
        .back-to-top:hover {
            background: #2980b9;
        }
        
        .student-list {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .student-list h4 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .student-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        
        .student-tag {
            background: #3498db;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 10px;
            }
            
            .header {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .timetable {
                font-size: 0.9em;
            }
            
            .timetable th,
            .timetable td {
                padding: 8px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
"""
    
    def _get_html_footer(self) -> str:
        """Get the HTML footer"""
        return """    </div>
</body>
</html>"""
    
    def _get_day_from_slot(self, slot: str) -> str:
        """Extract day from a slot like 'MON1'"""
        day_map = {
            'MON': 'Monday',
            'TUE': 'Tuesday', 
            'WED': 'Wednesday',
            'THU': 'Thursday',
            'FRI': 'Friday'
        }
        day_code = slot[:3]
        return day_map.get(day_code, 'Unknown')
    
    def _get_time_from_slot(self, slot: str) -> str:
        """Extract time from a slot like 'MON1'"""
        time_map = {
            '1': '08:30 - 09:30',
            '2': '09:30 - 10:30',
            '3': '10:30 - 11:30', 
            '4': '11:30 - 12:30',
            '5': '12:30 - 13:30',  # Lunch break
            '6': '13:30 - 14:30',
            '7': '14:30 - 15:30',
            '8': '15:30 - 16:30'
        }
        slot_num = slot[3:]
        return time_map.get(slot_num, 'Unknown')
    
    def _is_lunch_break_slot(self, slot: str) -> bool:
        """Check if a slot is during lunch break"""
        slot_num = slot[3:] if len(slot) > 3 else ''
        return slot_num == '5'
    
    def _organize_slots_by_time(self) -> Dict[str, Dict[str, str]]:
        """Organize slots by time"""
        time_slots = {}
        for slot in slots:
            time = self._get_time_from_slot(slot)
            day = self._get_day_from_slot(slot)
            
            if time not in time_slots:
                time_slots[time] = {}
            
            time_slots[time][day] = slot
        
        return time_slots
    
    def _format_activity_html(self, activity, room_id: str) -> str:
        """Format activity information as HTML with student details"""
        if activity is None:
            return '<div class="empty-slot">—</div>'
        
        # Get lecturer information
        lecturer_name = "Unknown Lecturer"
        if hasattr(activity, 'teacher_id') and activity.teacher_id in lecturers_dict:
            lecturer = lecturers_dict[activity.teacher_id]
            lecturer_name = f"{lecturer.first_name} {lecturer.last_name}"
        
        # Get room information
        room_info = f"Room: {room_id}"
        if room_id in spaces_dict:
            room_capacity = spaces_dict[room_id].size
            room_info = f"{room_id} (Cap: {room_capacity})"
        
        # Get student information
        students = self.data_loader.get_activity_students(activity.id)
        student_count = len(students)
        
        # Create student tags (show first few students)
        student_tags = ""
        if students:
            display_students = students[:5]  # Show first 5 students
            for student_id in display_students:
                student_tags += f'<span class="student-tag">{student_id}</span>'
            
            if len(students) > 5:
                student_tags += f'<span class="student-tag">+{len(students) - 5} more</span>'
        
        return f"""
        <div class="activity">
            <div class="activity-title">{activity.subject}</div>
            <div class="activity-details">
                <div class="lecturer">👨‍🏫 {lecturer_name}</div>
                <div class="venue">🏢 {room_info}</div>
                <div class="student-info">👥 {student_count} students</div>
                <div class="student-tags" style="margin-top: 5px;">
                    {student_tags}
                </div>
            </div>
        </div>
        """
    
    def _generate_timetable_row(self, time_range: str, time_slots: Dict[str, Dict[str, str]], 
                               timetable: dict, group_id: str) -> str:
        """Generate a single row in the timetable"""
        # Check if this is lunch break time
        is_lunch_break = "12:30 - 13:30" in time_range
        
        if is_lunch_break:
            return f'''
            <tr class="lunch-break-row">
                <td class="time-slot">{time_range}</td>
                <td colspan="5"><div class="lunch-break">🍽️ LUNCH BREAK</div></td>
            </tr>
            '''
        
        # Regular time slot row
        row_html = f'<tr><td class="time-slot">{time_range}</td>'
        
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            row_html += '<td>'
            
            if day in time_slots[time_range]:
                slot = time_slots[time_range][day]
                group_activities_found = False
                
                # Find activities for this group in this slot
                if slot in timetable:
                    rooms_in_slot = timetable[slot]
                    if isinstance(rooms_in_slot, dict):
                        for room_code, activity in rooms_in_slot.items():
                            if (activity is not None and hasattr(activity, 'group_ids') 
                                and group_id in activity.group_ids):
                                row_html += self._format_activity_html(activity, room_code)
                                group_activities_found = True
                                break
                
                if not group_activities_found:
                    row_html += '<div class="empty-slot">—</div>'
            else:
                row_html += '<div class="empty-slot">—</div>'
            
            row_html += '</td>'
        
        row_html += '</tr>'
        return row_html
    
    def _generate_group_timetable(self, group_id: str, timetable: dict) -> str:
        """Generate HTML for a specific group's timetable"""
        group_name = f"Group {group_id}"
        
        # Get group statistics
        group_students = self.data_loader.get_group_students(group_id)
        student_count = len(group_students)
        
        # Get activities for this group
        group_activities = set()
        for student_id in group_students:
            student_activities = self.data_loader.get_student_activities(student_id)
            group_activities.update(student_activities)
        
        html = f"""
        <div class="group-section" id="{group_name}">
            <div class="group-header">
                <h2>{group_name}</h2>
                <div class="group-info">
                    <div class="info-card">
                        <strong>{student_count}</strong><br>
                        <span>Students</span>
                    </div>
                    <div class="info-card">
                        <strong>{len(group_activities)}</strong><br>
                        <span>Activities</span>
                    </div>
                    <div class="info-card">
                        <strong>{group_id}</strong><br>
                        <span>Group ID</span>
                    </div>
                </div>
            </div>
            
            <table class="timetable">
                <tr>
                    <th>Time</th>
                    <th>Monday</th>
                    <th>Tuesday</th>
                    <th>Wednesday</th>
                    <th>Thursday</th>
                    <th>Friday</th>
                </tr>
        """
        
        # Get all time slots organized by time
        time_slots = self._organize_slots_by_time()
        
        # Sort time ranges
        sorted_times = sorted(time_slots.keys())
        
        # Generate rows for each time slot
        for time_range in sorted_times:
            html += self._generate_timetable_row(time_range, time_slots, timetable, group_id)
        
        html += '</table>'
        
        # Add student list for this group
        if group_students:
            html += f"""
            <div class="student-list">
                <h4>👥 Students in {group_name} ({len(group_students)} total):</h4>
                <div class="student-tags">
            """
            
            for student_id in group_students[:20]:  # Show first 20 students
                html += f'<span class="student-tag">{student_id}</span>'
            
            if len(group_students) > 20:
                html += f'<span class="student-tag">+{len(group_students) - 20} more students</span>'
            
            html += """
                </div>
            </div>
            """
        
        html += '<a href="#top" class="back-to-top">⬆️ Back to Top</a>'
        html += '</div>'
        
        return html
    
    def _generate_header(self) -> str:
        """Generate the enhanced header with statistics"""
        # Get statistics from enhanced data loader
        mappings = self.data_loader.export_student_mappings()
        
        timestamp = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        return f"""
        <div class="header">
            <h1>🎓 Enhanced SLIIT Computing Timetable</h1>
            <div class="subtitle">Complete Schedule with Student ID Mappings</div>
            <div class="subtitle">Generated on {timestamp}</div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-number">{mappings['total_students']}</span>
                    <span class="stat-label">Total Students</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{mappings['total_activities']}</span>
                    <span class="stat-label">Activities</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{mappings['total_groups']}</span>
                    <span class="stat-label">Groups</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{len(lecturers_dict)}</span>
                    <span class="stat-label">Lecturers</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{len(spaces_dict)}</span>
                    <span class="stat-label">Rooms</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{len(slots)}</span>
                    <span class="stat-label">Time Slots</span>
                </div>
            </div>
        </div>
        """
    
    def _generate_table_of_contents(self) -> str:
        """Generate table of contents with group information"""
        html = """
        <div class="toc" id="top">
            <h2>📋 Table of Contents</h2>
            <div class="toc-grid">
        """
        
        # Get all groups and their student counts
        for group_id in sorted(groups_dict.keys()):
            group_students = self.data_loader.get_group_students(group_id)
            student_count = len(group_students)
            group_name = f"Group {group_id}"
            
            html += f"""
            <div class="toc-item">
                <a href="#{group_name}">{group_name}</a>
                <div class="student-count">👥 {student_count} students</div>
            </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def generate_enhanced_html(self, timetable: dict, output_file: str = "enhanced_timetable.html") -> str:
        """
        Generate enhanced HTML timetable with student ID mappings
        
        Args:
            timetable: The optimized timetable
            output_file: Path to save the HTML file
            
        Returns:
            Path to the generated HTML file
        """
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        
        # Build the complete HTML
        html = self.html_header
        html += self._generate_header()
        html += self._generate_table_of_contents()
        
        # Generate timetables for each group
        for group_id in sorted(groups_dict.keys()):
            html += self._generate_group_timetable(group_id, timetable)
        
        html += self.html_footer
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ Enhanced HTML timetable saved to {output_file}")
        return output_file


# Global instance for easy access
enhanced_html_generator = EnhancedHTMLGenerator()

def generate_enhanced_timetable_html(timetable: dict, output_file: str = "enhanced_timetable.html") -> str:
    """
    Convenience function to generate enhanced HTML timetable
    
    Args:
        timetable: The optimized timetable
        output_file: Path to save the HTML file
        
    Returns:
        Path to the generated HTML file
    """
    return enhanced_html_generator.generate_enhanced_html(timetable, output_file)


if __name__ == "__main__":
    # Test the enhanced HTML generator
    print("🧪 Testing Enhanced HTML Generator")
    
    # Create a sample timetable for testing
    sample_timetable = {slot: {room: None for room in spaces_dict} for slot in slots}
    
    # Generate the HTML
    output_path = generate_enhanced_timetable_html(sample_timetable, "test_enhanced_timetable.html")
    print(f"Test HTML generated: {output_path}") 