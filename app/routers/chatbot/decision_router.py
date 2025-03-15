from typing import Dict, List, Any, Tuple, Optional
import logging
import jwt
from datetime import datetime
import os
from .rule_handler import RuleBasedHandler
from .llm_handler import LLMHandler
 
# Set up logging
logger = logging.getLogger(__name__)

class DecisionRouter:
    """
    Routes user queries between rule-based and LLM handlers based on query complexity.
    This ensures efficient use of resources by only using the LLM when necessary.
    """
    
    def __init__(self):
        """Initialize the decision router with both handler types."""
        self.rule_handler = RuleBasedHandler()
        self.llm_handler = LLMHandler()
        
    async def process_query(self, 
                      query: str, 
                      user_data: Dict[str, Any], 
                      conversation_history: List[Dict[str, Any]]
                     ) -> Dict[str, Any]:
        """
        Process a user query by routing to the appropriate handler.
        
        Args:
            query: The user's text query
            user_data: Dictionary containing user context (role, id, subgroup, etc.)
            conversation_history: List of previous messages in the conversation
            
        Returns:
            Dictionary containing the response and related metadata
        """
        try:
            # First try the rule-based handler (fast and resource-efficient)
            response, handled, suggestions = self.rule_handler.process_query(query, user_data)
            
            # If rule-based handler couldn't process it, use the LLM handler
            if not handled:
                logger.info(f"Rule-based handler could not process query: '{query}'. Routing to LLM.")
                response, suggestions = await self.llm_handler.process_query(
                    query, 
                    user_data,
                    conversation_history
                )
                handler_type = "llm"
            else:
                handler_type = "rule_based"
                logger.info(f"Query handled by rule-based system: '{query}'")
            
            # Return the result with metadata
            return {
                "response": response,
                "handler_type": handler_type,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Error in decision router: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an error while processing your request. Please try again.",
                "handler_type": "error",
                "suggestions": ["Show my timetable", "When is my next class?", "Help"]
            }
    
    def get_user_data_from_token(self, token: str) -> Dict[str, Any]:
        """
        Extract user data from authentication token.
        
        Args:
            token: JWT token
            
        Returns:
            Dictionary with user data
        """
        try:
            # Get the secret key for JWT verification
            secret_key = os.environ.get("JWT_SECRET_KEY", "your-secret-key")
            
            # Decode and verify the JWT token
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            
            # Extract user data
            user_id = payload.get("sub") or payload.get("user_id") or payload.get("id")
            role = payload.get("role", "student")
            
            # In a production setup, you would fetch additional user data from the database
            # For now, we're using data from the token and some placeholder values
            user_data = {
                "id": user_id,
                "role": role,
                "first_name": payload.get("first_name", "User"),
                "last_name": payload.get("last_name", ""),
            }
            
            # Add role-specific data
            if role == "student":
                user_data.update({
                    "subgroup": payload.get("subgroup", "SEM202"),  # Use actual subgroup from token
                    "year": payload.get("year", 2),
                    "subjects": payload.get("subjects", ["CS101", "CS205", "MA202"])
                })
            elif role == "faculty":
                user_data.update({
                    "faculty_id": payload.get("faculty_id", ""),
                    "departments": payload.get("departments", []),
                    "subjects": payload.get("subjects", [])
                })
            
            return user_data
            
        except jwt.PyJWTError as e:
            logger.error(f"Error decoding JWT token: {str(e)}")
            # Return default user data if token verification fails
            return {
                "id": "unknown",
                "role": "student",
                "subgroup": "unknown",
                "first_name": "Guest",
                "year": 1,
                "subjects": []
            }
