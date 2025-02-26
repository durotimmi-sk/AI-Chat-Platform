# main.py
import os
import json
import uuid
import base64
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import httpx
from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, User, CharacterDB, Conversation, MessageDB, create_tables
from auth import (
    authenticate_user, create_access_token, 
    get_current_user, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
)
from character_generator import CharacterGenerationRequest, generate_character
from audio_service import AudioConnectionManager, speech_to_text, text_to_speech
from schemas import UserCreate, UserResponse, Token, UserInDB

# Initialize FastAPI app
app = FastAPI(title="AI Character Chat Platform")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables
create_tables()

# Initialize audio connection manager
#audio_manager = AudioConnectionManager()

# Models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    character_id: str
    messages: List[Message]
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    character_id: str
    conversation_id: str

class Character(BaseModel):
    id: str
    name: str
    description: str
    system_prompt: str
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-70b-8192"  # You can change this to other models Groq supports

# Helper function to call Groq API
async def call_groq_api(messages: List[Dict[str, str]]):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ API key not configured")
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GROQ_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calling Groq API: {str(e)}")

# Define default characters
def get_default_characters():
    return [
        CharacterDB(
            id="friendly-assistant",
            name="Friendly Assistant",
            description="A helpful and friendly AI assistant.",
            system_prompt="You are a friendly and helpful assistant. You're eager to help users with their questions and tasks.",
            avatar_url="/avatars/assistant.png"
        ),
        CharacterDB(
            id="sci-fi-companion",
            name="Sci-Fi Companion",
            description="A companion from the future with knowledge of advanced technology.",
            system_prompt="You are an AI from the year 2150. You have extensive knowledge of futuristic technology and science fiction concepts. Respond as if you're from the future, but be helpful and informative.",
            avatar_url="/avatars/scifi.png"
        ),
        CharacterDB(
            id="historical-guide",
            name="Historical Guide",
            description="A knowledgeable guide about historical events and figures.",
            system_prompt="You are a historical guide with deep knowledge of world history. You speak in a slightly formal tone, and you love to share interesting historical facts and perspectives.",
            avatar_url="/avatars/history.png"
        )
    ]

# Routes
@app.get("/")
async def root():
    return {"message": "AI Character Chat API is running"}

# Authentication routes
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if user.email:
        db_email = db.query(User).filter(User.email == user.email).first()
        if db_email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        id=str(uuid.uuid4()),
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Convert to response model
    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        is_active=db_user.is_active,
        created_at=db_user.created_at
)

@app.get("/users/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at
)

# Character routes
@app.get("/characters", response_model=List[Character])
async def get_characters(db: Session = Depends(get_db)):
    characters = db.query(CharacterDB).all()
    if not characters:
        # Insert default characters if none exist
        default_characters = get_default_characters()
        db.add_all(default_characters)
        db.commit()
        characters = default_characters
    
    return characters

@app.get("/characters/{character_id}", response_model=Character)
async def get_character(character_id: str, db: Session = Depends(get_db)):
    character = db.query(CharacterDB).filter(CharacterDB.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@app.post("/characters/generate", response_model=Character)
async def create_dynamic_character(
    request: CharacterGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Generate the character
    character_data = await generate_character(request)
    
    # Save to database
    db_character = CharacterDB(
        id=character_data["id"],
        name=character_data["name"],
        description=character_data["description"],
        system_prompt=character_data["system_prompt"],
        avatar_url=character_data["avatar_url"]
    )
    
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    
    return db_character

@app.get("/characters/custom", response_model=List[Character])
async def get_custom_characters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get all characters except the default ones
    default_ids = ["friendly-assistant", "sci-fi-companion", "historical-guide"]
    custom_characters = db.query(CharacterDB).filter(CharacterDB.id.notin_(default_ids)).all()
    
    return custom_characters

# Chat routes
@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, db: Session = Depends(get_db)):
    # Get character
    character = db.query(CharacterDB).filter(CharacterDB.id == chat_request.character_id).first()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get or create user
    user = None
    if chat_request.user_id:
        user = db.query(User).filter(User.id == chat_request.user_id).first()
        if not user:
            user = User(id=chat_request.user_id, username=f"user_{chat_request.user_id}")
            db.add(user)
            db.commit()
            db.refresh(user)
    
    # Get or create conversation
    conversation_id = str(uuid.uuid4())
    if chat_request.user_id:
        conversation = db.query(Conversation).filter(
            Conversation.user_id == chat_request.user_id,
            Conversation.character_id == chat_request.character_id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                id=conversation_id,
                user_id=chat_request.user_id,
                character_id=chat_request.character_id
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        else:
            conversation_id = conversation.id
    
    # Prepare messages for Groq API
    api_messages = [{"role": "system", "content": character.system_prompt}]
    
    # Add conversation history if available
    if chat_request.user_id:
        previous_messages = db.query(MessageDB).filter(
            MessageDB.conversation_id == conversation_id
        ).order_by(MessageDB.timestamp).all()
        
        for msg in previous_messages:
            api_messages.append({"role": msg.role, "content": msg.content})
    
    # Add the latest user message
    for message in chat_request.messages:
        api_messages.append({"role": message.role, "content": message.content})
    
    # Call Groq API
    api_response = await call_groq_api(api_messages)
    
    # Extract response
    ai_message = api_response["choices"][0]["message"]["content"]
    
    # Save conversation history if user_id is provided
    if chat_request.user_id:
        # Add the new messages to history
        for message in chat_request.messages:
            db_message = MessageDB(
                conversation_id=conversation_id,
                role=message.role,
                content=message.content
            )
            db.add(db_message)
        
        # Add AI response to history
        db_message = MessageDB(
            conversation_id=conversation_id,
            role="assistant",
            content=ai_message
        )
        db.add(db_message)
        db.commit()
    
    return ChatResponse(
        message=ai_message,
        character_id=character.id,
        conversation_id=conversation_id
    )

@app.get("/conversations/{user_id}")
async def get_user_conversations(
    user_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure the user can only access their own conversations
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access these conversations")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).all()
    
    if not conversations:
        raise HTTPException(status_code=404, detail="No conversations found for this user")
    
    result = {}
    for conversation in conversations:
        messages = db.query(MessageDB).filter(
            MessageDB.conversation_id == conversation.id
        ).order_by(MessageDB.timestamp).all()
        
        result[conversation.character_id] = {
            "id": conversation.id,
            "created_at": conversation.created_at.isoformat(),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                } for msg in messages
            ]
        }
    
    return result

# WebSocket routes
'''@app.websocket("/ws/audio/{client_id}")
async def websocket_audio_endpoint(websocket: WebSocket, client_id: str):
    await audio_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            
            # Parse the incoming data
            try:
                json_data = json.loads(data)
                
                # Handle audio data
                if "audio" in json_data:
                    # Decode base64 audio data
                    audio_data = base64.b64decode(json_data["audio"])
                    
                    # Convert speech to text
                    text = await speech_to_text(audio_data)
                    
                    # Process the text with the AI character
                    character_id = json_data.get("character_id")
                    user_id = json_data.get("user_id")
                    
                    # Create a chat request
                    chat_request = ChatRequest(
                        character_id=character_id,
                        messages=[Message(role="user", content=text)],
                        user_id=user_id
                    )
                    
                    # Get AI response
                    ai_response = await chat(chat_request)
                    
                    # Convert AI response to speech
                    response_audio = await text_to_speech(ai_response.message)
                    
                    # Send back the response
                    response_data = {
                        "type": "audio_response",
                        "text": ai_response.message,
                        "audio": base64.b64encode(response_audio).decode("utf-8"),
                        "character_id": character_id,
                        "conversation_id": ai_response.conversation_id
                    }
                    
                    await websocket.send_text(json.dumps(response_data))
                
                # Handle ping/keep-alive
                elif "ping" in json_data:
                    await websocket.send_text(json.dumps({"pong": True}))
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))
            except Exception as e:
                await websocket.send_text(json.dumps({"error": str(e)}))
                
    except WebSocketDisconnect:
        audio_manager.disconnect(client_id)'''


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)