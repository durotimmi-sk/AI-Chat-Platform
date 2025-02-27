import os
import json
import base64
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from config.db import SessionLocal
from routes.chat import router as chat_router, chat_with_ai  # Import chat function
from routes.auth import router as auth_router
from services.audio_service import AudioConnectionManager, speech_to_text, text_to_speech

# Load environment variables first
load_dotenv()

# Create FastAPI app
app = FastAPI()

# Enable CORS (adjust for security in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourfrontend.com"],  # Replace with your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include API routes
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])

# Root endpoint
@app.get("/")
def root():
    return {"message": "FastAPI is running!"}

# WebSocket Manager
audio_manager = AudioConnectionManager()

@app.websocket("/ws/audio/{client_id}")
async def websocket_audio_endpoint(websocket: WebSocket, client_id: str):
    await audio_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                json_data = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))
                continue

            if "audio" in json_data:
                # Decode and process the audio
                audio_data = base64.b64decode(json_data["audio"])
                text = await speech_to_text(audio_data)

                # ✅ Call AI chat function directly instead of using TestClient
                ai_request = {
                    "user_id": json_data.get("user_id", 1),  # Default user_id if missing
                    "character": json_data.get("character", "Friendly AI"),
                    "message": text,
                }

                db: Session = SessionLocal()
                try:
                    ai_response = chat_with_ai(ai_request, db)  # Call AI function
                    ai_message = ai_response.get(ai_request["character"], "I didn't understand that.")
                finally:
                    db.close()  # Ensure database session is closed properly

                # Convert AI response to speech
                response_audio = await text_to_speech(ai_message)
                
                response_data = {
                    "text": ai_message,
                    "audio": base64.b64encode(response_audio).decode("utf-8"),
                }
                await websocket.send_text(json.dumps(response_data))
    except WebSocketDisconnect:
        audio_manager.disconnect(client_id)
