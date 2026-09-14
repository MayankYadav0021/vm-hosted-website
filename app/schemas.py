from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    model: Optional[str] = None

class RetrievedChunk(BaseModel):
    source: str
    chunk_id: int
    score: float
    text: str

class ChatResponse(BaseModel):
    question: str
    model: str
    answer: str
    retrieved_context: List[RetrievedChunk] = []
    latency_seconds: float
    prompt_tokens: int = 0
    output_tokens: int = 0
