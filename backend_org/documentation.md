# **📌 AI Chat Platform - Backend Documentation**
🚀 **Version:** 1.0  
🛠 **Technology Stack:** FastAPI, PostgreSQL, Docker, Alembic, SQLAlchemy, LangChain  
📅 **Last Updated:** _(Insert Date)_  

---

## **📖 Overview**
The **AI Chat Platform Backend** provides API endpoints to interact with AI characters via text and WebSockets. It includes **authentication, AI chat interactions, conversation history storage, character generation, and voice support**.

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
```

### **3️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4️⃣ Start the Application**
**Using Docker:**
```bash
docker-compose up --build
```

**Without Docker:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **5️⃣ Run Database Migrations**
```bash
docker-compose exec backend alembic upgrade head
```

---

## **🛠 API Endpoints**
### **🔑 Authentication (`routes/auth.py`)**
| **Method** | **Endpoint**            | **Description**                   |
|------------|-------------------------|-----------------------------------|
| `POST`     | `/auth/register`        | Register a new user               |
| `POST`     | `/auth/token`           | Login and get JWT token           |
| `GET`      | `/auth/me`              | Get logged-in user details        |

#### **Example: User Registration**
```bash
curl -X POST "http://localhost:8000/auth/register" -H "Content-Type: application/json" -d '{
  "username": "testuser",
  "password": "password123"
}'
```

---

### **💬 AI Chat (`routes/chat.py`)**
| **Method** | **Endpoint**               | **Description**                   |
|------------|----------------------------|-----------------------------------|
| `GET`      | `/chat/characters/`        | List available AI characters      |
| `POST`     | `/chat/`                    | Start conversation with AI        |
| `GET`      | `/chat/history/{user_id}/{character}` | Get conversation history |

#### **Example: Start Chat with AI**
```bash
curl -X POST "http://localhost:8000/chat/" -H "Content-Type: application/json" -d '{
  "user_id": 1,
  "character": "Chuck the Clown",
  "message": "Tell me a joke!"
}'
```
✅ **Response**
```json
{
  "user": "Tell me a joke!",
  "Chuck the Clown": "Why did the scarecrow win an award? Because he was outstanding in his field!",
  "conversation_id": 5
}
```

#### **Example: Get Chat History**
```bash
curl -X GET "http://localhost:8000/chat/history/1/Chuck%20the%20Clown"
```
✅ **Response**
```json
{
  "conversation_id": 5,
  "messages": [
    {"sender": "User", "content": "Tell me a joke!"},
    {"sender": "Chuck the Clown", "content": "Why did the scarecrow win an award? Because he was outstanding in his field!"}
  ]
}
```

---

### **🎙 Voice Chat (`services/audio_service.py`)**
| **Method** | **Endpoint**              | **Description**                      |
|------------|---------------------------|--------------------------------------|
| `WS`       | `/ws/audio/{client_id}`   | WebSocket endpoint for voice chat   |

#### **Example: Connect WebSocket**
```bash
wscat -c ws://localhost:8000/ws/audio/test-client
```

---

## **💾 Database Models (`models/models.py`)**
### **User**
| Column    | Type   | Description                 |
|-----------|--------|---------------------------|
| `id`      | `int`  | Primary Key (Auto-Inc)     |
| `username`| `str`  | Unique username            |
| `password`| `str`  | Hashed password            |

### **Conversation**
| Column         | Type   | Description                     |
|---------------|--------|---------------------------------|
| `id`          | `int`  | Primary Key                     |
| `user_id`     | `int`  | Foreign Key (User ID)           |
| `character`   | `str`  | AI Character Name               |
| `created_at`  | `datetime` | Timestamp |

### **Message**
| Column           | Type   | Description                      |
|-----------------|--------|---------------------------------|
| `id`           | `int`  | Primary Key                      |
| `conversation_id` | `int`  | Foreign Key (Conversation ID) |
| `sender`       | `str`  | "User" or AI Character          |
| `content`      | `text`  | Message text                    |

---

## **🛠 Deployment**
### **1️⃣ Deploy on Render**
- **Modify `docker-compose.yml` and `Dockerfile` to use a production database.**
- Use **Render, AWS, or DigitalOcean** for hosting.

### **2️⃣ Deploy Database (PostgreSQL)**
- Use **Managed PostgreSQL** or **Supabase**.

### **3️⃣ Use HTTPS**
- Deploy using **NGINX + Let’s Encrypt**.

---

## **🔑 Security**
✅ **Environment Variables:** Store **API keys & database credentials** in `.env`.  
✅ **JWT Authentication:** Secure API with JWT tokens.  
✅ **CORS Policy:** Restrict frontend access in `main.py`.  
✅ **Rate Limiting:** Use `fastapi-limiter` for abuse protection.  

---

## **🚀 Contributors**
👤 **Our Names** - All Backend Developers  
📧 **Contact:** your-email@example.com  

🔗 **GitHub Repo:** _(Our GitHub URL)_  
🔗 **Live API:** _(Your API URL)_  

