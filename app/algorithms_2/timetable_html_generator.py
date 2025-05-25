"""
HTML Timetable Generator for TimeTableScheduler
Generates an HTML representation of the timetable for easy viewing.
"""

import os
import datetime
from Data_Loading import slots, activities_dict, groups_dict, spaces_dict, lecturers_dict

# HTML template constants
HTML_HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SLIIT Course Timetable - Faculty of Computing</title>
    <style>
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
            background: linear-gradient(135deg, #003366 0%, #004080 100%);
            color: white;
            position: relative;
        }
        
        .institution-header h1 {
            margin: 0 0 10px 0;
            font-size: 2.5em;
            font-weight: 300;
            letter-spacing: 1px;
            color: white;
        }
        
        .institution-header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 15px;
            color: white;
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
            background-color: #003366;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 500;
            transition: background-color 0.3s ease;
        }
        
        .btn:hover {
            background-color: #004080;
        }
        
        .btn-secondary {
            background-color: #6c757d;
        }
        
        .btn-secondary:hover {
            background-color: #5a6268;
        }
        
        .content {
            padding: 20px;
        }
        
        h1, h2, h3 {
            color: #003366;
        }
        
        .toc {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #003366;
        }
        
        .toc h2 {
            margin-top: 0;
            color: #003366;
        }
        
        .toc-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .toc-list a {
            display: block;
            text-decoration: none;
            color: #003366;
            padding: 8px 12px;
            background-color: white;
            border-radius: 5px;
            border: 1px solid #dee2e6;
            transition: all 0.3s ease;
        }
        
        .toc-list a:hover {
            background-color: #003366;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .timetable {
            width: 100%;
            margin-bottom: 40px;
            border-collapse: collapse;
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .timetable th {
            background: linear-gradient(135deg, #003366 0%, #004080 100%);
            color: white;
            padding: 15px 10px;
            text-align: center;
            border: none;
            font-weight: 600;
            font-size: 0.95em;
        }
        
        .timetable td {
            border: 1px solid #e9ecef;
            padding: 12px 8px;
            vertical-align: top;
            min-height: 80px;
            background-color: white;
        }
        
        .timetable .time-slot {
            background-color: #f8f9fa;
            font-weight: 600;
            text-align: center;
            width: 12%;
            color: #495057;
            border-right: 2px solid #dee2e6;
        }
        
        .activity {
            padding: 8px;
            margin-bottom: 6px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
            background-color: #f8f9ff;
            font-size: 0.85em;
            transition: transform 0.2s ease;
        }
        
        .activity:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .activity .course-code {
            font-weight: 600;
            color: #003366;
            margin-bottom: 2px;
        }
        
        .activity .course-name {
            font-style: italic;
            color: #6c757d;
            margin-bottom: 2px;
        }
        
        .activity .lecturer {
            font-size: 0.8em;
            color: #495057;
            margin-bottom: 1px;
        }
        
        .activity .venue {
            font-size: 0.8em;
            color: #6c757d;
            font-weight: 500;
        }
        
        .empty-slot {
            text-align: center;
            color: #adb5bd;
            font-style: italic;
            padding: 20px;
        }
        
        .back-to-top {
            display: block;
            text-align: center;
            margin: 30px 0;
            text-decoration: none;
            color: #003366;
            font-weight: 500;
            padding: 10px;
            border-radius: 5px;
            transition: background-color 0.3s ease;
        }
        
        .back-to-top:hover {
            background-color: #f8f9fa;
        }
        
        .group-header {
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            padding: 20px;
            margin: 40px 0 20px 0;
            border-radius: 8px;
            border-left: 5px solid #003366;
        }
        
        .group-header h2 {
            margin: 0;
            color: #003366;
            font-size: 1.5em;
        }
        
        .activity.practical {
            background-color: #e8f5e8;
            border-left-color: #28a745;
        }
        
        .activity.lecture {
            background-color: #f8f9ff;
            border-left-color: #007bff;
        }
        
        .activity.tutorial {
            background-color: #fff8e1;
            border-left-color: #ffc107;
        }
        
        .lunch-break {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            color: #856404;
            font-weight: 600;
            text-align: center;
            padding: 15px;
            border-radius: 6px;
            border: 2px solid #ffc107;
            position: relative;
            font-size: 0.9em;
        }
        
        .lunch-break::before {
            content: "🍽️";
            margin-right: 8px;
            font-size: 1.1em;
        }
        
        .lunch-break-row {
            background-color: #fffbf0 !important;
        }
        
        .lunch-break-time {
            background-color: #fff3cd !important;
            color: #856404 !important;
            font-weight: 600;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 0;
            }
            
            .institution-header h1 {
                font-size: 1.8em;
            }
            
            .toc-list {
                grid-template-columns: 1fr;
            }
            
            .timetable {
                font-size: 0.8em;
            }
            
            .activity {
                padding: 6px;
                font-size: 0.75em;
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
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
</head>
<body>
    <div class="container">
        <div class="institution-header">
            <h1>SLIIT Course Timetable</h1>
            <div class="subtitle">Faculty of Computing</div>
            <div class="generated-info">
                Sri Lanka Institute of Information Technology
            </div>
        </div>
        
        <div class="actions-bar">
            <a href="#" class="btn" onclick="downloadPDF()">📄 Download PDF</a>
            <a href="#" class="btn btn-secondary" onclick="window.print()">🖨️ Print Timetable</a>
        </div>
        
        <div class="content">
"""

HTML_TOC_HEADER = """
    <div class="toc">
        <h2>📚 Course Groups</h2>
        <div class="toc-list">
"""

HTML_TOC_FOOTER = """
        </div>
    </div>
"""

HTML_FOOTER = """
        </div>
    </div>
    
    <script>
        async function downloadPDF() {
            const { jsPDF } = window.jspdf;
            
            // Hide action buttons temporarily
            const actionsBar = document.querySelector('.actions-bar');
            actionsBar.style.display = 'none';
            
            try {
                const canvas = await html2canvas(document.querySelector('.container'), {
                    scale: 2,
                    useCORS: true,
                    allowTaint: true
                });
                
                const imgData = canvas.toDataURL('image/png');
                const pdf = new jsPDF('l', 'mm', 'a4'); // landscape orientation
                
                const imgWidth = 297; // A4 landscape width in mm
                const pageHeight = 210; // A4 landscape height in mm
                const imgHeight = (canvas.height * imgWidth) / canvas.width;
                let heightLeft = imgHeight;
                
                let position = 0;
                
                pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
                heightLeft -= pageHeight;
                
                while (heightLeft >= 0) {
                    position = heightLeft - imgHeight;
                    pdf.addPage();
                    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
                    heightLeft -= pageHeight;
                }
                
                const timestamp = new Date().toISOString().split('T')[0];
                pdf.save(`SLIIT_Timetable_${timestamp}.pdf`);
            } catch (error) {
                console.error('Error generating PDF:', error);
                alert('Error generating PDF. Please try using the print function instead.');
            } finally {
                // Show action buttons again
                actionsBar.style.display = 'block';
            }
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
    </script>
</body>
</html>
"""

# Constants for HTML generation

def get_activity_type(subject):
    """Determine the activity type based on its subject name."""
    subject_lower = subject.lower()
    if 'practical' in subject_lower or 'lab' in subject_lower:
        return 'practical'
    elif 'tutorial' in subject_lower:
        return 'tutorial'
    else:
        return 'lecture'

def format_activity_html(activity, room):
    """Format an activity as HTML."""
    if activity is None:
        return '<div class="empty-slot">---</div>'
    
    activity_type = get_activity_type(activity.subject)
    
    # Format group information
    group_info = ""
    if activity.group_ids:
        group_names = [f"Group {g_id}" for g_id in activity.group_ids]
        group_info = ", ".join(group_names)
    
    # Format lecturer information
    lecturer_info = ""
    if activity.teacher_id in lecturers_dict:
        lecturer = lecturers_dict[activity.teacher_id]
        lecturer_info = f"{lecturer.first_name} {lecturer.last_name}"
    else:
        lecturer_info = f"Lecturer {activity.teacher_id}"
    
    # Format room information
    room_info = ""
    if room in spaces_dict:
        room_info = spaces_dict[room].code
    else:
        room_info = f"Room {room}"
    
    return f"""
    <div class="activity {activity_type}">
        <div>{group_info}</div>
        <div class="course-code">{activity.subject}</div>
        <div class="lecturer">{lecturer_info}</div>
        <div class="venue">{room_info}</div>
    </div>
    """

def _get_day_from_slot(slot):
    """Extract day from a slot like 'MON1'."""
    day_map = {
        'MON': 'Monday',
        'TUE': 'Tuesday',
        'WED': 'Wednesday',
        'THU': 'Thursday',
        'FRI': 'Friday'
    }
    day_code = slot[:3]
    return day_map.get(day_code, 'Unknown')

def _get_time_from_slot(slot):
    """Extract time from a slot like 'MON1'."""
    # Convert slot numbers to time ranges following SLIIT schedule
    # 8:00 AM - 4:30 PM with lunch break at 12:30-1:30
    time_map = {
        '1': '08:30 - 09:30',
        '2': '09:30 - 10:30', 
        '3': '10:30 - 11:30',
        '4': '11:30 - 12:30',
        '5': '12:30 - 13:30',  # Lunch break - should be blocked
        '6': '13:30 - 14:30',
        '7': '14:30 - 15:30',
        '8': '15:30 - 16:30'
    }
    slot_num = slot[3:]
    return time_map.get(slot_num, 'Unknown')

def _organize_slots_by_time():
    """Helper function to organize slots by time."""
    time_slots = {}
    for slot in slots:
        time = _get_time_from_slot(slot)
        day = _get_day_from_slot(slot)
        
        if time not in time_slots:
            time_slots[time] = {}
        
        time_slots[time][day] = slot
    
    return time_slots

def _is_lunch_break_slot(slot):
    """Check if a slot is during lunch break (12:30-13:30)."""
    slot_num = slot[3:] if len(slot) > 3 else ''
    return slot_num == '5'  # Slot 5 is 12:30-13:30

def _generate_timetable_row(time_range, time_slots, timetable, group_id):
    """Helper function to generate a single row in the timetable."""
    # Check if this is lunch break time
    is_lunch_break = "12:30 - 13:30" in time_range
    
    if is_lunch_break:
        # Special handling for lunch break row
        row_html = f'<tr class="lunch-break-row"><td class="time-slot lunch-break-time">{time_range}</td>'
        # Add a single lunch break cell spanning all days
        row_html += '<td colspan="5"><div class="lunch-break">LUNCH BREAK</div></td>'
        row_html += '</tr>'
        return row_html
    
    # Regular time slot row
    row_html = f'<tr><td class="time-slot">{time_range}</td>'
    
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        row_html += '<td>'
        
        if day in time_slots[time_range]:
            slot = time_slots[time_range][day]
            group_activities_found = False
            
            # The timetable is a dictionary with structure {slot: {room: activity_obj}}
            # Find activities for this group in this slot
            if slot in timetable:
                rooms_in_slot = timetable[slot]
                if isinstance(rooms_in_slot, dict):
                    for room_code, activity in rooms_in_slot.items():
                        if activity is not None and hasattr(activity, 'group_ids') and group_id in activity.group_ids:
                            row_html += format_activity_html(activity, room_code)
                            group_activities_found = True
                            break  # Found an activity for this group in this slot
            
            if not group_activities_found:
                row_html += '<div class="empty-slot">—</div>'
        else:
            row_html += '<div class="empty-slot">—</div>'
        
        row_html += '</td>'
    
    row_html += '</tr>'
    return row_html

def generate_group_timetable_html(group_id, timetable):
    """Generate HTML for a specific group's timetable."""
    # Use group ID instead of name
    group_name = f"Group {group_id}"
    
    html = f"""
    <div id="{group_name}" class="group-header">
        <h2>{group_name}</h2>
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
    time_slots = _organize_slots_by_time()
    
    # Sort time ranges
    sorted_times = sorted(time_slots.keys())
    
    # Generate rows for each time slot
    for time_range in sorted_times:
        html += _generate_timetable_row(time_range, time_slots, timetable, group_id)
    
    html += '</table>'
    html += '<a href="#top" class="back-to-top">Back to Top</a>'
    
    return html

def get_groups_by_year_semester():
    """Organize groups by year and semester."""
    year_semester_groups = {}
    
    for group_id in groups_dict:
        # All groups go into a single category for simplicity
        year_semester = "All Groups"
        
        if year_semester not in year_semester_groups:
            year_semester_groups[year_semester] = []
        
        year_semester_groups[year_semester].append(group_id)
    
    return year_semester_groups

def generate_table_of_contents(year_semester_groups):
    """Generate the table of contents HTML."""
    html = HTML_TOC_HEADER
    
    for year_semester, group_ids in sorted(year_semester_groups.items()):
        html += f'<h3>{year_semester}</h3>'
        
        for group_id in sorted(group_ids):
            # Use group ID instead of name
            group_name = f"Group {group_id}"
            html += f'<a href="#{group_name}">{group_name}</a>'
    
    html += HTML_TOC_FOOTER
    return html

def generate_timetable_html(timetable, output_file="timetable.html"):
    """
    Generate an HTML representation of the timetable.
    
    Args:
        timetable: The optimized timetable
        output_file: Path to save the HTML file
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    
    # Start with header
    html = HTML_HEADER
    
    # Add a timestamp
    timestamp = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
    html += f'<p id="top" style="text-align: center; color: #6c757d; margin-bottom: 20px;">Generated on {timestamp}</p>'
    
    # Organize groups by year and semester
    year_semester_groups = get_groups_by_year_semester()
    
    # Generate table of contents
    html += generate_table_of_contents(year_semester_groups)
    
    # Generate timetables for each group
    for year_semester, group_ids in sorted(year_semester_groups.items()):
        for group_id in sorted(group_ids):
            html += generate_group_timetable_html(group_id, timetable)
    
    # Add footer
    html += HTML_FOOTER
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Timetable HTML saved to {output_file}")
    return output_file
