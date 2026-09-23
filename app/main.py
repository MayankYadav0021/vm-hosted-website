from fastapi import FastAPI, HTTPException
from app.config import MODEL_PRIMARY
from app.schemas import ChatRequest, ChatResponse
from app.services.ollama_service import OllamaService
from app.services.rag_service import RAGService
from app.services.guardrail_service import GuardrailService

app = FastAPI(title="CodeBase RAG Assistant", version="1.1")

ollama = OllamaService()
rag = RAGService()
guardrails = GuardrailService()


@app.get("/health")
def health():
    return {
        "api": True,
        "ollama": ollama.health(),
        "guardrails": True
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # Input guardrail
    validation = guardrails.validate_input(req.question)

    if not validation["allowed"]:
        raise HTTPException(
            status_code=400,
            detail={
                "guardrail": "input",
                "reason": validation["reason"],
                "details": validation.get("details")
            }
        )

    try:
        r = rag.direct_answer(
            validation["question"],
            req.model or MODEL_PRIMARY
        )

        # Output guardrail
        output_validation = guardrails.validate_output(r["text"])

        if not output_validation["allowed"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "guardrail": "output",
                    "reason": output_validation["reason"],
                    "details": output_validation.get("details")
                }
            )

        return ChatResponse(
            question=validation["question"],
            model=req.model or MODEL_PRIMARY,
            answer=output_validation["answer"],
            latency_seconds=r["latency_seconds"],
            prompt_tokens=r["prompt_tokens"],
            output_tokens=r["output_tokens"]
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/rag", response_model=ChatResponse)
def rag_chat(req: ChatRequest):
    # Input guardrail
    validation = guardrails.validate_input(req.question)

    if not validation["allowed"]:
        raise HTTPException(
            status_code=400,
            detail={
                "guardrail": "input",
                "reason": validation["reason"],
                "details": validation.get("details")
            }
        )

    try:
        r = rag.answer(
            validation["question"],
            req.model or MODEL_PRIMARY
        )

        # Output guardrail
        output_validation = guardrails.validate_output(r["text"])

        if not output_validation["allowed"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "guardrail": "output",
                    "reason": output_validation["reason"],
                    "details": output_validation.get("details")
                }
            )

        return ChatResponse(
            question=validation["question"],
            model=req.model or MODEL_PRIMARY,
            answer=output_validation["answer"],
            retrieved_context=r["retrieved"],
            latency_seconds=r["latency_seconds"],
            prompt_tokens=r["prompt_tokens"],
            output_tokens=r["output_tokens"]
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(500, str(e))
