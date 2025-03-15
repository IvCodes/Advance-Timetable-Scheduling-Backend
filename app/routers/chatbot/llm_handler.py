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
        else:
            logger.info("OPENROUTER_API_KEY found in environment variables.")
            
        # Model configuration
        self.model_name = "deepseek/deepseek-chat:free"
        self.temperature = 0.7
        self.max_tokens = 300
        
        # Use localhost for the HTTP referrer in testing environment
        referer = "http://localhost:8080"
        
        try:
            # Initialize OpenAI client for OpenRouter
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": referer,
                    "X-Title": "Timetable Scheduling Assistant"
                }
            )
            logger.info(f"LLM Handler initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            self.client = None
        
    def process_query(self, 
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
            # Check if client is properly initialized
            if self.client is None:
                logger.error("LLM client is not initialized. Cannot process query.")
                return "I'm sorry, I'm having trouble connecting to my AI service. Please try again later or contact support.", ["Try again", "Contact support"]
                
            # Format conversation history for the LLM
            formatted_history = self._format_conversation_history(conversation_history)
            
            # Generate context about the user for personalized responses
            user_context = self._generate_user_context(user_data)
            
            # Create the system message with instructions
            system_message = {
                "role": "system",
                "content": self._create_system_prompt(user_context)
            }
            
            # Combine everything for the final prompt
            complete_messages = [system_message] + formatted_history + [{"role": "user", "content": query}]
            
            logger.info(f"Sending query to LLM: {query[:50]}...")
            
            # Get response from LLM API
            response = self._get_llm_response(complete_messages)
            
            # Generate suggestions based on the query
            suggestions = self._generate_suggestions(query)
            
            return response, suggestions
            
        except Exception as e:
            logger.error(f"Error in LLM handler: {str(e)}")
            return "I'm sorry, I encountered an error processing your request. Please try again.", ["Try again", "Contact support"]
    
    def _get_llm_response(self, messages: List[Dict[str, Any]]) -> str:
        """
        Send a request to the LLM API and return the response.
        
        Args:
            messages: List of message objects in the OpenAI Chat format
            
        Returns:
            The text response from the LLM
        """
        try:
            logger.info("Sending request to OpenRouter API")
            
            # Make the API request to OpenRouter
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            logger.info(f"Received response from OpenRouter API: status_code={getattr(response, 'status_code', 'N/A')}")
            
            # Extract and return the response text
            content = response.choices[0].message.content
            logger.info(f"Response content: {content[:50]}...")
            return content
            
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error calling LLM API: {error_type}: {str(e)}")
            # Add more verbose logging to help debugging
            if hasattr(e, 'response') and hasattr(e.response, 'json'):
                try:
                    logger.error(f"API error details: {e.response.json()}")
                except Exception as json_error:
                    logger.error(f"Failed to parse error response: {str(json_error)}")
            raise
    
    def _format_conversation_history(self, conversation_history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format conversation history for LLM input."""
        formatted_history = []
        for msg in conversation_history:
            if msg.get("role") in ["user", "assistant"] and msg.get("content"):
                formatted_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        return formatted_history
    
    def _generate_user_context(self, user_data: Dict[str, Any]) -> str:
        """Generate context about the user for personalized responses."""
        user_id = user_data.get("user_id", "unknown")
        return f"You are chatting with user {user_id}."
    
    def _create_system_prompt(self, user_context: str) -> str:
        """Create system prompt with instructions."""
        return f"""You are a helpful Timetable Assistant for an advanced academic scheduling system. {user_context}
        
Your role is to help users understand the timetable scheduling system and provide information about:

1. EXPLAINING ALGORITHMS IN SIMPLE TERMS:
   - Genetic Algorithms: "Think of class schedules as if they're competing in a tournament. We start with many possible schedules, keep the best ones (like the winners of each round), combine their good qualities, and occasionally make small random changes. After many rounds, we end up with an optimal schedule - just like natural selection produces well-adapted organisms."
   
   - Constraint Satisfaction: "This is like solving a puzzle where each piece (a class) must fit perfectly with others. We have rules like 'no teacher can be in two places at once' or 'this room can only hold 30 students.' The algorithm finds arrangements where all these rules are satisfied."
   
   - Simulated Annealing: "Imagine trying to find the lowest point in a hilly landscape while blindfolded. Sometimes you need to walk uphill temporarily to avoid getting stuck in a small valley, when there's a much deeper valley elsewhere. This algorithm works similarly by sometimes accepting worse solutions temporarily to find better ones later."

2. APPLICATION FEATURES:
   - How to view personal timetables
   - How to find free rooms
   - How to check when classes are scheduled
   - Other user-specific features

Respond in a friendly, helpful manner. Keep answers concise but thorough. Avoid technical jargon and use everyday analogies when explaining complex concepts.
"""
    
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
