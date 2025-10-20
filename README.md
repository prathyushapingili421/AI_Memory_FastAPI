# 🧠 AI Memory FastAPI

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async%20API-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-async--motor-brightgreen?logo=mongodb)](https://www.mongodb.com/)
[![License](https://img.shields.io/github/license/prathyushapingili421/AI_Memory_FastAPI)](https://choosealicense.com/licenses/)

A FastAPI-based backend that captures and stores chat-based memories using MongoDB, embedding models, and structured memory layers — including:

- 🔁 Short-term memory
- 🧾 Long-term (summary) memory
- 🧠 Episodic memory (fact-based with importance weighting)

---

## 🚀 Features

- 🗨️ Chat endpoint: `POST /api/chat`
- 🧠 Memory introspection: `GET /api/memory/{user_id}`
- 📊 Aggregated lifetime memory: `GET /api/aggregate/{user_id}`
- ⚡ Asynchronous MongoDB via `motor`
- 🧬 Embedding model integration (Ollama, HuggingFace, etc.)
- 🧾 Episodic memory extraction and ranking
- 🖥️ Optional web-based chat UI: `http://localhost:8000/static/chat.html`

---

## 📦 Setup Instructions

### 🧰 1. Install Dependencies

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required Python packages
pip install -r requirements.txt
````

---

### 🛠️ 2. MongoDB Setup

Ensure MongoDB is running locally on the default port (`localhost:27017`), or update the URI in `.env`.

```bash
# Create .env file from the template
cp .env.template .env
```

Then edit the `.env` file if needed:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB=ai_memory_db
```

> 💡 You can also connect to a remote or cloud MongoDB instance (e.g., [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)) by replacing the `MONGO_URI` with your cloud connection string.

---

### ▶️ 3. Run the Application

```bash
uvicorn ai_memory_fastapi.main:app --reload
```

* 📘 **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
* 💬 **Chat UI:** [http://localhost:8000/static/chat.html](http://localhost:8000/static/chat.html)

---

## 📁 Folder Structure

```
ai_memory_fastapi/
│
├── main.py                     # FastAPI entry point
├── config.py                   # Settings / .env loading
├── models.py                   # Pydantic models
├── requirements.txt            # Pip dependencies
├── .env.template               # Sample environment config
│
├── static/
│   └── chat.html               # Mini chat frontend
│
├── routers/
│   ├── chat.py                 # /api/chat routes
│   ├── memory.py               # /api/memory routes
│   └── aggregate.py            # /api/aggregate routes
│
├── services/
│   ├── memory_logic.py         # Episodic memory, summaries
│   ├── embeddings.py           # Embedding logic
│   └── ollama_client.py        # LLM API wrapper
│
├── mongoimpl/
│   └── mongo.py                # Async MongoDB manager
```

---

## 🧪 Example API Call (cURL)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "u1", "session_id": "s1", "message": "I am happy"}'
```

---

## 🤝 Credits

Built by **Prathyusha Pingili**
Powered by FastAPI + MongoDB + Ollama + Embeddings = 🧠💬

---

## 📌 License

This project is licensed under the **MIT License**.

