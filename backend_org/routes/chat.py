from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq  
from dotenv import load_dotenv
import os

from models.models import Conversation, Message
from config.db import get_db
from pydantic import BaseModel
from typing import List
from services.character_generator import CharacterGenerationRequest, generate_character

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Ensure this is set in .env

# Define FastAPI router
router = APIRouter()

# Predefined AI Characters
CHARACTER_PERSONAS = {
    "Chuck the Clown": "You are Chuck, a silly and mischievous clown who loves to make jokes.",
    "Sarcastic Pirate": "You are a pirate with a dry wit and sarcastic tone. You often use pirate lingo.",
    "Professor Sage": "You are an old and wise professor who loves deep discussions and intellectual insights.",
    "Yoda from Star Wars": "You are Yoda from Star Wars. Speak in wise, cryptic phrases, you do.",
}

# Define the prompt template
PROMPT_TEMPLATE = """The following is a conversation between {character} and a user:

{history}

User: {input}

{character}:"""

# Initialize LLM with ChatGroq
llm = ChatGroq(
    model="mixtral-8x7b-32768",
    temperature=0.2,
    max_tokens=512,
)

# Pydantic Models
class ChatRequest(BaseModel):
    user_id: int
    character: str
    message: str

class MessageResponse(BaseModel):
    sender: str
    content: str
    timestamp: str

class ChatHistoryResponse(BaseModel):
    conversation_id: int
    messages: List[MessageResponse]

# ✅ Chat with AI and Save Messages
@router.post("/")
def chat_with_ai(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Handle chat with AI character.
    """
    try:
        # Ensure the conversation exists
        conversation = db.query(Conversation).filter_by(user_id=request.user_id, character=request.character).first()
        if not conversation:
            conversation = Conversation(user_id=request.user_id, character=request.character)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # Retrieve previous chat messages for history
        previous_messages = db.query(Message).filter_by(conversation_id=conversation.id).order_by(Message.timestamp).all()
        history = "\n".join([f"{msg.sender}: {msg.content}" for msg in previous_messages])

        # Store user message
        user_message = Message(conversation_id=conversation.id, sender="User", content=request.message)
        db.add(user_message)
        db.commit()

        # AI character context
        character_persona = CHARACTER_PERSONAS.get(
            request.character, f"You are {request.character}, a custom AI character."
        )

        # ✅ Format `full_context` before passing it to the AI
        full_context = f"{character_persona}\n\n{history}\nUser: {request.message}\n{request.character}:"

        # Initialize the prompt
        prompt = PromptTemplate(
            input_variables=["history", "input", "character"],
            template=PROMPT_TEMPLATE
        )

        chain = LLMChain(llm=llm, prompt=prompt)

        # Generate AI response
        ai_reply = chain.predict(history=history, input=request.message, character=request.character)

        # Store AI response
        ai_message = Message(conversation_id=conversation.id, sender=request.character, content=ai_reply)
        db.add(ai_message)
        db.commit()

        return {"user": request.message, request.character: ai_reply, "conversation_id": conversation.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Retrieve Chat History
@router.get("/history/{user_id}/{character}", response_model=ChatHistoryResponse)
def get_chat_history(user_id: int, character: str, db: Session = Depends(get_db)):
    """
    Retrieve chat history for a given user and character.
    """
    try:
        # Debugging: Log the request parameters
        print(f"🔍 Fetching chat history for User ID: {user_id}, Character: {character}")

        # Ensure correct character formatting for database lookup
        formatted_character = character.replace("%20", " ")

        # Retrieve the conversation
        conversation = db.query(Conversation).filter_by(user_id=user_id, character=formatted_character).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="No conversation found.")

        # Fetch messages and sort them by timestamp
        messages = (
            db.query(Message)
            .filter_by(conversation_id=conversation.id)
            .order_by(Message.timestamp.asc())  # Sort messages by time
            .all()
        )

        # Convert timestamps to ISO format for proper serialization
        message_list = [
            {
                "sender": msg.sender,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else "N/A",
            }
            for msg in messages
        ]

        return {"conversation_id": conversation.id, "messages": message_list}

    except Exception as e:
        print(f"❌ Error retrieving chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Unable to retrieve chat history")



# ✅ Get List of Available AI Characters
@router.get("/characters/")
def get_characters():
    """
    Returns a list of available AI characters for user selection.
    """
    return {"characters": list(CHARACTER_PERSONAS.keys()) + ["Custom Character"]}

# ✅ Fix async handling in character generation
@router.post("/characters/generate", response_model=dict)
async def create_dynamic_character(request: CharacterGenerationRequest, db: Session = Depends(get_db)):
    """
    Generate a new AI character dynamically.
    """
    try:
        character_data = await generate_character(request)

        # Ensure it returns a valid response
        if not character_data or not isinstance(character_data, dict):
            raise HTTPException(status_code=500, detail="Failed to generate character")

        return character_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
