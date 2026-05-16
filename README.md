# AAU AI Assistant

A RAG (Retrieval-Augmented Generation) chatbot for Al Ain University. Answers questions about programs, admissions, fees, campus life, and more using a Qdrant vector database and Groq LLM.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 18 + Vite |
| Backend | FastAPI + Python |
| LLM | Groq (llama-3.1-70b-versatile) |
| Vector DB | Qdrant |
| Embeddings | FastEmbed |

---

## Running Locally

You need **two terminals** open at the same time.

### 1. Set up environment variables

Copy the example files and fill in your keys:

```
backend/.env
```

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
QDRANT_URL=https://your-cluster-url.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here
```

```
frontend/.env
```

```env
VITE_API_URL=http://localhost:8000
```

### 2. Start the backend

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

> Backend runs at http://localhost:8000
> Health check: http://localhost:8000/health

### 3. Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

> Frontend runs at http://localhost:5173

---

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI app, /chat and /health endpoints
│   ├── rag_pipeline.py      # RAG logic (Qdrant retrieval + Groq generation)
│   ├── requirements.txt
│   └── .env                 # API keys (never commit this)
│
└── frontend/
    ├── src/
    │   ├── App.jsx           # Main state, send/clear logic
    │   ├── App.css           # All styles
    │   ├── api.js            # HTTP layer with retry + warm-up polling
    │   └── components/
    │       ├── ChatWindow.jsx        # Message list + typing indicator
    │       ├── MessageBubble.jsx     # Individual message with typewriter effect
    │       └── SuggestedQuestions.jsx
    ├── index.html
    └── package.json
```

---

## API

### `POST /chat`

```json
{
  "message": "What are the tuition fees?",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

Response:

```json
{
  "answer": "...",
  "sources": ["admissions.pdf", "fees.pdf"]
}
```

### `GET /health`

Returns `{ "status": "ready" }` when the RAG pipeline has finished loading, or `{ "status": "loading" }` while it warms up.
