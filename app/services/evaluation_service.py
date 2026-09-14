import json, os, psutil, time
from app.config import EMBED_MODEL
from app.services.ollama_service import OllamaService
from app.services.retrieval_service import RetrievalService

def keyword_score(text, keywords):
    t = text.lower()
    return sum(k.lower() in t for k in keywords) / max(len(keywords), 1)

class EvaluationService:
    def __init__(self):
        self.ollama = OllamaService()
        self.retriever = RetrievalService()

    def evaluate_question(self, model, item):
        start = time.perf_counter()
        before = psutil.Process().memory_info().rss
        qvec = self.ollama.embed(EMBED_MODEL, item["question"])
        retrieved = self.retriever.search(qvec, 4)
        context = "\n\n".join(x["text"] for x in retrieved)
        result = self.ollama.chat(
            model,
            "Use only this context. Do not invent facts.\nCONTEXT:\n" + context +
            "\nQUESTION:\n" + item["question"],
            0.1
        )
        latency = time.perf_counter() - start
        after = psutil.Process().memory_info().rss
        sources = [x["source"] for x in retrieved]
        expected_sources = item.get("expected_sources", [])
        rq = sum(any(s in got for got in sources) for s in expected_sources) / max(len(expected_sources), 1)
        relevance = keyword_score(result["text"], item.get("expected_keywords", []))
        return {
            "question_id": item["id"],
            "model": model,
            "question": item["question"],
            "answer": result["text"].replace("\n", " "),
            "retrieved_sources": ";".join(sources),
            "correctness_proxy": round(relevance, 3),
            "relevance": round(relevance, 3),
            "retrieval_quality": round(rq, 3),
            "hallucination_flag_proxy": int(bool(item.get("expected_keywords")) and relevance == 0),
            "latency_seconds": round(latency, 3),
            "prompt_tokens": result["prompt_tokens"],
            "output_tokens": result["output_tokens"],
            "memory_delta_mb": round((after-before)/(1024**2), 3)
        }

    def evaluate(self, models, path="data/evaluation_questions.json"):
        with open(path, encoding="utf-8") as f:
            dataset = json.load(f)
        return [self.evaluate_question(m, q) for m in models for q in dataset]
