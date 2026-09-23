from fastapi import FastAPI, HTTPException
from app.config import MODEL_PRIMARY
from app.schemas import ChatRequest, ChatResponse
from app.services.ollama_service import OllamaService
from app.services.rag_service import RAGService

app = FastAPI(title="CodeBase RAG Assistant", version="1.0")
ollama = OllamaService()
rag = RAGService()

@app.get("/health")
def health():
    return {"api": True, "ollama": ollama.health()}

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        r = rag.direct_answer(req.question, req.model or MODEL_PRIMARY)
        return ChatResponse(question=req.question, model=req.model or MODEL_PRIMARY,
                            answer=r["text"], latency_seconds=r["latency_seconds"],
                            prompt_tokens=r["prompt_tokens"], output_tokens=r["output_tokens"])
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/rag", response_model=ChatResponse)
def rag_chat(req: ChatRequest):
    try:
        r = rag.answer(req.question, req.model or MODEL_PRIMARY)
        return ChatResponse(question=req.question, model=req.model or MODEL_PRIMARY,
                            answer=r["text"], retrieved_context=r["retrieved"],
                            latency_seconds=r["latency_seconds"],
                            prompt_tokens=r["prompt_tokens"], output_tokens=r["output_tokens"])
    except Exception as e:
        raise HTTPException(500, str(e))
