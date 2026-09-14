import time
from app.config import EMBED_MODEL, MODEL_PRIMARY, TOP_K
from app.services.ollama_service import OllamaService
from app.services.retrieval_service import RetrievalService

class RAGService:
    def __init__(self):
        self.ollama = OllamaService()
        self.retriever = RetrievalService()

    def answer(self, question, model=MODEL_PRIMARY):
        start = time.perf_counter()
        qvec = self.ollama.embed(EMBED_MODEL, question)
        retrieved = self.retriever.search(qvec, TOP_K)
        context = "\n\n".join(
            f"[SOURCE: {x['source']} | SCORE: {x['score']:.4f}]\n{x['text']}"
            for x in retrieved
        )
        prompt = (
            "You are a software project assistant. Answer using ONLY the supplied "
            "project context. If evidence is insufficient, say so. Mention source "
            "files when possible.\n\nCONTEXT:\n" + context +
            "\n\nQUESTION:\n" + question + "\n\nANSWER:"
        )
        result = self.ollama.chat(model, prompt, 0.1)
        result["retrieved"] = retrieved
        result["latency_seconds"] = time.perf_counter() - start
        return result

    def direct_answer(self, question, model=MODEL_PRIMARY):
        start = time.perf_counter()
        result = self.ollama.chat(
            model,
            "Answer this software question. Do not invent project-specific details.\nQUESTION: " + question,
            0.1
        )
        result["latency_seconds"] = time.perf_counter() - start
        return result
