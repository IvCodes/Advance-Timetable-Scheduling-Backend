from typing import Dict, List, Any, Tuple
import logging
import os
from openai import OpenAI
import json

# Set up logging
logger = logging.getLogger(__name__)

class LLMHandler:
    """
    Handles complex user queries by leveraging a language model.
    This is the second-tier response system that processes queries the rule-based system can't handle.
    """
    
    def __init__(self):
        """Initialize the LLM handler with model configuration."""
        # Get OpenRouter API key from environment variables
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not found in environment variables. LLM integration will not work.")
            
        # Model configuration
        self.model_name = "deepseek/deepseek-chat:free"
        self.temperature = 0.7
        self.max_tokens = 300
        
        # Initialize OpenAI client for OpenRouter
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        
        logger.info(f"LLM Handler initialized with model: {self.model_name}")
    
    async def process_query(self, 
                     query: str, 
                     user_data: Dict[str, Any],
                     conversation_history: List[Dict[str, Any]]
                     ) -> Tuple[str, List[str]]:
        """
        Process a complex user query using a language model.
        
        Args:
            query: The user's text query
            user_data: Dictionary containing user context (role, id, subgroup, etc.)
            conversation_history: List of previous messages in the conversation
            
        Returns:
            Tuple containing:
            - Response text
            - List of follow-up suggestions
        """
        try:
            # Format conversation history for the LLM
            formatted_history = self._format_conversation_history(conversation_history)
            
            # Generate context about the user for personalized responses
            user_context = self._generate_user_context(user_data)
            
            # Create the system message with instructions
            system_message = {
                "role": "system",
                "content": f"""You are a helpful AI assistant for a university timetable scheduling system.
                
Your name is TimetableBot. Be friendly, concise, and helpful.

{user_context}

When responding to queries:
1. If asked about timetables or schedules, provide specific information when available
2. If asked about rooms, classes, or faculty, be specific based on the user's role and subgroup
3. Always be respectful and professional
4. Keep responses brief and to the point
5. Do not make up information if you don't know the answer
                """
            }
            
            # Combine everything for the final prompt
            complete_messages = [system_message] + formatted_history + [{
                "role": "user",
                "content": query
            }]
            
            logger.info(f"Sending query to LLM: {query[:50]}...")
            
            # Get response from LLM API
            response = await self._get_llm_response(complete_messages)
            
            # Generate suggestions based on the query
            suggestions = self._generate_suggestions(query)
            
            return response, suggestions
            
        except Exception as e:
            logger.error(f"Error in LLM handler: {str(e)}")
            return "I'm sorry, I encountered an error processing your request. Please try again.", ["Help", "Show my timetable", "When is my next class?"]
    
    async def _get_llm_response(self, messages: List[Dict[str, Any]]) -> str:
        """
        Send a request to the LLM API and return the response.
        
        Args:
            messages: List of message objects in the OpenAI Chat format
            
        Returns:
            The text response from the LLM
        """
        try:
            # Use localhost for the HTTP referrer in testing environment
            referer = "http://localhost:8080"
            
            # Make the API request to OpenRouter
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                headers={
                    "HTTP-Referer": referer,
                    "X-Title": "Timetable Scheduling Assistant"
                }
            )
            
            # Extract and return the response text
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error calling LLM API: {str(e)}")
            raise
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format conversation history for the LLM prompt."""
        formatted_history = []
        
        # Take only the last 5 messages to avoid context length issues
        recent_history = history[-5:] if len(history) > 5 else history
        
        for message in recent_history:
            role = "assistant" if message["role"] == "bot" else "user"
            formatted_history.append({
                "role": role,
                "content": message["content"]
            })
            
        return formatted_history
    
    def _generate_user_context(self, user_data: Dict[str, Any]) -> str:
        """Generate context about the user for the LLM prompt."""
        context = "User Context:\n"
        
        # Add role-specific information
        if user_data.get("role") == "student":
            context += f"""
- Student: {user_data.get('first_name', 'User')}
- Subgroup: {user_data.get('subgroup', 'Unknown')}
- Year: {user_data.get('year', 'Unknown')}
- Subjects: {', '.join(user_data.get('subjects', ['Unknown']))}
"""
        elif user_data.get("role") == "faculty":
            context += f"""
- Faculty: {user_data.get('first_name', 'User')} {user_data.get('last_name', '')}
- Faculty ID: {user_data.get('faculty_id', 'Unknown')}
- Departments: {', '.join(user_data.get('departments', ['Unknown']))}
- Subjects: {', '.join(user_data.get('subjects', ['Unknown']))}
"""
        else:
            context += f"- User: {user_data.get('first_name', 'User')}\n"
            
        return context
    
    def _generate_suggestions(self, query: str) -> List[str]:
        """Generate follow-up suggestions based on the query."""
        # Default suggestions
        default_suggestions = ["Show my timetable", "When is my next class?", "Find an empty room"]
        
        # Check for query keywords to customize suggestions
        query_lower = query.lower()
        
        if "timetable" in query_lower or "schedule" in query_lower:
            return ["What classes do I have tomorrow?", "Do I have any evening classes?", "When is my next break?"]
        elif "room" in query_lower or "location" in query_lower:
            return ["Is this room available later?", "Show all classes in this room", "Find empty rooms now"]
        elif "teacher" in query_lower or "professor" in query_lower or "faculty" in query_lower:
            return ["What other subjects does this teacher teach?", "When are their office hours?", "Is this teacher available now?"]
        elif "subject" in query_lower or "course" in query_lower or "class" in query_lower:
            return ["Who teaches this subject?", "When is the next lecture?", "What's the syllabus for this course?"]
            
        return default_suggestions
