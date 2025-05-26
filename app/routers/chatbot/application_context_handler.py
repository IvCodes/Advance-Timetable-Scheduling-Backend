"""
Application Context Handler for Timetable Assistant Chatbot

This module handles page context awareness and provides context-specific responses
based on the user's current location in the application.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from .enhanced_training_data import get_context_response, search_knowledge_base, get_enhanced_training_data

logger = logging.getLogger(__name__)

class ApplicationContextHandler:
    """
    Handles application context awareness for the chatbot.
    Provides context-specific responses based on current page/route.
    """
    
    def __init__(self):
        """Initialize the application context handler."""
        self.training_data = get_enhanced_training_data()
        
        # Define page context mappings
        self.page_contexts = {
            # Admin routes
            "/admin/dashboard": "admin_dashboard",
            "/admin/timetable": "timetable_management",
            "/admin/reports/teacher-allocation": "teacher_allocation_page",
            "/admin/reports/space-occupancy": "space_occupancy_page",
            "/admin/data-management": "data_management",
            "/admin/user-management": "user_management",
            "/admin/faculty-availability": "faculty_availability_management",
            
            # Faculty routes
            "/faculty/dashboard": "faculty_dashboard",
            "/faculty/timetable": "faculty_timetable",
            "/faculty/availability": "faculty_availability",
            
            # Student routes
            "/student/dashboard": "student_dashboard",
            "/student/timetable": "student_timetable",
            "/student/rooms": "room_finder",
            
            # General routes
            "/timetable": "timetable_view",
            "/reports": "reports_overview"
        }
        
        # Define context-specific help patterns
        self.context_help_patterns = {
            "teacher_allocation_page": [
                "workload", "teaching hours", "allocation", "teacher", "faculty",
                "percentage", "capacity", "distribution", "overload"
            ],
            "space_occupancy_page": [
                "room", "space", "occupancy", "capacity", "utilization",
                "availability", "slots", "lecture hall", "lab"
            ],
            "admin_dashboard": [
                "manage", "generate", "timetable", "algorithm", "reports",
                "users", "faculty", "data", "system"
            ],
            "faculty_dashboard": [
                "schedule", "availability", "teaching", "classes", "request",
                "time off", "personal", "timetable"
            ],
            "student_dashboard": [
                "classes", "schedule", "timetable", "room", "location",
                "teacher", "subject", "time"
            ]
        }
    
    def get_context_from_route(self, route: str) -> str:
        """
        Extract context from the current route/page.
        
        Args:
            route: Current route/page path
            
        Returns:
            Context identifier for the current page
        """
        # Normalize route
        route = route.lower().strip()
        if route.endswith('/'):
            route = route[:-1]
        
        # Direct mapping
        if route in self.page_contexts:
            return self.page_contexts[route]
        
        # Partial matching for dynamic routes
        for page_route, context in self.page_contexts.items():
            if route.startswith(page_route) or page_route in route:
                return context
        
        # Default context
        return "general"
    
    def get_context_aware_response(self, 
                                 query: str, 
                                 page_context: str, 
                                 user_role: str = None,
                                 current_data: Dict = None) -> Tuple[str, List[str], bool]:
        """
        Generate a context-aware response based on current page and user role.
        
        Args:
            query: User's query
            page_context: Current page context
            user_role: User's role (admin, faculty, student)
            current_data: Current page data (optional)
            
        Returns:
            Tuple of (response, suggestions, handled)
        """
        try:
            query_lower = query.lower()
            
            # Check if this is a context-specific query
            if self._is_context_specific_query(query_lower, page_context):
                return self._handle_context_specific_query(query, page_context, user_role, current_data)
            
            # Check if user is asking for help or explanation of current page
            if any(keyword in query_lower for keyword in ["help", "what is this", "explain", "what does", "how do"]):
                return self._handle_page_explanation(page_context, user_role, current_data)
            
            # Search knowledge base for relevant information
            knowledge_results = search_knowledge_base(query)
            if knowledge_results:
                best_match = knowledge_results[0]
                suggestions = self._get_context_suggestions(page_context, user_role)
                return best_match["answer"], suggestions, True
            
            # Not handled by context handler
            return "", [], False
            
        except Exception as e:
            logger.error(f"Error in context-aware response: {str(e)}")
            return "", [], False
    
    def _is_context_specific_query(self, query: str, page_context: str) -> bool:
        """Check if the query is specific to the current page context."""
        if page_context not in self.context_help_patterns:
            return False
        
        context_keywords = self.context_help_patterns[page_context]
        return any(keyword in query for keyword in context_keywords)
    
    def _handle_context_specific_query(self, 
                                     query: str, 
                                     page_context: str, 
                                     user_role: str,
                                     current_data: Dict = None) -> Tuple[str, List[str], bool]:
        """Handle queries specific to the current page context."""
        query_lower = query.lower()
        
        if page_context == "teacher_allocation_page":
            return self._handle_teacher_allocation_query(query_lower, current_data)
        elif page_context == "space_occupancy_page":
            return self._handle_space_occupancy_query(query_lower, current_data)
        elif page_context == "admin_dashboard":
            return self._handle_admin_dashboard_query(query_lower, user_role)
        elif page_context == "faculty_dashboard":
            return self._handle_faculty_dashboard_query(query_lower, user_role)
        elif page_context == "student_dashboard":
            return self._handle_student_dashboard_query(query_lower, user_role)
        
        return "", [], False
    
    def _handle_teacher_allocation_query(self, query: str, current_data: Dict = None) -> Tuple[str, List[str], bool]:
        """Handle Teacher Allocation Report specific queries."""
        teacher_data = self.training_data["teacher_allocation"]
        
        if "workload" in query and "percentage" in query:
            response = teacher_data["metrics_explanation"]["workload_percentage"]
            if current_data and "average_workload" in current_data:
                response += f" Currently, your system shows an average workload of {current_data['average_workload']}."
            suggestions = ["Which teachers are overloaded?", "Which teachers have capacity?", "How to balance workload?"]
            return response, suggestions, True
        
        elif "total teachers" in query or "how many teachers" in query:
            response = teacher_data["metrics_explanation"]["total_teachers"]
            if current_data and "total_teachers" in current_data:
                response += f" Your system currently has {current_data['total_teachers']} teachers."
            suggestions = ["Show teacher details", "Explain workload distribution", "View teaching hours"]
            return response, suggestions, True
        
        elif "teaching hours" in query:
            response = teacher_data["metrics_explanation"]["total_teaching_hours"]
            if current_data and "total_teaching_hours" in current_data:
                response += f" Currently, there are {current_data['total_teaching_hours']} total teaching hours assigned."
            suggestions = ["How are hours distributed?", "Which teachers teach most?", "Optimize hour allocation"]
            return response, suggestions, True
        
        elif "overload" in query or "too much" in query:
            response = teacher_data["insights"]["high_workload"]
            suggestions = ["Show overloaded teachers", "How to redistribute workload?", "Set workload limits"]
            return response, suggestions, True
        
        elif "capacity" in query or "available" in query:
            response = teacher_data["insights"]["low_workload"]
            suggestions = ["Show available teachers", "Assign more classes", "Balance teaching load"]
            return response, suggestions, True
        
        return "", [], False
    
    def _handle_space_occupancy_query(self, query: str, current_data: Dict = None) -> Tuple[str, List[str], bool]:
        """Handle Space Occupancy Report specific queries."""
        space_data = self.training_data["space_occupancy"]
        
        if "occupancy rate" in query or "how is occupancy calculated" in query:
            response = space_data["metrics_explanation"]["occupancy_rate"]
            suggestions = ["Show room utilization", "Find underused rooms", "Optimize room usage"]
            return response, suggestions, True
        
        elif "total spaces" in query or "how many rooms" in query:
            response = space_data["metrics_explanation"]["total_spaces"]
            if current_data and "total_spaces" in current_data:
                response += f" Your system has {current_data['total_spaces']} available spaces."
            suggestions = ["Show space details", "Check room capacity", "View availability"]
            return response, suggestions, True
        
        elif "capacity" in query and "total" in query:
            response = space_data["metrics_explanation"]["total_capacity"]
            if current_data and "total_capacity" in current_data:
                response += f" The total capacity across all spaces is {current_data['total_capacity']} students."
            suggestions = ["Show largest rooms", "Check room sizes", "Find suitable rooms"]
            return response, suggestions, True
        
        elif "underutilized" in query or "empty" in query or "unused" in query:
            response = space_data["insights"]["low_occupancy"]
            suggestions = ["Show empty rooms", "Schedule more classes", "Optimize space usage"]
            return response, suggestions, True
        
        elif "busy" in query or "overused" in query or "full" in query:
            response = space_data["insights"]["high_occupancy"]
            suggestions = ["Show busy rooms", "Find alternatives", "Redistribute classes"]
            return response, suggestions, True
        
        return "", [], False
    
    def _handle_admin_dashboard_query(self, query: str, user_role: str) -> Tuple[str, List[str], bool]:
        """Handle Admin Dashboard specific queries."""
        admin_features = self.training_data["admin_features"]
        
        if "generate timetable" in query or "create schedule" in query:
            response = admin_features["timetable_management"]["description"]
            suggestions = ["Choose algorithm", "Set constraints", "View results", "Export timetable"]
            return response, suggestions, True
        
        elif "manage faculty" in query or "faculty requests" in query:
            response = admin_features["faculty_availability"]["description"]
            suggestions = ["View pending requests", "Approve requests", "Assign substitutes", "Calendar view"]
            return response, suggestions, True
        
        elif "reports" in query:
            response = admin_features["reports"]["description"]
            suggestions = ["Teacher Allocation Report", "Space Occupancy Report", "System Analytics"]
            return response, suggestions, True
        
        elif "manage users" in query or "user management" in query:
            response = admin_features["user_management"]["description"]
            suggestions = ["Create users", "Assign roles", "Manage permissions", "View user list"]
            return response, suggestions, True
        
        return "", [], False
    
    def _handle_faculty_dashboard_query(self, query: str, user_role: str) -> Tuple[str, List[str], bool]:
        """Handle Faculty Dashboard specific queries."""
        faculty_features = self.training_data["faculty_features"]
        
        if "my schedule" in query or "my timetable" in query:
            response = faculty_features["personal_timetable"]["description"]
            suggestions = ["View this week", "Check next week", "Export schedule", "Find my rooms"]
            return response, suggestions, True
        
        elif "request time off" in query or "availability" in query:
            response = faculty_features["availability_management"]["description"]
            suggestions = ["Submit new request", "Check request status", "View calendar", "Cancel request"]
            return response, suggestions, True
        
        elif "teaching assignments" in query or "my subjects" in query:
            response = faculty_features["teaching_assignments"]["description"]
            suggestions = ["View subjects", "Check teaching hours", "See student groups", "Room assignments"]
            return response, suggestions, True
        
        return "", [], False
    
    def _handle_student_dashboard_query(self, query: str, user_role: str) -> Tuple[str, List[str], bool]:
        """Handle Student Dashboard specific queries."""
        student_features = self.training_data["student_features"]
        
        if "my classes" in query or "my schedule" in query:
            response = student_features["class_schedule"]["description"]
            suggestions = ["Today's classes", "Tomorrow's classes", "This week", "Find classroom"]
            return response, suggestions, True
        
        elif "find room" in query or "room location" in query:
            response = student_features["room_finder"]["description"]
            suggestions = ["Available rooms now", "Room facilities", "Building map", "Class locations"]
            return response, suggestions, True
        
        return "", [], False
    
    def _handle_page_explanation(self, page_context: str, user_role: str, current_data: Dict = None) -> Tuple[str, List[str], bool]:
        """Provide explanation of the current page."""
        context_response = get_context_response(page_context, user_role)
        
        response = context_response["greeting"]
        
        # Add current data context if available
        if current_data and page_context == "teacher_allocation_page":
            response += f"\n\nCurrent statistics: {current_data.get('total_teachers', 'N/A')} teachers, "
            response += f"{current_data.get('average_workload', 'N/A')} average workload, "
            response += f"{current_data.get('total_teaching_hours', 'N/A')} total teaching hours."
        
        elif current_data and page_context == "space_occupancy_page":
            response += f"\n\nCurrent statistics: {current_data.get('total_spaces', 'N/A')} spaces, "
            response += f"{current_data.get('average_occupancy', 'N/A')} average occupancy, "
            response += f"{current_data.get('total_capacity', 'N/A')} total capacity."
        
        suggestions = context_response["help_topics"]
        return response, suggestions, True
    
    def _get_context_suggestions(self, page_context: str, user_role: str) -> List[str]:
        """Get context-appropriate suggestions."""
        context_response = get_context_response(page_context, user_role)
        return context_response["help_topics"]
    
    def get_page_specific_greeting(self, page_context: str, user_role: str) -> str:
        """Get a greeting specific to the current page and user role."""
        context_response = get_context_response(page_context, user_role)
        return context_response["greeting"] 