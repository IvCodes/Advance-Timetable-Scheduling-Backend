import re
from typing import Dict, List, Any, Tuple, Optional
import logging
from datetime import datetime, timedelta
import random

# Set up logging
logger = logging.getLogger(__name__)

# Define constants for common suggestion strings
SHOW_TIMETABLE = "Show my timetable"
NEXT_CLASS = "When is my next class?"
FIND_EMPTY_ROOMS = "Find empty rooms"

class RuleBasedHandler:
    """
    Handles common timetable queries using rule-based pattern matching.
    This is the first-tier response system that processes simple, structured queries.
    """
    
    def __init__(self):
        # Define regex patterns for common queries
        self.patterns = {
            "show_timetable": re.compile(r"(show|display|view|get).*(timetable|schedule|classes)", re.IGNORECASE),
            "next_class": re.compile(r"(when|what).*(next|upcoming) (class|lecture|session)", re.IGNORECASE),
            "find_room": re.compile(r"(find|locate|where).*(room|class|lecture|lab)", re.IGNORECASE),
            "day_schedule": re.compile(r"(what|show).*(class|schedule).*(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)", re.IGNORECASE),
            "subject_info": re.compile(r"(tell|show|info|about).*(subject|course|class|module)\s+([A-Z]{2}\d{3})", re.IGNORECASE),
            "teacher_info": re.compile(r"(who|which).*(teacher|lecturer|professor|faculty).*(teach|taking|for)\s+([A-Z]{2}\d{3})", re.IGNORECASE),
            "deadline_info": re.compile(r"(when|what).*(deadline|due date|submission date).*(assignment|project|homework)", re.IGNORECASE),
            "greeting": re.compile(r"(hi|hello|hey|greetings)", re.IGNORECASE),
            "help": re.compile(r"(help|assist|support|guide)", re.IGNORECASE),
        }
        
        # Greeting responses with time-awareness
        self.greeting_responses = [
            "Hello! How can I help you with your timetable today?",
            "Hi there! What would you like to know about your schedule?",
            "Greetings! I'm your timetable assistant. What can I do for you?",
            "Hello! I'm here to help with all your scheduling needs. What would you like to know?"
        ]
        
        # Help responses
        self.help_responses = [
            "I can help you with:\n- Viewing your timetable\n- Finding when your next class is\n- Locating a specific room\n- Getting information about a subject\n- Finding out which teacher is teaching a course",
            "Here are some things you can ask me:\n- 'Show my schedule for today'\n- 'When is my next class?'\n- 'Who teaches CS101?'\n- 'Where is my next lecture?'\n- 'What's my Friday schedule?'"
        ]

    def process_query(self, query: str, user_data: Dict[str, Any]) -> Tuple[str, bool, Optional[List[str]]]:
        """
        Process a user query using rule-based pattern matching.
        
        Args:
            query: The user's text query
            user_data: Dictionary containing user context (role, id, subgroup, etc.)
            
        Returns:
            Tuple containing:
            - Response text
            - Boolean indicating if query was handled
            - Optional list of follow-up suggestions
        """
        # Process by query type
        handlers = {
            "greeting": self._handle_greeting,
            "help": self._handle_help,
            "show_timetable": self._handle_show_timetable,
            "next_class": self._handle_next_class,
            "day_schedule": self._handle_day_schedule
        }
        
        # Try each pattern handler
        for pattern_key, handler_func in handlers.items():
            if self.patterns[pattern_key].match(query):
                return handler_func(query, user_data)
            
        # Query not handled by rule-based system
        return "", False, None
    
    def _handle_greeting(self, query: str, user_data: Dict[str, Any]) -> Tuple[str, bool, List[str]]:
        """Handle greeting patterns with time-appropriate responses"""
        # Select a greeting based on time of day
        hour = datetime.now().hour
        if 5 <= hour < 12:
            greeting = "Good morning! "
        elif 12 <= hour < 17:
            greeting = "Good afternoon! "
        else:
            greeting = "Good evening! "
            
        response = greeting + random.choice(self.greeting_responses)
        return response, True, [SHOW_TIMETABLE, NEXT_CLASS, "Help me with scheduling"]
    
    def _handle_help(self, query: str, user_data: Dict[str, Any]) -> Tuple[str, bool, List[str]]:
        """Handle help requests with guidance information"""
        response = random.choice(self.help_responses)
        return response, True, [SHOW_TIMETABLE, FIND_EMPTY_ROOMS, "Today's schedule"]
    
    def _handle_show_timetable(self, query: str, user_data: Dict[str, Any]) -> Tuple[str, bool, List[str]]:
        """Handle requests to view timetable"""
        subgroup = user_data.get("subgroup", "unknown")
        response = f"I'll show you the timetable for {subgroup}. Please wait while I fetch that information."
        return response, True, ["Today's classes", "Tomorrow's classes", "This week's schedule"]
    
    def _handle_next_class(self, query: str, user_data: Dict[str, Any]) -> Tuple[str, bool, List[str]]:
        """Handle requests to find the next class"""
        subgroup = user_data.get("subgroup", "unknown")
        response = f"I'll check when your next class is for {subgroup}. This would typically connect to your timetable data."
        return response, True, ["Where is this class?", "What subject is it?", "Who's teaching?"]
    
    def _handle_day_schedule(self, query: str, user_data: Dict[str, Any]) -> Tuple[str, bool, List[str]]:
        """Handle requests for a specific day's schedule"""
        day = self._extract_day_from_query(query)
        subgroup = user_data.get("subgroup", "unknown")
        response = f"I'll get your schedule for {day} (subgroup: {subgroup}). In a full implementation, this would show your specific classes."
        return response, True, [f"What rooms am I in on {day}?", "Who's teaching these classes?"]
    
    def _extract_day_from_query(self, query: str) -> str:
        """Helper method to extract the day from a query"""
        query_lower = query.lower()
        
        if "today" in query_lower:
            return datetime.now().strftime("%A")
        elif "tomorrow" in query_lower:
            return (datetime.now() + timedelta(days=1)).strftime("%A")
        elif "monday" in query_lower:
            return "Monday"
        elif "tuesday" in query_lower:
            return "Tuesday"
        elif "wednesday" in query_lower:
            return "Wednesday"
        elif "thursday" in query_lower:
            return "Thursday"
        elif "friday" in query_lower:
            return "Friday"
        elif "saturday" in query_lower:
            return "Saturday"
        elif "sunday" in query_lower:
            return "Sunday"
        else:
            return "the requested day"
        
    def get_suggestions_for_response(self, response_type: str) -> List[str]:
        """
        Generate context-aware suggestions based on the type of response given.
        
        Args:
            response_type: The type of the last response
            
        Returns:
            A list of suggested follow-up queries
        """
        suggestions = {
            "timetable": ["What's my schedule tomorrow?", "Do I have any evening classes?", "Where is my next class?"],
            "next_class": ["What room is it in?", "Who teaches this class?", "What's after this class?"],
            "room": ["What other classes are in this room?", "Is this room available later?", "Show me all my classes in this room"],
            "subject": ["Who teaches this subject?", "When is the next lecture?", "What's the course outline?"],
            "teacher": ["What other subjects does this teacher teach?", "When are their office hours?", "Show all classes with this teacher"],
            "default": [SHOW_TIMETABLE, NEXT_CLASS, "Find an available room"]
        }
        
        return suggestions.get(response_type, suggestions["default"])
