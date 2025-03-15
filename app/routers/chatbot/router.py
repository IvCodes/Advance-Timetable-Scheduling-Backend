from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from app.utils.database import db
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from bson import ObjectId

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    tags=["chatbot"],
    responses={404: {"description": "Not found"}},
)

# Function to get database as dependency
async def get_database():
    return db

# Chat message models
class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    suggestions: Optional[List[str]] = None

# OAuth scheme for token verification
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Routes
@router.post("/message", response_model=ChatResponse)
async def process_message(
    chat_request: ChatRequest,
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Process a user's chat message and return an appropriate response.
    This endpoint handles the routing between rule-based responses and LLM.
    """
    try:
        # For demo purposes, we're using a simple implementation
        # In production, you would decode and verify the token
        
        # Log the incoming request for debugging
        logger.info(f"Received chat request: {chat_request}")
        
        # Create or retrieve conversation history
        conversation_id = chat_request.conversation_id
        if not conversation_id:
            # Create a new conversation
            conversation_id = str(await db.chat_conversations.insert_one({
                "user_id": chat_request.user_id or "anonymous",
                "created_at": datetime.now(),
                "messages": []
            }).inserted_id)
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
            # Convert string ID to ObjectId for MongoDB
            mongo_id = ObjectId(conversation_id)
            
            # Update the conversation with the new message
            update_result = await db.chat_conversations.update_one(
                {"_id": mongo_id},
                {"$push": {"messages": new_message}}
            )
            
            if update_result.matched_count == 0:
                # If no document was matched, the conversation ID might be invalid
                # Create a new conversation instead
                logger.warning(f"Conversation ID {conversation_id} not found, creating new conversation")
                conversation_id = str(await db.chat_conversations.insert_one({
                    "user_id": chat_request.user_id or "anonymous",
                    "created_at": datetime.now(),
                    "messages": [new_message]
                }).inserted_id)
                logger.info(f"Created new conversation with ID: {conversation_id}")
        except Exception as e:
            logger.error(f"Error updating conversation: {str(e)}")
            # Create a new conversation as fallback
            conversation_id = str(await db.chat_conversations.insert_one({
                "user_id": chat_request.user_id or "anonymous",
                "created_at": datetime.now(),
                "messages": [new_message]
            }).inserted_id)
            logger.info(f"Created new conversation with ID: {conversation_id} after error")
        
        # Process the message (placeholder for now)
        # In phase 2, we'll implement the actual rule-based and LLM routing
        response = "This is a placeholder response from the chatbot."
        
        # Generate suggestions based on the context
        suggestions = ["Show my timetable", "When is my next class?", "Find free rooms"]
        
        # Store the assistant response
        assistant_message = {
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now()
        }
        
        try:
            # Convert string ID to ObjectId for MongoDB
            mongo_id = ObjectId(conversation_id)
            
            # Update the conversation with the assistant's response
            await db.chat_conversations.update_one(
                {"_id": mongo_id},
                {"$push": {"messages": assistant_message}}
            )
        except Exception as e:
            logger.error(f"Error storing assistant response: {str(e)}")
        
        return ChatResponse(
            message=response,
            conversation_id=conversation_id,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

@router.get("/history/{conversation_id}", response_model=List[ChatMessage])
async def get_conversation_history(
    conversation_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Retrieve the conversation history for a specific conversation ID.
    """
    try:
        conversation = await db.chat_conversations.find_one({"_id": ObjectId(conversation_id)})
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return conversation.get("messages", [])
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation history: {str(e)}"
        )
