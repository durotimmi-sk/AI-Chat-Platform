# database.py
import os
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_chat.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models
# Update the User model in database.py
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversations = relationship("Conversation", back_populates="user")
    custom_characters = relationship("CharacterDB", back_populates="creator")

class CharacterDB(Base):
    __tablename__ = "characters"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    description = Column(Text)
    system_prompt = Column(Text)
    avatar_url = Column(String, nullable=True)
    is_dynamic = Column(Boolean, default=False)  # Whether this character was dynamically generated
    is_system = Column(Boolean, default=True)    # Whether this is a system default character
    voice_id = Column(String, nullable=True)     # Reference to a voice in a TTS system
    creator_id = Column(String, ForeignKey("users.id"), nullable=True)  # User who created this character
    attributes = Column(JSON, nullable=True)     # Additional character attributes as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversations = relationship("Conversation", back_populates="character")
    creator = relationship("User", back_populates="custom_characters")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    character_id = Column(String, ForeignKey("characters.id"))
    title = Column(String, nullable=True)  # Auto-generated title for the conversation
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="conversations")
    character = relationship("CharacterDB", back_populates="conversations")
    messages = relationship("MessageDB", back_populates="conversation", cascade="all, delete-orphan")

class MessageDB(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String)  # "user", "assistant", "system"
    content = Column(Text)
    audio_url = Column(String, nullable=True)  # URL to stored audio file if applicable
    video_url = Column(String, nullable=True)  # URL to stored video file if applicable
    meta_info = Column(JSON, nullable=True)     # Additional message metadata
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")

class AudioFile(Base):
    __tablename__ = "audio_files"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    file_path = Column(String)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    created_at = Column(DateTime, default=datetime.utcnow)

class VideoFile(Base):
    __tablename__ = "video_files"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    file_path = Column(String)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    thumbnail_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)