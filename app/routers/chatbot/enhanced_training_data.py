"""
Enhanced Training Data for Application-Aware Timetable Assistant Chatbot

This module contains comprehensive knowledge about the Advanced Timetable Scheduling System
including reports, dashboards, features, and system components.
"""

# Report Explanations
TEACHER_ALLOCATION_REPORT_DATA = {
    "description": "The Teacher Allocation Report shows how teaching workload is distributed across faculty members",
    "metrics_explanation": {
        "total_teachers": "The total number of faculty members in the system who can be assigned to teach classes",
        "average_workload": "The average percentage of maximum teaching capacity being used across all teachers",
        "total_teaching_hours": "The sum of all weekly teaching hours assigned to all faculty members",
        "weekly_hours": "Number of hours per week each teacher is assigned to teach classes",
        "workload_percentage": "Percentage of a teacher's maximum capacity being used (typically based on 20 hours/week maximum)"
    },
    "insights": {
        "high_workload": "Teachers with >80% workload may be overloaded and need workload redistribution",
        "low_workload": "Teachers with <20% workload have capacity for additional classes",
        "balanced_workload": "Ideal workload is 60-80% to allow for preparation time and flexibility"
    }
}

SPACE_OCCUPANCY_REPORT_DATA = {
    "description": "The Space Occupancy Report shows how efficiently rooms and facilities are being utilized",
    "metrics_explanation": {
        "total_spaces": "The total number of rooms, labs, and lecture halls available for scheduling",
        "average_occupancy": "The average percentage of time slots that rooms are occupied across all spaces",
        "total_capacity": "The sum of seating capacity across all available spaces",
        "occupied_slots": "Number of time slots in a week where the room has scheduled classes",
        "total_slots": "Total available time slots in a week (typically 45 for 9 periods × 5 days)",
        "occupancy_rate": "Percentage of time slots that are occupied (occupied_slots / total_slots × 100)"
    },
    "insights": {
        "high_occupancy": "Rooms with >80% occupancy are heavily used and may need scheduling optimization",
        "low_occupancy": "Rooms with <20% occupancy are underutilized and could accommodate more classes",
        "optimal_occupancy": "60-70% occupancy allows for flexibility and maintenance time"
    }
}

# Dashboard Features
ADMIN_DASHBOARD_FEATURES = {
    "timetable_management": {
        "description": "Generate, view, and manage timetables using various optimization algorithms",
        "features": ["Algorithm selection (GA, NSGA-II, CO)", "Timetable generation", "Performance metrics", "Export options"]
    },
    "data_management": {
        "description": "Manage core system data including faculty, subjects, rooms, and schedules",
        "features": ["Faculty management", "Subject management", "Room management", "Bulk data import"]
    },
    "reports": {
        "description": "View comprehensive reports on system utilization and performance",
        "features": ["Teacher Allocation Report", "Space Occupancy Report", "Timetable Analytics"]
    },
    "user_management": {
        "description": "Manage user accounts, roles, and permissions",
        "features": ["User creation", "Role assignment", "Permission management"]
    },
    "faculty_availability": {
        "description": "Manage faculty unavailability requests and substitute assignments",
        "features": ["View requests", "Approve/deny requests", "Assign substitutes", "Calendar view"]
    }
}

FACULTY_DASHBOARD_FEATURES = {
    "personal_timetable": {
        "description": "View your personal teaching schedule and class assignments",
        "features": ["Weekly schedule", "Class details", "Room assignments", "Student groups"]
    },
    "availability_management": {
        "description": "Request time off and manage your availability",
        "features": ["Submit unavailability requests", "View request status", "Specify leave types"]
    },
    "teaching_assignments": {
        "description": "View your assigned subjects and teaching responsibilities",
        "features": ["Subject list", "Teaching hours", "Student groups", "Room assignments"]
    }
}

STUDENT_DASHBOARD_FEATURES = {
    "class_schedule": {
        "description": "View your class timetable and schedule information",
        "features": ["Weekly timetable", "Class locations", "Teacher information", "Subject details"]
    },
    "room_finder": {
        "description": "Find available rooms and class locations",
        "features": ["Room availability", "Location finder", "Facility information"]
    }
}

# Algorithm Explanations (Simple Terms)
ALGORITHM_EXPLANATIONS = {
    "genetic_algorithm": {
        "simple_explanation": "Think of creating timetables like breeding the best solutions. We start with many random timetables, keep the best ones, combine their good features, and make small random changes. After many generations, we get an excellent timetable - just like how nature creates well-adapted animals!",
        "use_case": "Best for finding good overall solutions when you have many competing requirements",
        "pros": ["Finds creative solutions", "Handles complex constraints", "Good for multi-objective problems"],
        "cons": ["Takes time to run", "Results may vary between runs"]
    },
    "nsga2": {
        "simple_explanation": "This is like having multiple judges scoring timetables on different criteria (teacher satisfaction, room utilization, student preferences). Instead of one 'best' solution, it finds many good solutions that excel in different areas, letting you choose based on your priorities.",
        "use_case": "When you need to balance multiple conflicting goals simultaneously",
        "pros": ["Provides multiple solution options", "Balances competing objectives", "Shows trade-offs clearly"],
        "cons": ["More complex to understand", "Requires choosing from multiple solutions"]
    },
    "constraint_optimization": {
        "simple_explanation": "This works like solving a jigsaw puzzle with strict rules. Each class is a puzzle piece that must fit perfectly - no teacher can be in two places at once, rooms can't be overbooked, and students need reasonable schedules. The algorithm finds arrangements where all rules are satisfied.",
        "use_case": "When you have strict requirements that absolutely must be met",
        "pros": ["Guarantees all rules are followed", "Fast and reliable", "Easy to understand results"],
        "cons": ["May not find solutions if constraints are too strict", "Less creative than other methods"]
    }
}

# System Features
SYSTEM_FEATURES = {
    "etl_system": {
        "description": "Bulk data import and export system for managing large datasets",
        "features": ["Template download", "Data validation", "Impact analysis", "Bulk upload"]
    },
    "notification_system": {
        "description": "Real-time notifications for important system events",
        "features": ["Faculty requests", "System updates", "Error alerts", "Status changes"]
    },
    "role_based_access": {
        "description": "Security system that controls what users can see and do",
        "roles": {
            "admin": "Full system access, can manage all data and users",
            "faculty": "Can view personal schedule and manage availability",
            "student": "Can view class schedules and find rooms"
        }
    }
}

# Common Questions and Answers
COMMON_QA = [
    {
        "question": "What does the Teacher Allocation Report show?",
        "answer": "The Teacher Allocation Report shows how teaching workload is distributed across faculty. It displays each teacher's assigned subjects, weekly teaching hours, and workload percentage. This helps administrators ensure fair distribution of teaching responsibilities and identify teachers who may be overloaded or have capacity for additional classes."
    },
    {
        "question": "How is workload percentage calculated?",
        "answer": "Workload percentage is calculated based on a teacher's assigned hours compared to their maximum capacity (typically 20 hours per week). For example, if a teacher has 6 hours of classes per week, their workload is 30% (6/20 × 100). This helps ensure teachers aren't overloaded and have time for preparation and other duties."
    },
    {
        "question": "What does the Space Occupancy Report tell me?",
        "answer": "The Space Occupancy Report shows how efficiently rooms are being used. It displays each room's capacity, how many time slots are occupied, and the occupancy rate. This helps identify underutilized rooms that could accommodate more classes and overused rooms that might need scheduling optimization."
    },
    {
        "question": "How is occupancy rate calculated?",
        "answer": "Occupancy rate is calculated as (occupied time slots / total available time slots) × 100. For example, if a room has classes in 3 out of 45 possible weekly time slots, the occupancy rate is 7% (3/45 × 100). This shows how much of the room's potential is being used."
    },
    {
        "question": "What's the difference between the three algorithms?",
        "answer": "Genetic Algorithm is like evolution - it breeds better solutions over time. NSGA-II is like having multiple judges scoring on different criteria. Constraint Optimization is like solving a puzzle with strict rules. Each has strengths: GA for creativity, NSGA-II for balancing multiple goals, and CO for meeting strict requirements."
    },
    {
        "question": "How do I request time off as faculty?",
        "answer": "Go to your Faculty Dashboard and click on 'Availability Management'. You can submit an unavailability request by selecting the date, choosing a leave type (sick leave, personal leave, conference, etc.), and providing a reason. The request will be sent to administrators for approval."
    },
    {
        "question": "How can I see my teaching schedule?",
        "answer": "Your teaching schedule is available on your Faculty Dashboard under 'Personal Timetable'. This shows your weekly schedule with class times, subjects, rooms, and student groups. You can also export this schedule or view it in different formats."
    },
    {
        "question": "Where can I find available rooms?",
        "answer": "Room availability can be found in the Space Occupancy Report or through the room finder feature. This shows which rooms are free during specific time slots and their capacity and facilities."
    }
]

# Context-Aware Responses
CONTEXT_RESPONSES = {
    "teacher_allocation_page": {
        "greeting": "I can see you're viewing the Teacher Allocation Report. This shows how teaching workload is distributed across faculty members.",
        "help_topics": ["Explain workload percentages", "Identify overloaded teachers", "Find teachers with capacity", "Understand the metrics"]
    },
    "space_occupancy_page": {
        "greeting": "You're looking at the Space Occupancy Report. This shows how efficiently rooms and facilities are being utilized.",
        "help_topics": ["Explain occupancy rates", "Find underutilized rooms", "Identify busy rooms", "Understand capacity metrics"]
    },
    "admin_dashboard": {
        "greeting": "Welcome to the Admin Dashboard! You have access to all system management features.",
        "help_topics": ["Generate timetables", "Manage faculty requests", "View reports", "Manage users"]
    },
    "faculty_dashboard": {
        "greeting": "Welcome to your Faculty Dashboard! Here you can manage your schedule and availability.",
        "help_topics": ["View my schedule", "Request time off", "Check teaching assignments", "Update availability"]
    },
    "student_dashboard": {
        "greeting": "Welcome to your Student Dashboard! Here you can view your class schedule and find rooms.",
        "help_topics": ["View my timetable", "Find empty rooms", "Check class locations", "See teacher information"]
    }
}

def get_enhanced_training_data():
    """Return all enhanced training data for the chatbot"""
    return {
        "teacher_allocation": TEACHER_ALLOCATION_REPORT_DATA,
        "space_occupancy": SPACE_OCCUPANCY_REPORT_DATA,
        "admin_features": ADMIN_DASHBOARD_FEATURES,
        "faculty_features": FACULTY_DASHBOARD_FEATURES,
        "student_features": STUDENT_DASHBOARD_FEATURES,
        "algorithms": ALGORITHM_EXPLANATIONS,
        "system_features": SYSTEM_FEATURES,
        "common_qa": COMMON_QA,
        "context_responses": CONTEXT_RESPONSES
    }

def get_context_response(page_context: str, user_role: str = None):
    """Get context-aware greeting and help topics for current page"""
    context_key = page_context.lower().replace(" ", "_").replace("-", "_")
    
    if context_key in CONTEXT_RESPONSES:
        response = CONTEXT_RESPONSES[context_key].copy()
        
        # Customize based on user role
        if user_role:
            if user_role == "admin" and "admin" not in context_key:
                response["greeting"] += " As an admin, you have full access to all features."
            elif user_role == "faculty" and "faculty" not in context_key:
                response["greeting"] += " You can also access your faculty dashboard for personal schedule management."
            elif user_role == "student" and "student" not in context_key:
                response["greeting"] += " You can view your class schedule from your student dashboard."
        
        return response
    
    return {
        "greeting": "I'm here to help you with the timetable system!",
        "help_topics": ["Show my schedule", "Explain features", "Find information", "Get help"]
    }

def search_knowledge_base(query: str):
    """Search the knowledge base for relevant information"""
    query_lower = query.lower()
    results = []
    
    # Search common Q&A
    for qa in COMMON_QA:
        if any(keyword in query_lower for keyword in qa["question"].lower().split()):
            results.append(qa)
    
    # Search algorithm explanations
    if any(keyword in query_lower for keyword in ["algorithm", "genetic", "nsga", "constraint", "optimization"]):
        for alg_name, alg_data in ALGORITHM_EXPLANATIONS.items():
            if alg_name.replace("_", " ") in query_lower or any(keyword in query_lower for keyword in alg_name.split("_")):
                results.append({
                    "question": f"How does {alg_name.replace('_', ' ').title()} work?",
                    "answer": alg_data["simple_explanation"]
                })
    
    return results[:3]  # Return top 3 results 