

# **📌 AI Chat Platform - Backend & Gradio UI Documentation**
🚀 **Version:** 1.0  
🛠 **Technology Stack:** FastAPI, PostgreSQL, Docker, Alembic, SQLAlchemy, LangChain, Gradio  
📅 **Last Updated:** _(Insert Date)_  

---

## **📖 Overview**
The **AI Chat Platform Backend & Gradio UI** provides API endpoints to interact with AI characters via text and WebSockets. It includes **authentication, AI chat interactions, conversation history storage, character generation, and voice support**.  

The **Gradio UI (`gradio_ui.py`)** serves as the frontend, allowing users to **sign up, log in, select AI characters, chat, and view chat history**.

---

## **📂 Project Structure**
📍 **Directory:** `backend/`
```
backend/
│── config/                  # 📂 Configuration Files
│   ├── db.py                # 📌 Database connection setup (SQLAlchemy)
│
│── migrations/              # 📂 Alembic Migrations Folder
│   ├── env.py               # 📌 Alembic configuration script
│   ├── versions/            # 📂 Stores migration scripts
│
│── models/                  # 📂 Database Models
│   ├── models.py            # 📌 Defines SQLAlchemy models (User, Message, Conversation)
│
│── routes/                  # 📂 FastAPI API Routes
│   ├── auth.py              # 📌 User Authentication (JWT login, register)
│   ├── chat.py              # 📌 Chat API (AI interaction, history)
│
│── services/                # 📂 Business Logic Services
│   ├── audio_service.py     # 📌 Handles WebSocket audio (speech-to-text, text-to-speech)
│   ├── character_generator.py # 📌 AI Character Generation
│
│── gradio_ui.py             # 📌 Main Gradio interface (AI Chat Frontend)
│
│── .env                     # 📌 Environment Variables (API keys, DB credentials)
│── alembic.ini              # 📌 Alembic Configuration
│── docker-compose.yml       # 📌 Docker Compose Setup
│── Dockerfile               # 📌 Backend Docker Configuration
│── main.py                  # 📌 FastAPI Entry Point
│── requirements.txt         # 📌 Dependencies List
│── cli_chat.py              # 📌 CLI for AI Chat Interaction
```

---

## **🛠 Setup & Installation**
### **1️⃣ Clone the Repository**
```bash
git clone https://github.com/your-repo/ai-chat-backend.git
cd ai-chat-backend/backend
```

### **2️⃣ Set Up Environment Variables**
Create a `.env` file:
```bash
touch .env
```
Paste this inside:
```
DATABASE_URL=postgresql://root:root@db:5432/ai_chat_platform
GROQ_API_KEY=your-api-key
SECRET_KEY=your-secret-key
FASTAPI_URL=http://localhost:8000
```

### **3️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4️⃣ Start the Backend Application**
**Using Docker:**
```bash
docker-compose up --build
```

**Without Docker:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **5️⃣ Start the Gradio UI**
```bash
python frontend/gradio_ui.py
```
Gradio will provide a **local URL** (e.g., `http://127.0.0.1:7860`) to access the AI chat interface.

### **6️⃣ Run Database Migrations**
```bash
docker-compose exec backend alembic upgrade head
```

---

## **🖥️ Features**
### **🔑 User Authentication**
- **Sign Up:** Create a new account.
- **Login:** Authenticate with username and password.
- **Session Management:** Stores `user_id`, chat history, and selected AI character.

### **🎭 AI Character Selection**
- Users can choose from **predefined characters**:
  - Chuck the Clown 🤡
  - Sarcastic Pirate 🏴‍☠️
  - Professor Sage 🎓
  - Yoda from Star Wars 🟢
- Option to create **custom AI characters**.

### **💬 AI Chat Functionality**
- **Real-time Chat:** User messages are sent to the backend, and AI responses are returned.
- **ChatGPT-Style Interface:** Messages appear in a formatted conversation window.

### **📜 Chat History**
- **Saves previous conversations** for logged-in users.
- Loads chat history automatically after login.

---

## **🛠 API Endpoints**
### **🔑 Authentication (`routes/auth.py`)**
| **Method** | **Endpoint**            | **Description**                   |
|------------|-------------------------|-----------------------------------|
| `POST`     | `/auth/register`        | Register a new user               |
| `POST`     | `/auth/token`           | Login and get JWT token           |
| `GET`      | `/auth/me`              | Get logged-in user details        |

---

### **💬 AI Chat (`routes/chat.py`)**
| **Method** | **Endpoint**               | **Description**                   |
|------------|----------------------------|-----------------------------------|
| `GET`      | `/chat/characters/`        | List available AI characters      |
| `POST`     | `/chat/`                    | Start conversation with AI        |
| `GET`      | `/chat/history/{user_id}/{character}` | Get conversation history |

---

## **🎨 Gradio UI (`frontend/gradio_ui.py`)**
### **💻 Key Functions**
| **Function** | **Description** |
|-------------|----------------|
| `signup()` | Registers a new user |
| `login()` | Authenticates user, loads chat history |
| `get_characters()` | Fetches available AI characters |
| `chat_with_ai()` | Sends user message to backend, retrieves AI response |
| `get_chat_history()` | Loads previous chat conversations |
| `create_gradio_interface()` | Builds the Gradio UI |

### **💬 Chat UI Function**
```python
def chat_ui(user_message, chat_history, session):
    """Handles user input and updates chat in correct Gradio format."""
    if not session["user_id"]:
        chat_history.append(("System", "❌ Please log in first."))
        return chat_history, session
    if not session["character"]:
        chat_history.append(("System", "❌ Please select a character."))
        return chat_history, session

    ai_response, session = chat_with_ai(user_message, session)
    if isinstance(ai_response, str):
        chat_history.append(("You", user_message))
        chat_history.append(("AI", ai_response))
    else:
        chat_history.append(("System", "⚠️ Unexpected response format."))
    
    return chat_history, session
```

### **🚀 Running Gradio UI**
```bash
python frontend/gradio_ui.py
```

---

## **🛠 Deployment**
### **1️⃣ Deploy on Hugging Face Spaces**
```bash
gradio deploy
```
### **2️⃣ Deploy with Docker**
```bash
docker build -t ai-chat-ui .
docker run -p 7860:7860 ai-chat-ui
```

---

## **🔑 Security**
✅ **Use HTTPS for Deployment**  
✅ **Restrict API Access with CORS**  
✅ **Store API Keys in `.env`**  

---

## **🚀 Contributors**
👤 **Our Names** - Backend & UI Developers  
📧 **Contact:** your-email@example.com  

🔗 **GitHub Repo:** _(Insert URL)_  
🔗 **Live API & UI:** _(Insert URL)_  

