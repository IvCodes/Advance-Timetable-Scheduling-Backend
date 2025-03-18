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
    <title>SLIIT Timetable</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        h1, h2, h3 {
            color: #003366;
        }
        .institution-header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background-color: #003366;
            color: white;
        }
        .toc {
            margin-bottom: 30px;
            padding: 15px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        .toc h2 {
            margin-top: 0;
        }
        .toc-list {
            column-count: 3;
            column-gap: 20px;
        }
        .toc-list a {
            display: block;
            text-decoration: none;
            color: #003366;
            margin-bottom: 5px;
        }
        .toc-list a:hover {
            text-decoration: underline;
        }
        .timetable {
            width: 100%;
            margin-bottom: 40px;
            border-collapse: collapse;
        }
        .timetable th {
            background-color: #003366;
            color: white;
            padding: 10px;
            text-align: center;
            border: 1px solid #ddd;
        }
        .timetable td {
            border: 1px solid #ddd;
            padding: 10px;
            vertical-align: top;
            min-height: 80px;
        }
        .timetable .time-slot {
            background-color: #f0f0f0;
            font-weight: bold;
            text-align: center;
            width: 10%;
        }
        .activity {
            padding: 5px;
            margin-bottom: 5px;
            background-color: #e6f3ff;
            border-radius: 3px;
        }
        .activity .course-code {
            font-weight: bold;
            color: #003366;
        }
        .activity .course-name {
            font-style: italic;
        }
        .activity .lecturer {
            font-size: 0.9em;
            color: #666;
        }
        .activity .venue {
            font-size: 0.9em;
            color: #666;
        }
        .empty-slot {
            text-align: center;
            color: #999;
        }
        .back-to-top {
            display: block;
            text-align: center;
            margin-top: 20px;
            margin-bottom: 40px;
            text-decoration: none;
            color: #003366;
        }
        .back-to-top:hover {
            text-decoration: underline;
        }
        .group-header {
            background-color: #e6f3ff;
            padding: 10px;
            margin-top: 30px;
            margin-bottom: 10px;
            border-radius: 5px;
        }
        .activity.practical {
            background-color: #e1f5e1;
        }
        .activity.lecture {
            background-color: #e6f3ff;
        }
        .activity.tutorial {
            background-color: #fff1e6;
        }
        .debug {
            background-color: #ffffcc;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ccc;
        }
    </style>
</head>
<body>
    <div class="institution-header">
        <h1>Sri Lanka Institute of Information Technology</h1>
        <p>Generated Timetable</p>
    </div>
"""

HTML_TOC_HEADER = """
    <div class="toc">
        <h2>Table of Contents</h2>
        <div class="toc-list">
"""

HTML_TOC_FOOTER = """
        </div>
    </div>
"""

HTML_FOOTER = """
    <script>
        // Add any JavaScript functionality here if needed
    </script>
</body>
</html>
"""

# Constants for HTML generation
UL_CLOSE = '</ul>'
LI_CLOSE = '</li>'

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
    # Convert slot numbers to time ranges
    # This is a simplification - adjust as needed for your actual slot times
    time_map = {
        '1': '08:30',
        '2': '09:30',
        '3': '10:30',
        '4': '11:30',
        '5': '13:30',
        '6': '14:30',
        '7': '15:30',
        '8': '16:30'
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

def _generate_timetable_row(time_range, time_slots, timetable, group_id):
    """Helper function to generate a single row in the timetable."""
    row_html = f'<tr><td class="time-slot">{time_range}</td>'
    
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        row_html += '<td>'
        if day in time_slots[time_range]:
            slot = time_slots[time_range][day]
            group_activities_found = False
            
            # The timetable is now a dictionary with (slot, room) keys
            # Find activities for this group in this slot
            for (slot_id, room) in timetable:
                if slot_id == slot:
                    activity = timetable[(slot_id, room)]
                    if activity is not None and group_id in activity.group_ids:
                        row_html += format_activity_html(activity, room)
                        group_activities_found = True
            
            if not group_activities_found:
                row_html += '<div class="empty-slot">-x-</div>'
        else:
            row_html += '<div class="empty-slot">---</div>'
        
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

def _generate_debug_information(timetable):
    """Generate HTML with debugging information."""
    html = '<div class="debug">'
    html += '<h3>Timetable Debugging Information</h3>'
    html += '<p>Timetable structure:</p>'
    html += '<ul>'
    
    if not timetable:
        html += '<li>Timetable is empty</li>'
    else:
        # Count unique slots
        slots_dict = {}
        for (slot, room) in timetable:
            if slot not in slots_dict:
                slots_dict[slot] = []
            slots_dict[slot].append(room)
        
        html += f'<li>Number of time slots: {len(slots_dict)}</li>'
        html += f'<li>Available slots: {", ".join(slots_dict.keys())}</li>'
        
        # Show some sample slots
        slot_count = 0
        html += '<li>Sample time slots:</li>'
        html += '<ul>'
        for slot in slots_dict:
            if slot_count < 5:  # Just show a few samples
                html += f'<li>{slot} ({_get_day_from_slot(slot)} {_get_time_from_slot(slot)}): {len(slots_dict[slot])} rooms</li>'
                
                # Show a few activities in this slot
                activity_count = 0
                html += '<ul>'
                for room in slots_dict[slot]:
                    activity = timetable.get((slot, room))
                    if activity_count < 3 and activity is not None:  # Just show a few activities
                        groups = ', '.join([str(g) for g in activity.group_ids]) if activity.group_ids else "None"
                        html += f'<li>Room {room}: {activity.subject} (Groups: {groups})</li>'
                    activity_count += 1
                html += UL_CLOSE
                
            slot_count += 1
        html += UL_CLOSE
        
        # Show group information
        html += '<li>Groups Information:</li>'
        html += '<ul>'
        group_count = 0
        for group_id in groups_dict:
            if group_count < 10:  # Just show a few samples
                html += f'<li>Group ID: {group_id}, Size: {groups_dict[group_id].size}</li>'
            group_count += 1
        html += f'<li>Total groups: {len(groups_dict)}</li>'
        html += UL_CLOSE
    
    html += UL_CLOSE
    html += '</div>'
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
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html += f'<p id="top">Timetable generated on {timestamp}</p>'
    
    # Add debugging information
    html += _generate_debug_information(timetable)
    
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
