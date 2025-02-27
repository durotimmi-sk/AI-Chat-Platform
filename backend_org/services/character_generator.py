import os
import httpx
import json
from pydantic import BaseModel
from typing import Dict, Any, Optional
import random

class CharacterGenerationRequest(BaseModel):
    theme: Optional[str] = None
    personality_traits: Optional[list] = None
    knowledge_areas: Optional[list] = None
    era: Optional[str] = None
    style: Optional[str] = None

async def generate_character(request: CharacterGenerationRequest) -> Dict[str, Any]:
    """
    Generate a dynamic AI character based on user preferences.
    """
    prompt = f"""
    Create a detailed AI character profile:
    - Theme: {request.theme or 'Any'}
    - Personality traits: {', '.join(request.personality_traits) if request.personality_traits else 'Friendly, helpful'}
    - Knowledge areas: {', '.join(request.knowledge_areas) if request.knowledge_areas else 'General knowledge'}
    - Era: {request.era or 'Contemporary'}
    - Communication style: {request.style or 'Conversational'}
    """
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}", "Content-Type": "application/json"},
            json={"model": "llama3-70b-8192", "messages": [{"role": "user", "content": prompt}]}
        )
        result = response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", {})

