import json
import gradio as gr
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

# Signup function
def signup(username, password):
    response = requests.post(f"{FASTAPI_URL}/auth/register", json={"username": username, "password": password})
    if response.status_code == 200:
        return f"✅ Account created! Please login, {username}."
    else:
        return "❌ Error creating an account. Please try again."

# Login function
def login(username, password, session):
    response = requests.post(
        f"{FASTAPI_URL}/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        data = response.json()
        session["user_id"] = data.get("user_id")
        session["chat_id"] = None
        print("🟢 Login Successful - Session Updated:", session)

        # ✅ Load previous chat history automatically
        session["chat_history"] = get_chat_history(session)
        
        return f"✅ Welcome, {username}! Your chat history is loaded.", session
    else:
        return "❌ Invalid credentials. Please try again.", session

# Fetch available AI characters
def get_characters():
    try:
        response = requests.get(f"{FASTAPI_URL}/chat/characters/")
        response.raise_for_status()
        return response.json().get("characters", [])
    except requests.exceptions.RequestException:
        return ["Chuck the Clown", "Sarcastic Pirate"]  # Default characters

# Start a new chat
def start_new_chat(character_name, session):
    session["character"] = character_name
    session["chat_id"] = None  # Reset chat history
    return f"🔦 You are now chatting with {character_name}", session

# Chat function
def chat_with_ai(user_input, session):
    print("🔍 Chat Function - Session Data:", session)
    if not session["user_id"]:
        return "❌ Please log in first.", session
    if not session["character"]:
        return "❌ Please select a character.", session
    
    payload = {
        "user_id": session["user_id"],
        "character": session["character"],
        "message": user_input,
    }
    print("📤 Sending Payload:", json.dumps(payload, indent=2))
    
    try:
        response = requests.post(f"{FASTAPI_URL}/chat/", json=payload)
        response.raise_for_status()
        data = response.json()
        print("📥 AI Response:", json.dumps(data, indent=2))
        session["chat_id"] = data.get("conversation_id")
        return data.get(session["character"], "AI did not respond."), session
    except requests.exceptions.RequestException as e:
        return f"❌ Error connecting to AI: {str(e)}", session

# Chat history function
def get_chat_history(session):
    """Retrieve chat history in proper format for Chatbot component."""
    if not session["chat_id"]:
        return [("System", "❌ No chat history found.")]
    try:
        response = requests.get(f"{FASTAPI_URL}/chat/history/{session['user_id']}/{session['character']}")
        response.raise_for_status()
        messages = response.json().get("messages", [])

        # Ensure correct format for Gradio Chatbot
        return [(msg["sender"], msg["content"]) for msg in messages]
    except requests.exceptions.RequestException as e:
        return [("System", f"❌ Error retrieving chat history: {str(e)}")]

# Gradio UI
def create_gradio_interface():
    with gr.Blocks(title="AI Chat Platform") as iface:
        gr.Markdown("# 🤖 AI Chat Platform")

        # ✅ Initialize session state
        session = gr.State({"user_id": None, "chat_id": None, "character": None})

        with gr.Tab("🔑 Login"):
            username_input = gr.Textbox(label="Username")
            password_input = gr.Textbox(label="Password", type="password")
            login_btn = gr.Button("Login")
            login_output = gr.Textbox(label="Status", interactive=False)
            login_btn.click(login, inputs=[username_input, password_input, session], outputs=[login_output, session])
        
        with gr.Tab("🆕 Sign Up"):
            username_input_signup = gr.Textbox(label="Username")
            password_input_signup = gr.Textbox(label="Password", type="password")
            signup_btn = gr.Button("Sign Up")
            signup_output = gr.Textbox(label="Status", interactive=False)
            signup_btn.click(signup, inputs=[username_input_signup, password_input_signup], outputs=signup_output)

        with gr.Tab("🎭 Select Character"):
            character_dropdown = gr.Dropdown(label="Choose AI Character", choices=get_characters(), interactive=True)
            select_btn = gr.Button("Start Chat")
            character_output = gr.Textbox(label="Status", interactive=False)
            select_btn.click(start_new_chat, inputs=[character_dropdown, session], outputs=[character_output, session])

        with gr.Tab("💬 Chat with AI"):
            chatbot = gr.Chatbot(label="AI Chat", height=400)  # ✅ ChatGPT-style chatbot
            chat_input = gr.Textbox(label="Your Message")
            send_btn = gr.Button("Send")

            def chat_ui(user_message, chat_history, session):
                """Handles user input and updates chat in correct Gradio format."""
                if not session["user_id"]:
                    chat_history.append(("System", "❌ Please log in first."))
                    return chat_history, session
                if not session["character"]:
                    chat_history.append(("System", "❌ Please select a character."))
                    return chat_history, session

                # Send message to backend
                ai_response, session = chat_with_ai(user_message, session)

                # Ensure the response is valid
                if isinstance(ai_response, str):
                    chat_history.append(("You", user_message))
                    chat_history.append(("AI", ai_response))
                else:
                    chat_history.append(("System", "⚠️ Unexpected response format."))

                return chat_history, session

            send_btn.click(chat_ui, inputs=[chat_input, chatbot, session], outputs=[chatbot, session])

        with gr.Tab("📜 Chat History"):
            history_btn = gr.Button("Load History")
            history_output = gr.Textbox(label="Conversation History", lines=10, interactive=False)
            history_btn.click(get_chat_history, inputs=[session], outputs=[history_output])

    return iface

# Run Gradio app
if __name__ == "__main__":
    gradio_app = create_gradio_interface()
    gradio_app.launch(share=True)
