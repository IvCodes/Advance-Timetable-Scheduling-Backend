from typing import Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import logging
from bson import ObjectId
from app.routers.chatbot.llm_handler import LLMHandler
from app.utils.database import db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Initialize LLM handler
llm_handler = LLMHandler()

# Constants
PUSH_OPERATION = "$push"

# Router
router = APIRouter()

# Models
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    suggestions: List[str] = []

# Routes
@router.post("/message", response_model=ChatResponse)
def process_message(
    chat_request: ChatRequest
) -> ChatResponse:
    """
    Process an incoming chat message and generate a response.
    
    Args:
        chat_request: The chat request containing the user message
        
    Returns:
        ChatResponse containing the assistant's response and conversation ID
    """
    try:
        # Log the incoming message
        logger.info(f"Received chat request: message='{chat_request.message}' user_id='{chat_request.user_id}' conversation_id='{chat_request.conversation_id}'")
        
        # Handle conversation history
        conversation_id, mongo_id = _handle_conversation_history(chat_request)
        
        # Generate response
        result = _generate_response(mongo_id, chat_request)
        response = result[0]
        suggestions = result[1]
        
        return ChatResponse(
            message=response,
            conversation_id=conversation_id,
            suggestions=suggestions
        )
    except Exception as e:
        logger.error("Error processing chat message: " + str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

# Helper functions to reduce complexity
def _handle_conversation_history(chat_request):
    """Process and store conversation history, return conversation_id and mongo_id."""
    conversation_id = chat_request.conversation_id
    if not conversation_id or conversation_id == "string":  # Handle default Swagger UI value
        # Create a new conversation
        result = db.chat_conversations.insert_one({
            "user_id": chat_request.user_id or "anonymous",
            "created_at": datetime.now(),
            "messages": []
        })
        conversation_id = str(result.inserted_id)
        logger.info(f"Created new conversation with ID: {conversation_id}")
    else:
        logger.info(f"Using existing conversation with ID: {conversation_id}")
    
    # Store the user message
    new_message = {
        "role": "user",
        "content": chat_request.message,
        "timestamp": datetime.now()
    }
    
    try:
        # Try to convert string ID to ObjectId for MongoDB
        try:
            mongo_id = ObjectId(conversation_id)
        except Exception as e:
            logger.warning(f"Invalid conversation ID format: {e}, creating new conversation")
            result = db.chat_conversations.insert_one({
                "user_id": chat_request.user_id or "anonymous",
                "created_at": datetime.now(),
                "messages": [new_message]
            })
            conversation_id = str(result.inserted_id)
            mongo_id = ObjectId(conversation_id)
            logger.info(f"Created new conversation with ID: {conversation_id}")
        
        # Update the conversation with the new message
        update_result = db.chat_conversations.update_one(
            {"_id": mongo_id},
            {PUSH_OPERATION: {"messages": new_message}}
        )
        
        if update_result.matched_count == 0:
            # If no document was matched, the conversation ID might be invalid
            # Create a new conversation instead
            logger.warning(f"Conversation ID {conversation_id} not found, creating new conversation")
            result = db.chat_conversations.insert_one({
                "user_id": chat_request.user_id or "anonymous",
                "created_at": datetime.now(),
                "messages": [new_message]
            })
            conversation_id = str(result.inserted_id)
            mongo_id = ObjectId(conversation_id)
            logger.info(f"Created new conversation with ID: {conversation_id}")
    except Exception as e:
        logger.error(f"Error updating conversation: {str(e)}")
        # Create a new conversation as fallback
        result = db.chat_conversations.insert_one({
            "user_id": chat_request.user_id or "anonymous",
            "created_at": datetime.now(),
            "messages": [new_message]
        })
        conversation_id = str(result.inserted_id)
        mongo_id = ObjectId(conversation_id)
        logger.info(f"Created new conversation with ID: {conversation_id} after error")
    
    return conversation_id, mongo_id

def _generate_response(mongo_id, chat_request):
    """Generate a response using the LLM handler and store it in the database."""
    try:
        # Get user data from the request
        user_data = {
            "id": chat_request.user_id,
            "role": "student"  # Default role
        }
        
        # Format messages for the LLM
        conversation = db.chat_conversations.find_one({"_id": mongo_id})
        conversation_history = conversation.get("messages", [])
        
        # Process the query using the LLM handler
        logger.info("Sending request to DeepSeek API")
        response, suggestions = llm_handler.process_query(
            chat_request.message,
            user_data,
            conversation_history
        )
        logger.info("Received response from DeepSeek API")
        
        # Add assistant message to conversation history
        try:
            assistant_message = {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now()
            }
            
            db.chat_conversations.update_one(
                {"_id": mongo_id},
                {PUSH_OPERATION: {"messages": assistant_message}}
            )
        except Exception as e:
            logger.error(f"Error storing assistant response in database: {str(e)}")
            # Continue anyway, so the user still gets a response
        
        return response, suggestions
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        # Return a fallback response to the user when the LLM fails
        fallback_response = "I'm experiencing technical difficulties at the moment. Please try again in a few moments or contact support."
        fallback_suggestions = ["Try again", "Contact support", "Ask a different question"]
        
        # Try to store the fallback response in the database
        try:
            fallback_message = {
                "role": "assistant",
                "content": fallback_response,
                "timestamp": datetime.now()
            }
            
            db.chat_conversations.update_one(
                {"_id": mongo_id},
                {PUSH_OPERATION: {"messages": fallback_message}}
            )
        except Exception as db_error:
            logger.error(f"Error storing fallback response: {str(db_error)}")
        
        return fallback_response, fallback_suggestions

@router.get("/history/{conversation_id}", response_model=List[ChatMessage])
def get_conversation_history(
    conversation_id: str
):
    """
    Get conversation history for a given conversation ID.
    
    Args:
        conversation_id: The ID of the conversation to retrieve
        
    Returns:
        List of chat messages in the conversation
    """
    try:
        # Convert string ID to ObjectId
        mongo_id = ObjectId(conversation_id)
        
        # Get conversation from database
        conversation = db.chat_conversations.find_one({"_id": mongo_id})
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation with ID {conversation_id} not found"
            )
        
        # Return messages from the conversation
        return conversation.get("messages", [])
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation history: {str(e)}"
        )
