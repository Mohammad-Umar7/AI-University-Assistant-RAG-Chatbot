import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_pipeline import RAGPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rag: RAGPipeline | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag
    logger.info("Starting up — loading RAG pipeline...")
    rag = RAGPipeline()
    yield
    logger.info("Shutting down.")


app = FastAPI(title="AAU AI Assistant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@app.get("/health")
def health():
    return {"status": "ok", "service": "AAU AI Assistant"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not rag:
        raise HTTPException(status_code=503, detail="RAG pipeline not ready")
    try:
        history_dicts = [msg.model_dump() for msg in request.history]
        result = rag.query(request.message, history_dicts)
        return result
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
