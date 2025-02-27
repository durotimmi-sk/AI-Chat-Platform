from sqlalchemy import JSON, Boolean

class CharacterDB(Base):
    __tablename__ = "characters"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    description = Column(Text)
    system_prompt = Column(Text)
    avatar_url = Column(String, nullable=True)
    is_dynamic = Column(Boolean, default=False)
    creator_id = Column(String, ForeignKey("users.id"), nullable=True)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
