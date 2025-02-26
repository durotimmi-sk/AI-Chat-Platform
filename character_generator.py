# character_generator.py
import os
import httpx
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel
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
    
    This function uses the Groq API to dynamically create character profiles.
    """
    # Set up the character generation prompt
    prompt = f"""
    Create a detailed AI character profile based on the following criteria:
    
    Theme: {request.theme or 'Any'}
    Personality traits: {', '.join(request.personality_traits) if request.personality_traits else 'Friendly, helpful'}
    Knowledge areas: {', '.join(request.knowledge_areas) if request.knowledge_areas else 'General knowledge'}
    Era: {request.era or 'Contemporary'}
    Communication style: {request.style or 'Conversational'}
    
    Generate a JSON object with the following fields:
    - id: A unique identifier (use kebab-case, like "future-historian")
    - name: A catchy name for the character
    - description: A short paragraph describing the character
    - system_prompt: A comprehensive system prompt (300-500 words) that will guide the AI to embody this character
    - avatar_description: A brief description of what this character might look like (for image generation)
    """
    
    # Call the Groq API
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a creative character designer for an AI conversation platform."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GROQ_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Extract and parse the JSON content
            content = result["choices"][0]["message"]["content"]
            
            # Find JSON in the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                character_data = json.loads(json_content)
                
                # Ensure it has all the required fields
                required_fields = ["id", "name", "description", "system_prompt"]
                if all(field in character_data for field in required_fields):
                    # Add a placeholder avatar URL (this would be replaced with a real image in production)
                    character_data["avatar_url"] = generate_placeholder_avatar(character_data.get("name", "Unknown"))
                    return character_data
            
            # If JSON parsing failed or fields are missing, return an error
            raise ValueError("Failed to generate valid character data")
            
        except Exception as e:
            print(f"Error generating character: {str(e)}")
            # Fall back to a pre-defined character
            return generate_fallback_character(request)

def generate_placeholder_avatar(name: str) -> str:
    """Generate a placeholder avatar URL based on the character name."""
    # In a production system, you would generate or select a real avatar image
    # For now, we'll use a placeholder service
    return f"/api/placeholder/avatar/{name.replace(' ', '-').lower()}"

def generate_fallback_character(request: CharacterGenerationRequest) -> Dict[str, Any]:
    """Generate a fallback character if the API call fails."""
    # Create a basic character based on the request
    theme = request.theme or "general"
    traits = request.personality_traits or ["friendly", "helpful"]
    knowledge = request.knowledge_areas or ["general knowledge"]
    era = request.era or "contemporary"
    
    # Generate a simple character based on inputs
    character_id = f"{theme.lower().replace(' ', '-')}-{random.randint(1000, 9999)}"
    name = f"{theme.title()} Guide"
    
    traits_str = ", ".join(traits)
    knowledge_str = ", ".join(knowledge)
    
    description = f"A {traits_str} character with knowledge of {knowledge_str}, from the {era} era."
    
    system_prompt = f"""
    You are a {traits_str} character named {name} from the {era} era.
    You have extensive knowledge about {knowledge_str}.
    When speaking with users, maintain a consistent personality that is {traits_str}.
    Provide helpful and informative responses while staying in character.
    Your goal is to engage users in meaningful conversations about topics related to {knowledge_str}.
    """
    
    return {
        "id": character_id,
        "name": name,
        "description": description,
        "system_prompt": system_prompt,
        "avatar_url": generate_placeholder_avatar(name)
    }