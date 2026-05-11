# ⚡ NeuralChat — LLM-Powered Chatbot

> Streamlit · MongoDB · Ollama (Mistral) · Local LLM

---

## 🗂 Project Structure

```
chatbot_app/
├── app.py            # Streamlit frontend + routing
├── db.py             # MongoDB CRUD helpers
├── requirements.txt  # Python dependencies
└── README.md
```

---

## ⚙️ Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | ≥ 3.10 | python.org |
| MongoDB | ≥ 6.0 | mongodb.com/try/download |
| Ollama | latest | ollama.com |

---

## 🚀 Setup & Run

### 1. Clone & install Python deps
```bash
git clone <YOUR_GITHUB_URL>
cd chatbot_app
pip install -r requirements.txt
```

### 2. Start MongoDB
```bash
# macOS / Linux
mongod --dbpath /data/db

# Windows
mongod
```

### 3. Start Ollama + pull Mistral
```bash
ollama serve          # starts the local model server
ollama pull mistral   # downloads the Mistral 7B model (~4 GB)
```

### 4. Launch the app
```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 🔑 Features

- **Login / Register** — SHA-256 hashed passwords, unique usernames enforced by MongoDB unique index
- **Persistent chat history** — all messages stored in `neuralchat.messages` collection with UTC timestamps
- **Context-aware replies** — last 20 turns sent to Mistral for coherent multi-turn conversations
- **Per-user stats** — message counts shown in sidebar
- **Full history on return** — loading previous sessions is seamless

---

## 🗄 MongoDB Schema

### `users` collection
```json
{
  "username":      "alice",
  "password_hash": "<sha256>",
  "created_at":    "2024-01-01T00:00:00Z"
}
```

### `messages` collection
```json
{
  "username":  "alice",
  "role":      "user | assistant",
  "content":   "What is quantum computing?",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## 🔧 Configuration

Edit `db.py` to change:
```python
MONGO_URI = "mongodb://localhost:27017"   # → your Atlas URI etc.
DB_NAME   = "neuralchat"
```

Edit `app.py` to change:
```python
OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "mistral"   # swap to llama3, phi3, etc.
```
# chatbot
