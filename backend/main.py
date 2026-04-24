import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AAU AI Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = None
is_ready = False


def _load_pipeline():
    global rag, is_ready
    from rag_pipeline import RAGPipeline
    rag = RAGPipeline()
    is_ready = True
    logger.info("RAG pipeline ready.")


@app.on_event("startup")
async def startup():
    # Load pipeline in background so port binds immediately
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _load_pipeline)


@app.get("/health")
def health():
    return {"status": "ready" if is_ready else "loading"}


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not is_ready:
        raise HTTPException(status_code=503, detail="Still loading, please wait a moment.")
    try:
        history_dicts = [msg.model_dump() for msg in request.history]
        result = rag.query(request.message, history_dicts)
        return result
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
